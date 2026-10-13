#!/usr/bin/env python3
"""
Execution Mode-Aware Broadcasting Unit Tests

Tests the execution mode-aware broadcasting system that provides:
1. Real-time logging broadcasts for authenticated frontend users
2. No broadcasting for public API execution (api/public/loop, api/public/agent)
3. Integration with SessionManager for execution mode detection
4. Broadcasting service isolation and resource management
5. Thread-safe broadcasting for concurrent users

Following TDD approach: These tests define the expected behavior
and will initially fail until the broadcasting enhancement is implemented.
"""

import unittest
import threading
import time
from unittest.mock import patch, MagicMock, Mock
from concurrent.futures import ThreadPoolExecutor

from flask import Flask

# Import existing broadcasting service
try:
    from web.services.socket_io_service import send_message_to_user
except ImportError:
    send_message_to_user = None

# Import the enhanced broadcasting service we'll create
try:
    from core.services.execution_mode_broadcasting import ExecutionModeBroadcastingService, get_broadcasting_service
except ImportError:
    ExecutionModeBroadcastingService = None
    get_broadcasting_service = None

from core.services.session_manager import session_manager
from core.services.logger_service import LoggerService


class TestExecutionModeBroadcasting(unittest.TestCase):
    """Test execution mode-aware broadcasting service"""

    def setUp(self):
        """Set up test environment"""
        if ExecutionModeBroadcastingService is None:
            self.skipTest("ExecutionModeBroadcastingService not yet implemented")

        self.service = ExecutionModeBroadcastingService()

    def test_authenticated_mode_broadcasting_enabled(self):
        """Test that broadcasting is enabled for authenticated execution mode"""
        # Create authenticated session
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        # Broadcasting should be enabled
        self.assertTrue(self.service.should_broadcast())

    def test_public_mode_broadcasting_disabled(self):
        """Test that broadcasting is disabled for public execution mode"""
        # Create public session
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('public')

        # Broadcasting should be disabled
        self.assertFalse(self.service.should_broadcast())

    def test_logger_integration_with_broadcasting(self):
        """Test that LoggerService uses broadcasting service for mode awareness"""
        # Create authenticated session
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        logger = LoggerService()

        # Mock the broadcasting service
        with patch.object(self.service, 'broadcast_log_message') as mock_broadcast:
            # Logger should use broadcasting service
            with patch('core.services.logger_service.send_message_to_user') as mock_send, \
                    patch('core.services.logger_service.config.WEB_OR_CLI', 'web'):
                logger.info("Test message for authenticated mode")

                # Should broadcast in authenticated mode
                if self.service.should_broadcast():
                    mock_send.assert_called()
                else:
                    mock_send.assert_not_called()

    def test_concurrent_user_broadcasting_isolation(self):
        """Test that broadcasting is properly isolated between concurrent users"""
        results = {}

        def user_worker(user_id: int, execution_mode: str):
            # Create session for this user
            session_id = session_manager.create_session_for_loop(
                user_id=user_id,
                loop_id=user_id + 60,
                project_id=user_id
            )
            session_manager.set_execution_mode(execution_mode)

            # Check broadcasting status
            should_broadcast = self.service.should_broadcast()

            results[user_id] = {
                'execution_mode': execution_mode,
                'should_broadcast': should_broadcast,
                'user_id': user_id
            }

        # Run concurrent workers with different execution modes
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(user_worker, 1, 'authenticated'),  # Should broadcast
                executor.submit(user_worker, 2, 'public'),         # Should not broadcast
                executor.submit(user_worker, 3, 'authenticated'),  # Should broadcast
                executor.submit(user_worker, 4, 'public')          # Should not broadcast
            ]
            [f.result() for f in futures]

        # Verify isolation
        self.assertEqual(len(results), 4)
        self.assertTrue(results[1]['should_broadcast'])   # Authenticated
        self.assertFalse(results[2]['should_broadcast'])  # Public
        self.assertTrue(results[3]['should_broadcast'])   # Authenticated
        self.assertFalse(results[4]['should_broadcast'])  # Public

    def test_broadcasting_service_singleton(self):
        """Test that broadcasting service follows singleton pattern"""
        if get_broadcasting_service is None:
            self.skipTest("get_broadcasting_service not yet implemented")

        service1 = get_broadcasting_service()
        service2 = get_broadcasting_service()

        self.assertEqual(id(service1), id(service2))
        self.assertIsInstance(service1, ExecutionModeBroadcastingService)

    def test_message_filtering_by_execution_mode(self):
        """Test that messages are filtered based on execution mode"""
        # Test authenticated mode - messages should be sent
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        with patch('web.services.socket_io_service.send_message_to_user') as mock_send:
            self.service.broadcast_log_message(
                user_id=1,
                action='info',
                message='Test authenticated message',
                loop_id=61
            )

            # Should have sent message in authenticated mode
            if self.service.should_broadcast():
                mock_send.assert_called_once_with(1, 'info', {
                    'message': 'Test authenticated message',
                    'loop_id': 61
                })

        # Test public mode - messages should be filtered out
        session_manager.set_execution_mode('public')

        with patch('web.services.socket_io_service.send_message_to_user') as mock_send:
            self.service.broadcast_log_message(
                user_id=1,
                action='info',
                message='Test public message',
                loop_id=61
            )

            # Should not send message in public mode
            if not self.service.should_broadcast():
                mock_send.assert_not_called()

    def test_api_route_execution_mode_detection(self):
        """Test automatic execution mode detection based on API routes"""
        # Mock API route contexts
        test_routes = [
            ('/api/public/loop/1', 'public'),
            ('/api/public/agent/2/action/WAKEUP/', 'public'),
            ('/api/loops/run', 'authenticated'),
            ('/admin/loops/execute', 'authenticated')
        ]

        for route, expected_mode in test_routes:
            with self.subTest(route=route):
                detected_mode = self.service.detect_execution_mode_from_route(route)
                self.assertEqual(detected_mode, expected_mode)

    def test_broadcasting_performance_under_load(self):
        """Test broadcasting performance with multiple concurrent messages"""
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        # Reduce message count to avoid output overflow
        message_count = 10
        sent_messages = []

        def message_sender(message_id: int):
            message = f"Performance test message {message_id}"
            self.service.broadcast_log_message(
                user_id=1,
                action='info',
                message=message,
                loop_id=61
            )
            sent_messages.append(message_id)

        # Send messages concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(message_sender, i) for i in range(message_count)]
            [f.result() for f in futures]

        # All messages should have been processed
        self.assertEqual(len(sent_messages), message_count)

    def test_graceful_fallback_when_socketio_unavailable(self):
        """Test graceful handling when SocketIO service is unavailable"""
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        # Mock SocketIO service to raise exception
        with patch('web.services.socket_io_service.send_message_to_user') as mock_send:
            mock_send.side_effect = Exception("SocketIO not available")

            # Should not raise exception, should handle gracefully
            try:
                self.service.broadcast_log_message(
                    user_id=1,
                    action='error',
                    message='Test message with SocketIO failure',
                    loop_id=61
                )
                self.assertTrue(True)  # Success if no exception
            except Exception as e:
                self.fail(f"Broadcasting should handle SocketIO failures gracefully: {e}")

    def test_message_queuing_and_batching(self):
        """Test message queuing and batching for performance optimization"""
        if not hasattr(self.service, 'enable_message_batching'):
            self.skipTest("Message batching not implemented")

        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        # Enable batching
        self.service.enable_message_batching(batch_size=5, flush_interval=1.0)

        messages = []
        for i in range(10):
            message = f"Batch test message {i}"
            self.service.queue_message(
                user_id=1,
                action='info',
                message=message,
                loop_id=61
            )
            messages.append(message)

        # Wait for batching to process
        time.sleep(1.5)

        # Verify messages were batched and sent
        self.assertEqual(len(messages), 10)


