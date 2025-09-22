# core/tests/unit/test_concurrent_logging.py
import unittest
import asyncio
import threading
from unittest.mock import Mock, patch, call
import time

from core.services.logger_service import LoggerService
from core.services.thread_safe_session import thread_safe_session_manager
from web.services.concurrent_web_loop_runner import ConcurrentWebLoopRunner


class TestConcurrentLogging(unittest.TestCase):
    """Test that logging works correctly during concurrent loop execution"""

    def setUp(self):
        """Set up test environment"""
        self.mock_app = Mock()
        self.user_id = 1
        self.loop_id = 50

        # Clean up any existing sessions
        thread_safe_session_manager._global_sessions.clear()

    def tearDown(self):
        """Clean up after tests"""
        thread_safe_session_manager._global_sessions.clear()

    @patch('core.services.logger_service.send_message_to_user')
    def test_logger_sends_messages_during_concurrent_execution(self, mock_send_message):
        """
        Test that logger.log() calls send_message_to_user() with correct parameters
        during concurrent loop execution.

        This test verifies:
        1. Logger has correct user_id and loop_id from session
        2. send_message_to_user is called with proper parameters
        3. Messages include loop_id for frontend routing
        """
        # Arrange: Create isolated session for concurrent execution
        session_id = thread_safe_session_manager.create_session_for_loop(
            user_id=self.user_id,
            loop_id=self.loop_id,
            project_id=1
        )

        # Act: Create logger and log a message (simulating loop execution)
        logger = LoggerService(user_id=self.user_id)
        test_message = "Test log message during loop execution"
        logger.info(test_message)

        # Assert: Verify send_message_to_user was called correctly
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args

        # Check parameters passed to send_message_to_user
        self.assertEqual(call_args[0][0], self.user_id)  # user_id
        self.assertEqual(call_args[0][1], 'info')        # action

        # Check message data
        message_data = call_args[0][2]
        self.assertIn('message', message_data)
        self.assertIn('loop_id', message_data)
        self.assertEqual(message_data['loop_id'], self.loop_id)
        self.assertIn(test_message, message_data['message'])

    @patch('core.services.logger_service.send_message_to_user')
    def test_concurrent_loops_dont_interfere(self, mock_send_message):
        """
        Test that two concurrent loops send logs to their respective users
        without interference.

        This test verifies loop isolation:
        1. Loop A logs go to user A with loop_id A
        2. Loop B logs go to user B with loop_id B
        3. No cross-contamination of messages
        """
        # Arrange: Create two separate sessions for different users/loops
        user_a, loop_a = 1, 50
        user_b, loop_b = 2, 60

        session_a = thread_safe_session_manager.create_session_for_loop(
            user_id=user_a, loop_id=loop_a, project_id=1
        )

        def run_loop_a():
            """Simulate loop A execution in separate thread"""
            # Create session for user A in this thread (threads don't inherit thread-local data)
            thread_safe_session_manager.create_session_for_loop(
                user_id=user_a, loop_id=loop_a, project_id=1
            )
            # Create logger for user A
            logger_a = LoggerService(user_id=user_a)
            logger_a.info("Loop A message 1")
            time.sleep(0.1)  # Simulate some processing
            logger_a.info("Loop A message 2")

        def run_loop_b():
            """Simulate loop B execution in separate thread"""
            # Create new session for user B in this thread
            thread_safe_session_manager.create_session_for_loop(
                user_id=user_b, loop_id=loop_b, project_id=2
            )
            logger_b = LoggerService(user_id=user_b)
            logger_b.info("Loop B message 1")
            time.sleep(0.1)  # Simulate some processing
            logger_b.info("Loop B message 2")

        # Act: Run both loops concurrently
        thread_a = threading.Thread(target=run_loop_a, daemon=True)
        thread_b = threading.Thread(target=run_loop_b, daemon=True)

        thread_a.start()
        thread_b.start()

        thread_a.join(timeout=2)
        thread_b.join(timeout=2)

        # Assert: Verify correct message routing
        self.assertEqual(mock_send_message.call_count, 4)  # 2 messages per loop

        calls = mock_send_message.call_args_list

        # Verify user A messages
        user_a_calls = [call for call in calls if call[0][0] == user_a]
        user_b_calls = [call for call in calls if call[0][0] == user_b]

        self.assertEqual(len(user_a_calls), 2)
        self.assertEqual(len(user_b_calls), 2)

        # Verify loop_id isolation
        for call in user_a_calls:
            self.assertEqual(call[0][2]['loop_id'], loop_a)
            self.assertIn("Loop A", call[0][2]['message'])

        for call in user_b_calls:
            self.assertEqual(call[0][2]['loop_id'], loop_b)
            self.assertIn("Loop B", call[0][2]['message'])

    @patch('core.services.logger_service.send_message_to_user')
    def test_logger_handles_missing_session_gracefully(self, mock_send_message):
        """
        Test that logger handles cases where session context is missing
        (e.g., when not in concurrent execution mode).
        """
        # Arrange: No session context set up

        # Act: Create logger without session context
        logger = LoggerService(user_id=self.user_id)
        logger.info("Message without session context")

        # Assert: Logger should handle gracefully
        # Either send with None loop_id or skip sending - both acceptable
        if mock_send_message.called:
            call_args = mock_send_message.call_args
            message_data = call_args[0][2]
            # loop_id might be None or missing - that's acceptable
            self.assertIn('message', message_data)


if __name__ == '__main__':
    unittest.main()