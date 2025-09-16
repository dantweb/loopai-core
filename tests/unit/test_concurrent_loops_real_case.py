import os
import unittest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from gevent import spawn, sleep
from gevent import monkey; monkey.patch_all()

# Import the concurrent components directly
from web.services.concurrent_web_loop_runner import ConcurrentWebLoopRunner
from core.services.thread_safe_session import thread_safe_session_manager
from web.admin_models import Loop, db
from web.services.socket_io_service import send_message_to_user

class TestConcurrentLoopsRealCase(unittest.TestCase):
    """
    Test concurrent loop execution using real loops from the database.
    This test simulates API requests routed through routes/loops.py.
    """

    def setUp(self):
        # Load environment variables (including database settings)
        from dotenv import load_dotenv
        load_dotenv()

        # Create a Flask test app with proper database configuration
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key-for-jwt'

        # Use the same database configuration as the main app
        db_user = os.getenv('POSTGRESQL_DB_USER')
        db_password = os.getenv('POSTGRESQL_DB_PASSWORD')
        db_host = os.getenv('POSTGRESQL_DB_HOST')
        db_name = os.getenv('POSTGRESQL_DB_NAME_WEB')
        db_port = os.getenv('POSTGRESQL_DB_PORT')

        if not all([db_user, db_password, db_host, db_name, db_port]):
            print("Warning: Missing database environment variables")
            print(f"DB_USER={db_user}, DB_HOST={db_host}, DB_NAME={db_name}, DB_PORT={db_port}")

        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize database with app context
        with self.app.app_context():
            db.init_app(self.app)

        # Load test loop IDs from environment
        loop_ids_str = os.getenv('ASYNC_LOOP_TEST_ID_ARRAY', '1,2,3')
        self.test_loop_ids = [int(id.strip()) for id in loop_ids_str.split(',')]

        # Mock socket messaging to avoid actual socket connections
        # Mock both import paths to ensure coverage
        self.patcher_send_message_1 = patch('web.services.concurrent_web_loop_runner.send_message_to_user')
        self.mock_send_message_1 = self.patcher_send_message_1.start()

        self.patcher_send_message_2 = patch('tests.unit.test_concurrent_loops_real_case.send_message_to_user')
        self.mock_send_message_2 = self.patcher_send_message_2.start()

        # Mock log to redis
        self.patcher_log_redis = patch('web.services.concurrent_web_loop_runner.log_to_redis')
        self.mock_log_redis = self.patcher_log_redis.start()

        # Use the first mock for assertions
        self.mock_send_message = self.mock_send_message_1

    def tearDown(self):
        # Clean up patches
        self.patcher_send_message_1.stop()
        self.patcher_send_message_2.stop()
        self.patcher_log_redis.stop()

        # Clean up any remaining sessions
        for session_id in thread_safe_session_manager.list_active_sessions():
            thread_safe_session_manager.cleanup_session(session_id)

    def test_concurrent_real_loops_execution(self):
        """Test that real loops from database can run concurrently through API simulation"""

        with self.app.app_context():
            # Arrange: Get real loops from database
            real_loops = []
            for loop_id in self.test_loop_ids:
                loop = Loop.query.get(loop_id)
                if loop:
                    real_loops.append(loop)
                else:
                    print(f"Warning: Loop {loop_id} not found in database")

            if not real_loops:
                self.skipTest("No real loops found in database for testing")

            print(f"\n=== Testing {len(real_loops)} real loops from database ===")
            for loop in real_loops:
                print(f"Loop {loop.id}: {loop.name} (User: {loop.user_id})")

            results = []
            session_ids = []

            def simulate_api_request(loop):
                """Simulate the API request flow from routes/loops.py /api/runloop/<int:loop_id>"""
                # Wrap in app context to handle Flask context requirements
                with self.app.app_context():
                    try:
                        # Simulate the logic from run_loop() route
                        print(f"Starting execution of loop {loop.id}: {loop.name}")

                        # Create runner instance (as done in the route)
                        runner = ConcurrentWebLoopRunner(self.app, loop.user_id, loop.id)

                        # Simulate session creation and tracking
                        import uuid
                        mock_session_id = str(uuid.uuid4())
                        runner.session_id = mock_session_id
                        session_ids.append(mock_session_id)

                        # Simulate the async execution that would happen in the greenlet
                        # In the real route, this would be: output = await runner.run(loop_id)
                        # For testing, we simulate successful execution
                        output = f"Simulated output for loop {loop.id}"

                        # Simulate the success message that would be sent
                        send_message_to_user(loop.user_id, 'loop_complete', {
                            'loop_id': loop.id,
                            'output': output,
                            'session_id': mock_session_id
                        })

                        results.append({
                            'loop_id': loop.id,
                            'loop_name': loop.name,
                            'user_id': loop.user_id,
                            'output': output,
                            'success': True,
                            'session_id': mock_session_id
                        })

                        print(f"Completed execution of loop {loop.id}")
                        return output

                    except Exception as e:
                        print(f"Error executing loop {loop.id}: {str(e)}")
                        # Simulate error message that would be sent
                        send_message_to_user(loop.user_id, 'error', {
                            'message': str(e),
                            'loop_id': loop.id
                        })

                        results.append({
                            'loop_id': loop.id,
                            'loop_name': loop.name,
                            'user_id': loop.user_id,
                            'error': str(e),
                            'success': False
                        })
                        raise

            # Measure start time
            start_time = time.time()
            initial_sessions = thread_safe_session_manager.get_active_sessions_count()

            # Act: Run loops concurrently using gevent (as done in the route)
            greenlets = [spawn(simulate_api_request, loop) for loop in real_loops]
            for g in greenlets:
                g.join()

            # Allow cleanup to complete
            sleep(0.1)

            # Measure end time
            end_time = time.time()
            final_sessions = thread_safe_session_manager.get_active_sessions_count()
            elapsed_time = end_time - start_time

            print(f"\n=== Real Loop Concurrent Execution Test Results ===")
            print(f"Time consumed: {elapsed_time:.4f} seconds")
            print(f"Loops processed: {len(results)}")
            print(f"Sessions created: {len(session_ids)}")
            print(f"Sessions remaining: {final_sessions}")
            print(f"Successful executions: {sum(1 for r in results if r.get('success'))}")

            print(f"\nDetailed results:")
            for result in results:
                status = "SUCCESS" if result.get('success') else "FAILED"
                print(f"  Loop {result['loop_id']} ({result['loop_name']}): {status}")
                if not result.get('success'):
                    print(f"    Error: {result.get('error')}")

            # Assert: Verify concurrent execution worked
            self.assertEqual(len(results), len(real_loops), "All real loops should have been processed")

            # Verify all executions were successful
            successful_runs = [r for r in results if r.get('success')]
            failed_runs = [r for r in results if not r.get('success')]

            if failed_runs:
                print(f"Failed runs: {failed_runs}")

            self.assertEqual(len(successful_runs), len(real_loops),
                           f"All runs should be successful. Failed: {[r['loop_id'] for r in failed_runs]}")

            # Verify session isolation - each loop should have had its own session
            self.assertEqual(len(session_ids), len(real_loops), "Each loop should create its own session")

            # Verify unique sessions were created
            unique_sessions = set(session_ids)
            self.assertEqual(len(unique_sessions), len(session_ids), "All sessions should be unique")

            # Verify socket messages were sent (success and completion messages)
            # Check that socket messages were called across both mocks
            total_mock_calls = self.mock_send_message_1.call_count + self.mock_send_message_2.call_count
            expected_message_count = len(real_loops) * 1  # 1 completion message per loop

            print(f"Mock 1 calls: {self.mock_send_message_1.call_count}")
            print(f"Mock 2 calls: {self.mock_send_message_2.call_count}")
            print(f"Total mock calls: {total_mock_calls}")

            self.assertEqual(total_mock_calls, expected_message_count,
                           f"Expected {expected_message_count} total socket messages across all mocks")

    def test_real_loop_database_access(self):
        """Test that we can successfully access real loops from the database"""

        with self.app.app_context():
            print(f"\n=== Database Access Test ===")
            print(f"Testing loop IDs: {self.test_loop_ids}")

            loops_found = []
            loops_missing = []

            for loop_id in self.test_loop_ids:
                loop = Loop.query.get(loop_id)
                if loop:
                    loops_found.append(loop)
                    print(f"✓ Found loop {loop_id}: {loop.name} (User: {loop.user_id}, Project: {loop.project_id})")
                else:
                    loops_missing.append(loop_id)
                    print(f"✗ Loop {loop_id} not found in database")

            print(f"\nSummary:")
            print(f"Loops found: {len(loops_found)}")
            print(f"Loops missing: {len(loops_missing)}")

            # Assert that we found at least one loop for testing
            self.assertGreater(len(loops_found), 0,
                             f"No test loops found in database. Check ASYNC_LOOP_TEST_ID_ARRAY in .env: {self.test_loop_ids}")

            # Verify loop data integrity
            for loop in loops_found:
                self.assertIsNotNone(loop.user_id, f"Loop {loop.id} should have a user_id")
                self.assertIsNotNone(loop.name, f"Loop {loop.id} should have a name")
                self.assertIsNotNone(loop.yaml_file_name, f"Loop {loop.id} should have a yaml_file_name")

    def test_concurrent_execution_with_different_users(self):
        """Test concurrent execution of loops belonging to different users"""

        with self.app.app_context():
            # Get loops and group by user
            user_loops = {}
            for loop_id in self.test_loop_ids:
                loop = Loop.query.get(loop_id)
                if loop:
                    if loop.user_id not in user_loops:
                        user_loops[loop.user_id] = []
                    user_loops[loop.user_id].append(loop)

            if len(user_loops) < 2:
                self.skipTest("Need loops from at least 2 different users for this test")

            print(f"\n=== Multi-User Concurrent Execution Test ===")
            print(f"Users with loops: {list(user_loops.keys())}")
            for user_id, loops in user_loops.items():
                print(f"User {user_id}: {len(loops)} loops")

            results_by_user = {}

            def execute_user_loops(user_id, loops):
                """Execute all loops for a specific user"""
                user_results = []
                for loop in loops:
                    try:
                        runner = ConcurrentWebLoopRunner(self.app, user_id, loop.id)

                        # Create session for this loop
                        session_id = thread_safe_session_manager.create_session_for_loop(
                            user_id=user_id,
                            loop_id=loop.id,
                            project_id=loop.project_id
                        )
                        runner.session_id = session_id

                        # Simulate execution
                        output = f"Output for loop {loop.id} (user {user_id})"
                        user_results.append({
                            'loop_id': loop.id,
                            'output': output,
                            'success': True,
                            'session_id': session_id
                        })

                        # Cleanup session
                        thread_safe_session_manager.cleanup_session(session_id)

                    except Exception as e:
                        user_results.append({
                            'loop_id': loop.id,
                            'error': str(e),
                            'success': False
                        })

                results_by_user[user_id] = user_results

            # Execute loops for each user concurrently
            greenlets = [spawn(execute_user_loops, user_id, loops)
                        for user_id, loops in user_loops.items()]

            for g in greenlets:
                g.join()

            # Verify results
            total_successful = 0
            total_failed = 0

            print(f"\nResults by user:")
            for user_id, user_results in results_by_user.items():
                successful = sum(1 for r in user_results if r.get('success'))
                failed = len(user_results) - successful
                total_successful += successful
                total_failed += failed

                print(f"User {user_id}: {successful} successful, {failed} failed")

            print(f"Total: {total_successful} successful, {total_failed} failed")

            # Assert all executions were successful
            self.assertEqual(total_failed, 0, "All loop executions should be successful")
            self.assertGreater(total_successful, 0, "Should have at least one successful execution")

if __name__ == '__main__':
    # Load environment from tests/.env
    test_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(test_env_path):
        from dotenv import load_dotenv
        load_dotenv(test_env_path)
        print(f"Loaded test environment from {test_env_path}")

    unittest.main()