import os
import unittest
import asyncio
import time
import psutil
import jwt
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from gevent import spawn, sleep
from gevent import monkey; monkey.patch_all()

# We'll test the route function directly but with proper mocking
# to avoid the Flask-Login authentication complexity

class TestConcurrentRoutesFixed(unittest.TestCase):
    """
    Test concurrent loop execution by bypassing authentication middleware
    and testing the core functionality directly.
    """

    def setUp(self):
        # Create a Flask test app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key-for-jwt'

        # Mock current_user
        self.current_user = Mock()
        self.current_user.id = 1

        # Mock the Loop model
        self.loop_mock_1 = Mock()
        self.loop_mock_1.id = 1
        self.loop_mock_1.user_id = 1
        self.loop_mock_1.project_id = 1
        # Add user attribute for the route code that accesses loop.user.id
        self.loop_mock_1.user = Mock()
        self.loop_mock_1.user.id = 1

        self.loop_mock_2 = Mock()
        self.loop_mock_2.id = 2
        self.loop_mock_2.user_id = 1
        self.loop_mock_2.project_id = 1
        # Add user attribute for the route code that accesses loop.user.id
        self.loop_mock_2.user = Mock()
        self.loop_mock_2.user.id = 1

        # Start patching before importing the route function
        self.patcher_loop = patch('web.routes.loops.Loop')
        self.mock_loop_model = self.patcher_loop.start()
        self.mock_loop_model.query.get.side_effect = lambda x: (
            self.loop_mock_1 if x == 1 else
            self.loop_mock_2 if x == 2 else
            None
        )

        self.patcher_send_message = patch('web.routes.loops.send_message_to_user')
        self.mock_send_message = self.patcher_send_message.start()

        # Patch the async_loop_executor instead of ConcurrentWebLoopRunner
        self.patcher_async_executor = patch('web.routes.loops.async_loop_executor')
        self.mock_async_executor = self.patcher_async_executor.start()

        # Create a mock future result for async_loop_executor
        self.mock_future = Mock()
        self.mock_future.result.return_value = "Test output"
        self.mock_async_executor.execute_loop_async.return_value = self.mock_future

        # Get process for metrics
        self.process = psutil.Process(os.getpid())

        # Now import the function we want to test after patching
        from web.routes.loops import run_loop
        self.run_loop_function = run_loop

    def tearDown(self):
        # Clean up patches
        self.patcher_loop.stop()
        self.patcher_send_message.stop()
        self.patcher_async_executor.stop()

    def test_run_loop_function_directly(self):
        """Test the run_loop function directly without authentication middleware"""

        results = []
        loop_ids = [1, 2]

        def call_run_loop(loop_id):
            with self.app.test_request_context():
                try:
                    # Call the function directly, bypassing the @token_required decorator
                    # by calling the underlying function
                    result = self.run_loop_function.__wrapped__(self.current_user, loop_id)
                    results.append({'loop_id': loop_id, 'result': result, 'success': True})
                except Exception as e:
                    results.append({'loop_id': loop_id, 'error': str(e), 'success': False})

        # Measure start time
        start_time = time.time()
        start_memory = self.process.memory_info().rss / (1024 * 1024)

        # Execute multiple loops concurrently
        greenlets = [spawn(call_run_loop, loop_id) for loop_id in loop_ids]
        for g in greenlets:
            g.join()

        # Allow async operations to complete
        sleep(0.5)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / (1024 * 1024)

        # Print metrics
        elapsed_time = end_time - start_time
        memory_used = end_memory - start_memory
        print(f"\n=== Direct Route Function Test ===")
        print(f"Time consumed: {elapsed_time:.4f} seconds")
        print(f"Memory consumed: {memory_used:.2f} MB")
        print(f"Results: {results}")

        # Assert results
        self.assertEqual(len(results), len(loop_ids), "All calls should complete")

        # Verify successful calls
        successful_calls = [r for r in results if r.get('success')]
        self.assertEqual(len(successful_calls), len(loop_ids), f"All calls should succeed: {results}")

        # Check response format
        for result_data in successful_calls:
            result = result_data['result']
            self.assertIsInstance(result, tuple, "Should return (response, status_code)")
            self.assertEqual(len(result), 2, "Should return (response, status_code)")

            response, status_code = result
            self.assertEqual(status_code, 200, "Should return 200 status")

            response_json = response.get_json()
            self.assertEqual(response_json.get('success'), True, "Should indicate success")
            self.assertEqual(response_json.get('message'), "Loop is running.", "Should have correct message")

        # Verify mocks were called
        self.assertGreater(self.mock_loop_model.query.get.call_count, 0, "Should query for loops")
        self.assertGreater(self.mock_async_executor.execute_loop_async.call_count, 0, "Should call async executor")
        self.assertGreater(self.mock_send_message.call_count, 0, "Should send messages")

    def test_invalid_loop_handling(self):
        """Test that invalid loop IDs are handled correctly"""

        with self.app.test_request_context():
            # Test with loop ID that returns None
            result = self.run_loop_function.__wrapped__(self.current_user, 999)

            self.assertIsInstance(result, tuple, "Should return (response, status_code)")
            response, status_code = result
            self.assertEqual(status_code, 404, "Should return 404 for invalid loop")

            response_json = response.get_json()
            self.assertEqual(response_json.get('success'), False, "Should indicate failure")
            self.assertEqual(response_json.get('message'), "Loop not found.", "Should have correct error message")

    def test_concurrent_executor_usage(self):
        """Test that async_loop_executor is properly called"""

        with self.app.test_request_context():
            # Call the function
            result = self.run_loop_function.__wrapped__(self.current_user, 1)

            # Wait for async operations to complete
            sleep(0.1)

            # Verify async_loop_executor was called with correct parameters
            self.mock_async_executor.execute_loop_async.assert_called()
            call_args = self.mock_async_executor.execute_loop_async.call_args

            # The call should have app, user_id, loop_id parameters
            self.assertIsNotNone(call_args, "async_loop_executor.execute_loop_async should be called")

            # Verify parameters - call_args is (args, kwargs)
            args, kwargs = call_args
            self.assertEqual(len(args), 3, "Should have 3 positional args: app, user_id, loop_id")

            # args[1] should be user_id, args[2] should be loop_id
            self.assertEqual(args[1], 1, "User ID should be 1")
            self.assertEqual(args[2], 1, "Loop ID should be 1")

            # Verify the response indicates success
            response, status_code = result
            self.assertEqual(status_code, 200, "Should return success status")

            response_json = response.get_json()
            self.assertEqual(response_json.get('success'), True, "Should indicate success")


