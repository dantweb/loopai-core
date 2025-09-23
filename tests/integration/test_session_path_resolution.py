#!/usr/bin/env python3
"""
Session Path Resolution Test

This test validates that session managers provide correct user_id and loop_id
values for path construction, preventing the '/app/var/users/None/loops/None/config/WAKEUP.py' issue.
"""

import unittest
import threading
import os
import tempfile
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from core.models.step_model import StepModel, get_session_manager
from core.adapters.file_adapter_interface import get_loop_config_base_path_by_user_and_loop
from core.services.session_manager import session_manager
from core.services.thread_safe_session import thread_safe_session_manager


class TestSessionPathResolution(unittest.TestCase):
    """Test that session managers provide correct path resolution in threaded environments"""

    def setUp(self):
        """Set up test environment"""
        self.test_user_id = 42
        self.test_loop_id = 123
        self.test_project_id = 1

    def test_single_thread_path_resolution(self):
        """Test that path resolution works correctly in single thread"""
        # Set up session with known values
        session_manager.set_user_id(self.test_user_id)
        session_manager.set_loop_id(self.test_loop_id)
        session_manager.set_project_id(self.test_project_id)

        # Get session manager and verify it has correct data
        current_session = get_session_manager()
        user_id = current_session.get_user_id()
        loop_id = current_session.get_loop_id()

        print(f"Single thread session data: user_id={user_id}, loop_id={loop_id}")

        # Verify no None values
        self.assertIsNotNone(user_id, "User ID should not be None in single thread context")
        self.assertIsNotNone(loop_id, "Loop ID should not be None in single thread context")
        self.assertEqual(user_id, self.test_user_id, f"User ID should be {self.test_user_id}, got {user_id}")
        self.assertEqual(loop_id, self.test_loop_id, f"Loop ID should be {self.test_loop_id}, got {loop_id}")

        # Test path construction
        config_path = get_loop_config_base_path_by_user_and_loop(user_id, loop_id)
        expected_path_pattern = f"/app/var/users/{self.test_user_id}/loops/{self.test_loop_id}/config"

        print(f"Constructed path: {config_path}")
        print(f"Expected pattern: {expected_path_pattern}")

        # The path should NOT contain 'None'
        self.assertNotIn('None', config_path, f"Path should not contain 'None': {config_path}")
        self.assertIn(str(self.test_user_id), config_path, f"Path should contain user_id {self.test_user_id}: {config_path}")
        self.assertIn(str(self.test_loop_id), config_path, f"Path should contain loop_id {self.test_loop_id}: {config_path}")

    def test_threaded_session_path_resolution(self):
        """Test that path resolution works correctly in separate threads (this should initially FAIL)"""
        def test_path_in_thread(thread_id):
            """Test path resolution within a thread"""
            thread_name = f"PathTestThread-{thread_id}"
            threading.current_thread().name = thread_name

            try:
                # In a new thread, simulate what ThreadedRequestContext should do
                # Create session for this thread
                session_id = session_manager.create_session_for_loop(
                    user_id=self.test_user_id + thread_id,  # Unique user per thread
                    loop_id=self.test_loop_id + thread_id,  # Unique loop per thread
                    project_id=self.test_project_id
                )

                # Get session manager (this is where the bug occurs)
                current_session = get_session_manager()
                user_id = current_session.get_user_id()
                loop_id = current_session.get_loop_id()

                print(f"Thread {thread_id} session data: user_id={user_id}, loop_id={loop_id}")

                # Construct path using the session values
                config_path = get_loop_config_base_path_by_user_and_loop(user_id, loop_id)

                # Check for the broken path pattern
                has_none_values = user_id is None or loop_id is None
                path_contains_none = 'None' in config_path if config_path else True

                return {
                    'thread_id': thread_id,
                    'user_id': user_id,
                    'loop_id': loop_id,
                    'session_id': session_id,
                    'config_path': config_path,
                    'has_none_values': has_none_values,
                    'path_contains_none': path_contains_none,
                    'success': not has_none_values and not path_contains_none
                }

            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'user_id': None,
                    'loop_id': None,
                    'session_id': None,
                    'config_path': None,
                    'has_none_values': True,
                    'path_contains_none': True,
                    'success': False,
                    'error': str(e)
                }

            finally:
                # Clean up session
                try:
                    session_manager.cleanup_session()
                except:
                    pass

        # Test with multiple threads
        num_threads = 5
        results = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(test_path_in_thread, i): i for i in range(num_threads)}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Analyze results
        print(f"\n=== Threaded Path Resolution Test Results ===")
        print(f"Total threads: {num_threads}")

        successful_threads = [r for r in results if r['success']]
        failed_threads = [r for r in results if not r['success']]
        none_value_threads = [r for r in results if r['has_none_values']]
        none_path_threads = [r for r in results if r['path_contains_none']]

        print(f"Successful: {len(successful_threads)}")
        print(f"Failed: {len(failed_threads)}")
        print(f"None values: {len(none_value_threads)}")
        print(f"None in path: {len(none_path_threads)}")

        if failed_threads:
            print(f"\n=== Failed Thread Details ===")
            for result in failed_threads:
                print(f"Thread {result['thread_id']}:")
                print(f"  user_id: {result['user_id']}")
                print(f"  loop_id: {result['loop_id']}")
                print(f"  config_path: {result['config_path']}")
                if 'error' in result:
                    print(f"  error: {result['error']}")

        # This test should FAIL if session manager integration is broken
        if none_value_threads:
            self.fail(f"Session manager returning None values in {len(none_value_threads)} threads. "
                     f"This exposes the '/app/var/users/None/loops/None/config/WAKEUP.py' issue. "
                     f"Session manager integration needs to be fixed.")

        if none_path_threads:
            self.fail(f"Path contains 'None' in {len(none_path_threads)} threads. "
                     f"This causes the 'No such file or directory: /app/var/users/None/loops/None/config/WAKEUP.py' error.")

        # All threads should have valid session data
        self.assertEqual(len(failed_threads), 0,
                        f"All {num_threads} threads should have valid session data")
        self.assertEqual(len(successful_threads), num_threads,
                        f"All {num_threads} threads should construct valid paths")

    def test_step_model_load_code_module_path_resolution(self):
        """Test that StepModel.load_code_module uses correct paths (this will FAIL with broken session)"""
        # Set up session data
        session_manager.set_user_id(self.test_user_id)
        session_manager.set_loop_id(self.test_loop_id)
        session_manager.set_project_id(self.test_project_id)

        # Create a StepModel instance
        with patch('core.models.step_model.db'), \
             patch('core.services.logger_service.LoggerService'):

            step_model = StepModel(
                name="test_step",
                description="Test step",
                step_type="test",
                action=MagicMock(executor="test"),
                inputs=[],
                outputs=[]
            )

            # Mock the code source directory and WAKEUP.py file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create directory structure
                user_dir = os.path.join(temp_dir, str(self.test_user_id))
                loops_dir = os.path.join(user_dir, 'loops', str(self.test_loop_id), 'config')
                os.makedirs(loops_dir, exist_ok=True)

                # Create WAKEUP.py file
                wakeup_file = os.path.join(loops_dir, 'WAKEUP.py')
                with open(wakeup_file, 'w') as f:
                    f.write('# Test WAKEUP file\ntest_var = "test_value"\n')

                # Mock the path functions to use our temp directory
                with patch('core.adapters.file_adapter_interface.get_loop_config_base_path_by_user_and_loop') as mock_path:
                    mock_path.return_value = loops_dir

                    try:
                        # This should work without errors
                        step_model.load_code_module('WAKEUP.py')

                        # Verify the path was constructed correctly
                        mock_path.assert_called_once()
                        call_args = mock_path.call_args[0]  # Get positional arguments

                        print(f"StepModel path construction called with: user_id={call_args[0]}, loop_id={call_args[1]}")

                        # These should not be None
                        self.assertIsNotNone(call_args[0], "User ID passed to path construction should not be None")
                        self.assertIsNotNone(call_args[1], "Loop ID passed to path construction should not be None")

                        # Should be the correct values
                        self.assertEqual(str(call_args[0]), str(self.test_user_id),
                                       f"User ID should be {self.test_user_id}, got {call_args[0]}")
                        self.assertEqual(str(call_args[1]), str(self.test_loop_id),
                                       f"Loop ID should be {self.test_loop_id}, got {call_args[1]}")

                    except Exception as e:
                        if 'None' in str(e):
                            self.fail(f"StepModel.load_code_module failed with None values in path: {e}")
                        else:
                            # Re-raise if it's a different error
                            raise

    def test_broken_path_detection(self):
        """Test that specifically detects the broken path pattern"""
        # Simulate the broken scenario where session manager returns None
        with patch('core.models.step_model.get_session_manager') as mock_get_session:
            mock_session = MagicMock()
            mock_session.get_user_id.return_value = None  # This is the bug
            mock_session.get_loop_id.return_value = None  # This is the bug
            mock_get_session.return_value = mock_session

            # Construct path with None values (this is what causes the error)
            broken_path = get_loop_config_base_path_by_user_and_loop(None, None)

            print(f"Broken path: {broken_path}")

            # This should match the exact error pattern we see in logs
            expected_broken_pattern = "/app/var/users/None/loops/None/config"
            self.assertEqual(broken_path, expected_broken_pattern,
                           f"Broken path should match expected pattern: {expected_broken_pattern}")

            # And the WAKEUP.py file path should be the exact error we see
            wakeup_broken_path = os.path.join(broken_path, "WAKEUP.py")
            expected_error_path = "/app/var/users/None/loops/None/config/WAKEUP.py"
            self.assertEqual(wakeup_broken_path, expected_error_path,
                           f"WAKEUP.py path should match the error we see in logs: {expected_error_path}")

            # This test documents the exact broken behavior
            print(f"✅ This test confirms the broken path pattern: {expected_error_path}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)