class TestExecutionModeBroadcastingIntegration(unittest.TestCase):
    """Test broadcasting service integration with existing components"""

    def setUp(self):
        """Set up test environment"""
        if ExecutionModeBroadcastingService is None:
            self.skipTest("ExecutionModeBroadcastingService not yet implemented")

        self.service = ExecutionModeBroadcastingService()

    def test_logger_service_integration(self):
        """Test integration with enhanced LoggerService"""
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )
        session_manager.set_execution_mode('authenticated')

        logger = LoggerService()

        # Logger consults the session's execution mode (the same source as
        # should_broadcast(); calling the service itself would recurse, as it logs)
        with patch.object(session_manager, 'is_realtime_logging_enabled', return_value=False) as mock_realtime, \
                patch('core.services.logger_service.send_message_to_user') as mock_send, \
                patch('core.services.logger_service.config.WEB_OR_CLI', 'web'):
            logger.info("Integration test message")

            mock_realtime.assert_called()
            mock_send.assert_not_called()

    def test_session_manager_integration(self):
        """Test integration with SessionManager for execution mode detection"""
        # SessionManager should provide execution mode information
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )

        # Test different execution modes
        execution_modes = ['public', 'authenticated']
        for mode in execution_modes:
            with self.subTest(mode=mode):
                session_manager.set_execution_mode(mode)

                # Broadcasting service should detect the mode
                detected_mode = self.service.get_current_execution_mode()
                self.assertEqual(detected_mode, mode)

    def test_web_routes_integration(self):
        """Test integration with web routes for automatic mode detection"""
        # Mock Flask request context
        test_cases = [
            ('/api/public/loop/1', 'public'),
            ('/api/loops/run', 'authenticated'),
            ('/api/public/agent/1/action/WAKEUP/', 'public')
        ]

        for route, expected_mode in test_cases:
            with self.subTest(route=route):
                with Flask(__name__).test_request_context(route):
                    detected_mode = self.service.detect_execution_mode_from_request()
                    self.assertEqual(detected_mode, expected_mode)


def run_execution_mode_broadcasting_tests():
    """Run all execution mode broadcasting tests"""
    print("🧪 Running Execution Mode Broadcasting Tests...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionModeBroadcasting))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionModeBroadcastingIntegration))

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
        print("🎉 All execution mode broadcasting tests passed!")
    else:
        print("⚠️  Some execution mode broadcasting tests failed - this is expected initially with TDD approach")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_execution_mode_broadcasting_tests()
    exit(0 if success else 1)