class TestSessionIsolationCore(unittest.TestCase):
    """Test session isolation without any Flask dependencies"""

    def setUp(self):
        from core.services.thread_safe_session import thread_safe_session_manager
        self.session_manager = thread_safe_session_manager

        # Clean up any existing sessions
        for session_id in self.session_manager.list_active_sessions():
            self.session_manager.cleanup_session(session_id)

    def tearDown(self):
        # Clean up all sessions
        for session_id in self.session_manager.list_active_sessions():
            self.session_manager.cleanup_session(session_id)

    def test_concurrent_session_isolation(self):
        """Test that GeventLoopExecutor maintains session isolation between greenlets"""
        from web.services.async_loop_executor import async_loop_executor, GreenletSessionContext

        results = {}

        def create_isolated_session(thread_id):
            # Create greenlet-local session context directly
            session_context = GreenletSessionContext(
                user_id=thread_id,
                loop_id=thread_id + 100,
                project_id=thread_id + 200
            )

            # Set greenlet-specific data
            session_context.set_step_name(f"step_{thread_id}")
            session_context.set_environment({'thread_id': thread_id, 'data': f"data_{thread_id}"})

            # Simulate some work
            sleep(0.05)

            # Collect results from the session context
            results[thread_id] = {
                'session_id': session_context.get_session_id(),
                'user_id': session_context.get_user_id(),
                'loop_id': session_context.get_loop_id(),
                'project_id': session_context.get_project_id(),
                'thread_data': session_context.get_env('thread_id'),
                'custom_data': session_context.get_env('data')
            }

        # Run concurrent sessions using greenlets
        num_threads = 5
        greenlets = [spawn(create_isolated_session, i) for i in range(num_threads)]
        for g in greenlets:
            g.join()

        # Verify results
        self.assertEqual(len(results), num_threads, "All sessions should complete")

        for thread_id, data in results.items():
            self.assertEqual(data['user_id'], thread_id, f"User ID should match for thread {thread_id}")
            self.assertEqual(data['loop_id'], thread_id + 100, f"Loop ID should match for thread {thread_id}")
            self.assertEqual(data['project_id'], thread_id + 200, f"Project ID should match for thread {thread_id}")
            self.assertEqual(data['thread_data'], thread_id, f"Thread data should match for thread {thread_id}")
            self.assertEqual(data['custom_data'], f"data_{thread_id}", f"Custom data should match for thread {thread_id}")

        print(f"✅ Session isolation test passed - all {num_threads} greenlets maintained isolated session data")


if __name__ == '__main__':
    unittest.main()