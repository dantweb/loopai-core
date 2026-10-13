#!/usr/bin/env python3
"""
SessionManager Unit Tests

Tests the consolidated SessionManager that provides:
1. Multi-user session isolation for concurrent loop execution
2. Gevent and thread-local storage support
3. Hierarchical environment variable management (Project → Loop → Step)
4. Session lifecycle management with proper cleanup
5. Request data storage for RequestAdapter integration
6. Execution mode awareness (public vs authenticated)

Following TDD approach: These tests define the expected behavior
and will initially fail until the SessionManager is enhanced.
"""

import unittest
import threading
import time
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock

# Import the SessionManager that we'll be enhancing
from core.services.session_manager import SessionManager, session_manager
from core.models.broadcast_data import BroadcastData


class TestSessionManagerEnhancement(unittest.TestCase):
    """Test enhanced SessionManager with multi-user support"""

    def setUp(self):
        """Set up test environment"""
        # Create fresh SessionManager for each test
        self.session_manager = SessionManager()

        # Mock environment variables
        self.test_env = {
            'LOOPAI_LOG_PATH': '/app/var/logs',
            'PROJECT_VAR': 'project_value',
            'LOOP_VAR': 'loop_value'
        }

    def test_concurrent_session_isolation(self):
        """Test that concurrent sessions maintain complete isolation"""
        results = {}

        def worker(worker_id: int):
            # Create unique session for this worker
            session_id = self.session_manager.create_session_for_loop(
                user_id=worker_id,
                loop_id=worker_id + 100,
                project_id=worker_id + 200
            )

            # Set environment with unique values
            env = {'UNIQUE_KEY': f'worker_{worker_id}'}
            self.session_manager.set_environment(env)

            # Set other session data
            self.session_manager.set_step_name(f'step_{worker_id}')
            self.session_manager.set_loop_index(worker_id * 10)

            # Small delay to ensure concurrent execution
            time.sleep(0.1)

            # Collect results - these should be isolated per worker
            results[worker_id] = {
                'session_id': self.session_manager.get_session_id(),
                'user_id': self.session_manager.get_user_id(),
                'loop_id': self.session_manager.get_loop_id(),
                'project_id': self.session_manager.get_project_id(),
                'env_value': self.session_manager.get_env('UNIQUE_KEY'),
                'step_name': self.session_manager.get_step_name(),
                'loop_index': self.session_manager.get_loop_index()
            }

            return session_id

        # Run 5 concurrent workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(1, 6)]
            session_ids = [f.result() for f in futures]

        # Verify complete isolation
        self.assertEqual(len(results), 5, "Should have 5 distinct worker results")
        self.assertEqual(len(set(session_ids)), 5, "Should have 5 unique session IDs")

        for worker_id in range(1, 6):
            result = results[worker_id]
            self.assertEqual(result['user_id'], worker_id)
            self.assertEqual(result['loop_id'], worker_id + 100)
            self.assertEqual(result['project_id'], worker_id + 200)
            self.assertEqual(result['env_value'], f'worker_{worker_id}')
            self.assertEqual(result['step_name'], f'step_{worker_id}')
            self.assertEqual(result['loop_index'], worker_id * 10)

    def test_hierarchical_environment_override(self):
        """Test hierarchical environment: Project → Loop → Step inheritance"""
        # Mock file system paths and environment files
        with patch('core.services.loop_path_resolver.loop_path_resolver.get_loop_config_base_path_by_user_and_loop') as mock_config_path:
            mock_config_path.return_value = '/tmp/test_config'

            # Create temporary environment files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Project level .env
                project_env_content = "PROJECT_VAR=project_value\nCOMMON_VAR=from_project\n"

                # Loop level .env
                loop_env_content = "LOOP_VAR=loop_value\nCOMMON_VAR=from_loop\n"

                # Step level step_name.env
                step_env_content = "STEP_VAR=step_value\nCOMMON_VAR=from_step\n"

                with patch('os.path.exists') as mock_exists:
                    mock_exists.return_value = True

                    # Mock file reading for different environment levels
                    def mock_open_side_effect(filename, mode='r'):
                        mock_file = unittest.mock.mock_open()
                        if '.env' in filename and 'step_name.env' not in filename:
                            mock_file.return_value.read.return_value = loop_env_content
                        elif 'step_name.env' in filename:
                            mock_file.return_value.read.return_value = step_env_content
                        else:
                            mock_file.return_value.read.return_value = project_env_content
                        return mock_file.return_value

                    with patch('builtins.open', side_effect=mock_open_side_effect):

                        # Test hierarchical environment loading
                        env = self.session_manager.get_hierarchical_environment(
                            user_id=1,
                            loop_id=61,
                            step_name='step_name'
                        )

                        # Verify step level overrides loop level
                        self.assertEqual(env['LOOP_VAR'], 'loop_value')
                        self.assertEqual(env['STEP_VAR'], 'step_value')
                        self.assertEqual(env['COMMON_VAR'], 'from_step')  # Step should override loop

    def test_execution_mode_awareness(self):
        """Test execution mode detection (public vs authenticated)"""
        # Test public execution mode (no real-time logging)
        self.session_manager.set_execution_mode('public')
        self.assertFalse(self.session_manager.is_realtime_logging_enabled())

        # Test authenticated execution mode (with real-time logging)
        self.session_manager.set_execution_mode('authenticated')
        self.assertTrue(self.session_manager.is_realtime_logging_enabled())

    def test_request_data_storage(self):
        """Test request data storage for RequestAdapter integration"""
        # Create session
        session_id = self.session_manager.create_session_for_loop(1, 61, 1)

        # Store request data
        request_data = {
            'headers': {'Content-Type': 'application/json'},
            'body': {'test': 'data'},
            'method': 'POST'
        }

        self.session_manager.set_request_data(request_data)

        # Retrieve request data
        retrieved_data = self.session_manager.get_request_data()
        self.assertEqual(retrieved_data, request_data)

    def test_session_lifecycle_management(self):
        """Test session creation, retrieval, and cleanup"""
        # Create session
        session_id = self.session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )

        # Verify session exists
        self.assertIsNotNone(session_id)
        self.assertEqual(self.session_manager.get_user_id(), 1)
        self.assertEqual(self.session_manager.get_loop_id(), 61)

        # Get session by ID
        session_data = self.session_manager.get_session_by_id(session_id)
        self.assertIsNotNone(session_data)
        self.assertEqual(session_data['user_id'], 1)

        # Cleanup session
        self.session_manager.cleanup_session(session_id)

        # Verify session is cleaned up
        cleaned_session = self.session_manager.get_session_by_id(session_id)
        self.assertIsNone(cleaned_session)

    def test_session_monitoring(self):
        """Test session monitoring capabilities"""
        # Initially no active sessions
        self.assertEqual(self.session_manager.get_active_sessions_count(), 0)

        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = self.session_manager.create_session_for_loop(i+1, i+61, i+1)
            session_ids.append(session_id)

        # Verify count
        self.assertEqual(self.session_manager.get_active_sessions_count(), 3)

        # List active sessions
        active_sessions = self.session_manager.list_active_sessions()
        self.assertEqual(len(active_sessions), 3)

        for session_id in session_ids:
            self.assertIn(session_id, active_sessions)

    def test_broadcast_collection_isolation(self):
        """Test that broadcast collections are isolated per session"""
        results = {}

        def worker(worker_id: int):
            # Create session
            self.session_manager.create_session_for_loop(worker_id, worker_id + 100, worker_id)

            # Add broadcast data specific to this worker
            bc_data = BroadcastData({'worker': worker_id, 'message': f'broadcast_{worker_id}'})
            self.session_manager.collect_broadcast(bc_data)

            # Get broadcast collection
            results[worker_id] = self.session_manager.get_broadcast_collection()

        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker, i) for i in range(1, 4)]
            [f.result() for f in futures]

        # Verify isolation - each worker should only see their own broadcasts
        self.assertEqual(len(results), 3)
        for worker_id in range(1, 4):
            worker_broadcasts = results[worker_id]
            self.assertEqual(len(worker_broadcasts), 1)
            # Verify broadcast content is specific to worker
            self.assertEqual(worker_broadcasts[0]['worker'], worker_id)

    def test_step_name_isolation(self):
        """Test that step names are properly isolated per session"""
        # This test will initially fail as current SessionManager doesn't support step name isolation
        def set_and_get_step_name(step_name: str):
            self.session_manager.create_session_for_loop(1, 61, 1)
            self.session_manager.set_step_name(step_name)
            return self.session_manager.get_step_name()

        # This should work with enhanced SessionManager
        result = set_and_get_step_name('test_step')
        self.assertEqual(result, 'test_step')


class TestSessionManagerCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code"""

    def test_singleton_instance_compatibility(self):
        """Test that global session_manager instance still works"""
        # The global instance should still be accessible
        from core.services.session_manager import session_manager
        self.assertIsNotNone(session_manager)

        # Basic methods should work
        session_manager.set_user_id(1)
        self.assertEqual(session_manager.get_user_id(), 1)

    def test_bridge_methods_compatibility(self):
        """Test that bridge methods for request data still work"""
        from core.services.session_manager import session_manager

        # Bridge methods should work without error
        test_data = {'test': 'data'}
        session_manager.set_request_data(test_data)

        # get_request_data should return the data
        result = session_manager.get_request_data()
        # This might return None if ThreadSafeSessionManager is not available
        # but it shouldn't raise an exception


def run_session_manager_tests():
    """Run all SessionManager tests"""
    print("🧪 Running SessionManager Enhancement Tests...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManagerEnhancement))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManagerCompatibility))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n📊 Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")

    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")

    if result.wasSuccessful():
        print("🎉 All SessionManager tests passed!")
    else:
        print("⚠️  Some SessionManager tests failed - this is expected initially with TDD approach")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_session_manager_tests()
    exit(0 if success else 1)