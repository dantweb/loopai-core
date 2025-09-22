#!/usr/bin/env python3
"""
AsyncIO Thread Isolation Test

This test exposes the asyncio event loop conflicts in ThreadedLoopExecutor
by directly testing async loop execution in threaded environments.
"""

import asyncio
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from core.controllers.loop_controller import LoopController


class TestAsyncioThreadIsolation(unittest.TestCase):
    """Test asyncio event loop isolation in threaded execution"""

    def setUp(self):
        """Set up test environment"""
        self.test_yaml_content = """
session:
  name: test_async_loop
  code_source: ""
  loop:
    test_step:
      description: "Test async step"
      type: gpt
      input:
        type: text
        source: "test input"
      output:
        - text: {name: test_output}
      action:
        executor: gpt
        model: gpt-3.5-turbo
        prompt: "Test prompt"
"""

        # Create temporary YAML file
        self.yaml_file_path = '/tmp/test_async_loop.yaml'
        with open(self.yaml_file_path, 'w') as f:
            f.write(self.test_yaml_content)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.yaml_file_path):
            os.remove(self.yaml_file_path)

    def test_single_async_loop_execution(self):
        """Test that a single async loop can execute without errors"""
        with patch('core.services.session.session_manager') as mock_session:
            mock_session.has_current_session.return_value = False
            mock_session.regenerate_session_id.return_value = None
            mock_session.set_user_id.return_value = None
            mock_session.set_project_id.return_value = None
            mock_session.set_loop_id.return_value = None

            controller = LoopController(self.yaml_file_path, 1, 1, 1)

            # This should work without event loop conflicts
            try:
                result = asyncio.run(controller.run())
                self.assertIsNotNone(result, "Single async loop execution should succeed")
            except RuntimeError as e:
                if "event loop" in str(e).lower():
                    self.fail(f"Single async execution failed with event loop error: {e}")
                raise

    def test_concurrent_async_loop_execution_in_threads(self):
        """Test that multiple async loops can run concurrently in separate threads"""
        def run_loop_in_thread(thread_id):
            """Execute a loop asynchronously in a thread"""
            thread_name = f"TestThread-{thread_id}"
            threading.current_thread().name = thread_name

            with patch('core.services.session.session_manager') as mock_session:
                mock_session.has_current_session.return_value = False
                mock_session.regenerate_session_id.return_value = None
                mock_session.set_user_id.return_value = None
                mock_session.set_project_id.return_value = None
                mock_session.set_loop_id.return_value = None

                controller = LoopController(self.yaml_file_path, thread_id, 1, thread_id)

                # This is where the event loop conflict should occur
                try:
                    # Try the current approach that should fail
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(controller.run())
                        return {"thread_id": thread_id, "success": True, "result": result, "error": None}
                    finally:
                        loop.close()

                except Exception as e:
                    return {"thread_id": thread_id, "success": False, "result": None, "error": str(e)}

        # Test with multiple concurrent threads
        num_threads = 5
        results = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(run_loop_in_thread, i): i for i in range(num_threads)}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Analyze results
        successful_executions = [r for r in results if r["success"]]
        failed_executions = [r for r in results if not r["success"]]

        print(f"\n=== Concurrent Async Loop Test Results ===")
        print(f"Total threads: {num_threads}")
        print(f"Successful: {len(successful_executions)}")
        print(f"Failed: {len(failed_executions)}")

        if failed_executions:
            print(f"\nFailure Details:")
            for failure in failed_executions:
                print(f"  Thread {failure['thread_id']}: {failure['error']}")

        # Check for specific asyncio event loop conflicts
        event_loop_errors = [r for r in failed_executions if "event loop" in r["error"].lower()]
        if event_loop_errors:
            print(f"\nAsyncIO Event Loop Conflicts: {len(event_loop_errors)}")
            for error in event_loop_errors:
                print(f"  Thread {error['thread_id']}: {error['error']}")

            # This test should FAIL initially to expose the problem
            self.fail(f"Event loop conflicts detected in {len(event_loop_errors)} threads. "
                     f"This exposes the asyncio threading issue that needs to be fixed.")

        # All threads should succeed without event loop conflicts
        self.assertEqual(len(failed_executions), 0,
                        f"All {num_threads} threads should execute successfully without event loop conflicts")
        self.assertEqual(len(successful_executions), num_threads,
                        f"All {num_threads} threads should report successful execution")

    def test_asyncio_run_approach(self):
        """Test using asyncio.run() approach which should work better in threads"""
        def run_loop_with_asyncio_run(thread_id):
            """Execute a loop using asyncio.run() in a thread"""
            thread_name = f"AsyncioRunThread-{thread_id}"
            threading.current_thread().name = thread_name

            with patch('core.services.session.session_manager') as mock_session:
                mock_session.has_current_session.return_value = False
                mock_session.regenerate_session_id.return_value = None
                mock_session.set_user_id.return_value = None
                mock_session.set_project_id.return_value = None
                mock_session.set_loop_id.return_value = None

                controller = LoopController(self.yaml_file_path, thread_id, 1, thread_id)

                try:
                    # Use asyncio.run() which should handle event loop creation properly
                    result = asyncio.run(controller.run())
                    return {"thread_id": thread_id, "success": True, "result": result, "error": None}
                except Exception as e:
                    return {"thread_id": thread_id, "success": False, "result": None, "error": str(e)}

        # Test with multiple concurrent threads using asyncio.run()
        num_threads = 5
        results = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(run_loop_with_asyncio_run, i): i for i in range(num_threads)}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Analyze results
        successful_executions = [r for r in results if r["success"]]
        failed_executions = [r for r in results if not r["success"]]

        print(f"\n=== AsyncIO.run() Approach Test Results ===")
        print(f"Total threads: {num_threads}")
        print(f"Successful: {len(successful_executions)}")
        print(f"Failed: {len(failed_executions)}")

        if failed_executions:
            print(f"\nFailure Details:")
            for failure in failed_executions:
                print(f"  Thread {failure['thread_id']}: {failure['error']}")

        # asyncio.run() should work better - fewer event loop conflicts expected
        event_loop_errors = [r for r in failed_executions if "event loop" in r["error"].lower()]

        if len(event_loop_errors) < len(failed_executions):
            print(f"✅ asyncio.run() approach shows improvement: {len(event_loop_errors)} event loop errors vs {len(failed_executions)} total failures")

        # This should pass if asyncio.run() is the right approach
        self.assertLessEqual(len(event_loop_errors), 0,
                           f"asyncio.run() approach should eliminate event loop conflicts")

    def test_gevent_compatibility(self):
        """Test if gevent is interfering with asyncio event loops"""
        try:
            import gevent
            gevent_available = True
            print(f"\n=== Gevent Compatibility Test ===")
            print(f"Gevent version: {gevent.__version__}")

            # Check if gevent monkey patching is active
            from gevent import monkey
            if monkey.is_module_patched('socket'):
                print("⚠️  Gevent socket monkey patching is ACTIVE")
            if monkey.is_module_patched('threading'):
                print("⚠️  Gevent threading monkey patching is ACTIVE")
            if monkey.is_module_patched('time'):
                print("⚠️  Gevent time monkey patching is ACTIVE")

        except ImportError:
            gevent_available = False
            print(f"\n=== Gevent Compatibility Test ===")
            print("Gevent not available - this might explain why asyncio works")

        # This test is informational - it doesn't fail, just reports gevent status
        self.assertTrue(True, "Gevent compatibility check completed")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)