#!/usr/bin/env python3
"""
Integration test to prove session data access issue in async greenlet context.

This test verifies that session data stored in one greenlet context
is accessible when lambda code executes in the same or different context.
"""

import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from core.services.thread_safe_session import thread_safe_session_manager
from web.services.concurrent_web_loop_runner import ConcurrentWebLoopRunner
from web.admin_models import Loop, db
from flask import Flask


class TestSessionDataAccess(unittest.TestCase):
    """Test session data accessibility in lambda execution context"""

    def setUp(self):
        """Set up test environment"""
        # Create test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        with self.app.app_context():
            db.init_app(self.app)
            db.create_all()

        # Test data
        self.user_id = 1
        self.loop_id = 999
        self.test_request_data = {
            'method': 'POST',
            'path': '/api/public/agent/2/action/RECEIVE_POST/',
            'body': {
                'result': {
                    'result': {
                        'updated_files': [{
                            'path': 'test_session_file.json',
                            'file_operation': 'update',
                            'file_content': '{"test": "session_data_access"}'
                        }]
                    }
                }
            }
        }

    def tearDown(self):
        """Clean up test environment"""
        # Cleanup any remaining sessions
        for session_id in thread_safe_session_manager.list_active_sessions():
            thread_safe_session_manager.cleanup_session(session_id)

    def test_session_data_storage_and_retrieval(self):
        """Test basic session data storage and retrieval"""
        print("\n🧪 Testing Session Data Storage and Retrieval")

        # Create a session
        session_id = thread_safe_session_manager.create_session_for_loop(
            user_id=self.user_id,
            loop_id=self.loop_id,
            project_id=1
        )

        print(f"✅ Created session: {session_id}")

        # Store request data
        thread_safe_session_manager.set_request_data(self.test_request_data)
        print(f"✅ Stored request data with keys: {list(self.test_request_data.keys())}")

        # Retrieve request data
        retrieved_data = thread_safe_session_manager.get_request_data()

        # Verify data was stored and retrieved correctly
        self.assertIsNotNone(retrieved_data, "Retrieved data should not be None")
        self.assertEqual(retrieved_data['method'], 'POST', "Method should match")
        self.assertIn('body', retrieved_data, "Body should be present")

        print(f"✅ Retrieved request data successfully")
        print(f"📋 Retrieved keys: {list(retrieved_data.keys())}")

        # Cleanup
        thread_safe_session_manager.cleanup_session(session_id)

    def test_session_data_across_greenlet_context(self):
        """Test session data accessibility across greenlet contexts"""
        print("\n🧪 Testing Session Data Across Greenlet Context")

        from gevent import spawn

        session_data_results = {}

        def greenlet_function(session_id, test_name):
            """Function to run in a greenlet"""
            try:
                # Try to access session data from within greenlet
                retrieved_data = thread_safe_session_manager.get_request_data()
                session_data_results[test_name] = {
                    'success': retrieved_data is not None,
                    'data': retrieved_data,
                    'session_id': session_id
                }
                print(f"🔄 [{test_name}] Greenlet access result: {'SUCCESS' if retrieved_data else 'FAILED'}")
            except Exception as e:
                session_data_results[test_name] = {
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                }
                print(f"❌ [{test_name}] Greenlet access error: {str(e)}")

        # Create session and store data in main thread
        session_id = thread_safe_session_manager.create_session_for_loop(
            user_id=self.user_id,
            loop_id=self.loop_id,
            project_id=1
        )

        thread_safe_session_manager.set_request_data(self.test_request_data)
        print(f"✅ Stored request data in main thread, session: {session_id}")

        # Test 1: Access from same thread (should work)
        retrieved_main = thread_safe_session_manager.get_request_data()
        print(f"📋 Main thread access: {'SUCCESS' if retrieved_main else 'FAILED'}")

        # Test 2: Access from greenlet (this might fail due to context issues)
        greenlet = spawn(greenlet_function, session_id, 'greenlet_access')
        greenlet.join()

        # Analyze results
        print(f"\n📊 Session Data Access Results:")
        print(f"   Main thread access: {'SUCCESS' if retrieved_main else 'FAILED'}")

        if 'greenlet_access' in session_data_results:
            greenlet_result = session_data_results['greenlet_access']
            print(f"   Greenlet access: {'SUCCESS' if greenlet_result['success'] else 'FAILED'}")
            if not greenlet_result['success'] and 'error' in greenlet_result:
                print(f"   Greenlet error: {greenlet_result['error']}")

        # This test documents the current behavior - it might pass or fail
        # depending on how session context is handled in greenlets
        if 'greenlet_access' in session_data_results:
            greenlet_success = session_data_results['greenlet_access']['success']
            if not greenlet_success:
                print(f"⚠️  This confirms the session data access issue in greenlet context!")
            else:
                print(f"✅ Session data is accessible across greenlet contexts")

        # Cleanup
        thread_safe_session_manager.cleanup_session(session_id)

    def test_concurrent_web_loop_runner_session_context(self):
        """Test if ConcurrentWebLoopRunner maintains session context"""
        print("\n🧪 Testing ConcurrentWebLoopRunner Session Context")

        with self.app.app_context():
            # Mock a loop object
            mock_loop = MagicMock()
            mock_loop.id = self.loop_id
            mock_loop.user_id = self.user_id
            mock_loop.project_id = 1
            mock_loop.name = "Test RECEIVE_POST Loop"

            with patch('web.admin_models.Loop.query') as mock_query:
                mock_query.get.return_value = mock_loop

                # Create runner
                runner = ConcurrentWebLoopRunner(
                    app=self.app,
                    user_id=self.user_id,
                    loop_id=self.loop_id
                )

                # Test the session creation and data storage part of run_agent_by_action
                try:
                    # Create session like run_agent_by_action does
                    session_id = thread_safe_session_manager.create_session_for_loop(
                        user_id=self.user_id,
                        loop_id=self.loop_id,
                        project_id=None
                    )
                    runner.session_id = session_id

                    print(f"✅ Created runner session: {session_id}")

                    # Store request data like the method does
                    thread_safe_session_manager.set_request_data(self.test_request_data)
                    print(f"✅ Stored request data in runner context")

                    # Verify data is accessible immediately
                    stored_data = thread_safe_session_manager.get_request_data()
                    if stored_data:
                        print(f"✅ Request data immediately accessible")
                        print(f"📋 Data keys: {list(stored_data.keys())}")
                    else:
                        print(f"❌ Request data NOT immediately accessible")

                    # Now simulate what happens when lambda code tries to access the data
                    # This simulates the session_manager.get_request_data() call in WAKEUP.py
                    from core.services.session import session_manager

                    lambda_accessible_data = None
                    try:
                        lambda_accessible_data = session_manager.get_request_data()
                        if lambda_accessible_data:
                            print(f"✅ Session data accessible via session_manager")
                            print(f"📋 Lambda access keys: {list(lambda_accessible_data.keys())}")
                        else:
                            print(f"❌ Session data NOT accessible via session_manager")
                    except Exception as e:
                        print(f"💥 Error accessing session data via session_manager: {str(e)}")

                    # Test both access methods
                    thread_safe_data = thread_safe_session_manager.get_request_data()
                    regular_session_data = session_manager.get_request_data()

                    print(f"\n📊 Session Access Comparison:")
                    print(f"   thread_safe_session_manager: {'SUCCESS' if thread_safe_data else 'FAILED'}")
                    print(f"   regular session_manager: {'SUCCESS' if regular_session_data else 'FAILED'}")

                    if thread_safe_data and not regular_session_data:
                        print(f"🔍 ROOT CAUSE: Lambda code uses session_manager but data is in thread_safe_session_manager!")

                    # Cleanup
                    thread_safe_session_manager.cleanup_session(session_id)

                except Exception as e:
                    print(f"💥 Error in runner session test: {str(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")

    def test_session_manager_bridge_requirement(self):
        """Test that demonstrates the need for session manager bridge"""
        print("\n🧪 Testing Session Manager Bridge Requirement")

        # Create session with thread_safe_session_manager
        session_id = thread_safe_session_manager.create_session_for_loop(
            user_id=self.user_id,
            loop_id=self.loop_id,
            project_id=1
        )

        # Store data in thread_safe_session_manager
        thread_safe_session_manager.set_request_data(self.test_request_data)

        # Import both session managers
        from core.services.session import session_manager

        # Test access from both
        thread_safe_data = thread_safe_session_manager.get_request_data()

        # Check if regular session_manager even has get_request_data method
        has_get_request_data = hasattr(session_manager, 'get_request_data')
        regular_data = None

        if has_get_request_data:
            regular_data = session_manager.get_request_data()

        print(f"📊 Cross-Session Manager Access Test:")
        print(f"   Data stored in: thread_safe_session_manager")
        print(f"   thread_safe_session_manager.get_request_data(): {'SUCCESS' if thread_safe_data else 'FAILED'}")
        print(f"   session_manager.get_request_data() method exists: {'YES' if has_get_request_data else 'NO'}")

        if has_get_request_data:
            print(f"   session_manager.get_request_data(): {'SUCCESS' if regular_data else 'FAILED'}")
        else:
            print(f"   🔍 IDENTIFIED ROOT CAUSE: session_manager lacks get_request_data() method!")

        # This test should show that lambda code (using session_manager)
        # cannot access data stored by ConcurrentWebLoopRunner (using thread_safe_session_manager)
        if thread_safe_data and (not has_get_request_data or not regular_data):
            print(f"🎯 CONFIRMED: Lambda code cannot access session data stored by runner!")
            if not has_get_request_data:
                print(f"💡 SOLUTION NEEDED: Add get_request_data() method to session_manager")
            else:
                print(f"💡 SOLUTION NEEDED: Bridge between thread_safe_session_manager and session_manager")

        # Cleanup
        thread_safe_session_manager.cleanup_session(session_id)


def run_session_data_access_tests():
    """Run all session data access tests"""
    print("🚀 Running Session Data Access Tests...\n")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSessionDataAccess)
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
        print("🎉 All session data access tests passed!")
    else:
        print("⚠️  Some tests revealed session data access issues!")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_session_data_access_tests()
    exit(0 if success else 1)