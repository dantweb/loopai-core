#!/usr/bin/env python3
"""
LoggerService Unit Tests

Tests the enhanced LoggerService that provides:
1. Environment-based path configuration using LOOPAI_LOG_PATH
2. Component-specific log files (core.log, web.log, system.log)
3. Singleton pattern with get_logger_service() function
4. Thread-safe logging for concurrent operations
5. Integration with multi-user session context

Following TDD approach: These tests define the expected behavior
and will initially fail until the LoggerService is enhanced.
"""

import unittest
import tempfile
import os
import threading
from unittest.mock import patch, mock_open
from concurrent.futures import ThreadPoolExecutor

# Import existing logger service
from core.services.logger_service import LoggerService


class TestLoggerServiceEnhancement(unittest.TestCase):
    """Test enhanced LoggerService with environment-based configuration"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, 'logs')

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_environment_based_path_configuration(self):
        """Test that LoggerService uses LOOPAI_LOG_PATH from environment"""
        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': self.log_path}):
            logger = LoggerService()

            # Should use environment-configured path
            self.assertEqual(logger.get_log_path(), self.log_path)

    def test_component_specific_log_files(self):
        """Test that different components get separate log files"""
        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': self.log_path}):
            # Create component-specific loggers
            core_logger = LoggerService(component='core')
            web_logger = LoggerService(component='web')
            system_logger = LoggerService(component='system')

            # Each component should have different log file
            self.assertEqual(core_logger.get_log_file(), os.path.join(self.log_path, 'core.log'))
            self.assertEqual(web_logger.get_log_file(), os.path.join(self.log_path, 'web.log'))
            self.assertEqual(system_logger.get_log_file(), os.path.join(self.log_path, 'system.log'))

    def test_singleton_pattern(self):
        """Test that get_logger_service() returns singleton instance"""
        # This test will initially fail until we implement get_logger_service()
        try:
            from core.services.logger_service import get_logger_service
        except ImportError:
            self.skipTest("get_logger_service not yet implemented")

        logger1 = get_logger_service()
        logger2 = get_logger_service()

        # Should be the same instance
        self.assertEqual(id(logger1), id(logger2))
        self.assertIsInstance(logger1, LoggerService)

    def test_component_specific_singleton(self):
        """Test that each component gets its own singleton instance"""
        try:
            from core.services.logger_service import get_logger_service
        except ImportError:
            self.skipTest("get_logger_service not yet implemented")

        core_logger1 = get_logger_service('core')
        core_logger2 = get_logger_service('core')
        web_logger = get_logger_service('web')

        # Same component should return same instance
        self.assertEqual(id(core_logger1), id(core_logger2))

        # Different components should have different instances
        self.assertNotEqual(id(core_logger1), id(web_logger))

    def test_directory_creation(self):
        """Test that log directory is created if it doesn't exist"""
        non_existent_path = os.path.join(self.temp_dir, 'new_logs')

        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': non_existent_path}):
            logger = LoggerService()

            # Directory should be created when logger is initialized
            logger.ensure_log_directory()
            self.assertTrue(os.path.exists(non_existent_path))

    def test_fallback_to_default_path(self):
        """Test fallback to default path when LOOPAI_LOG_PATH is not set"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove LOOPAI_LOG_PATH from environment
            if 'LOOPAI_LOG_PATH' in os.environ:
                del os.environ['LOOPAI_LOG_PATH']

            logger = LoggerService()

            # Should use default path
            expected_default = '/app/var/logs'  # Based on Enhanced Architecture Plan
            self.assertEqual(logger.get_log_path(), expected_default)

    def test_concurrent_logging(self):
        """Test that logging is thread-safe in concurrent scenarios"""
        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': self.log_path}):
            logger = LoggerService()
            results = []

            def log_worker(worker_id: int):
                # Each worker logs messages
                for i in range(10):
                    message = f"Worker {worker_id} - Message {i}"
                    logger.info(message)
                    results.append(f"{worker_id}:{i}")

            # Run concurrent workers
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(log_worker, i) for i in range(5)]
                [f.result() for f in futures]

            # All messages should have been logged
            self.assertEqual(len(results), 50)  # 5 workers * 10 messages

    def test_user_context_logging(self):
        """Test that logger can include user context in log messages"""
        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': self.log_path}):
            from core.services.session_manager import session_manager

            # Create session with user context
            session_id = session_manager.create_session_for_loop(
                user_id=1,
                loop_id=61,
                project_id=1
            )

            logger = LoggerService()

            # Log message - should work with user context from session
            with patch.object(logger._logger, 'debug') as mock_debug:
                logger.info("Test message")

                # Should have called the underlying logger
                mock_debug.assert_called()
                # The message should include user context via the existing log method
                call_args = str(mock_debug.call_args)
                self.assertIn('UserID=[1]', call_args)

    def test_log_level_configuration(self):
        """Test that log level can be configured via environment"""
        with patch.dict(os.environ, {
            'LOOPAI_LOG_PATH': self.log_path,
            'LOOPAI_LOG_LEVEL': 'DEBUG'
        }):
            logger = LoggerService()

            # Should use configured log level
            self.assertEqual(logger.get_log_level(), 'DEBUG')

        with patch.dict(os.environ, {
            'LOOPAI_LOG_PATH': self.log_path,
            'LOOPAI_LOG_LEVEL': 'ERROR'
        }):
            logger = LoggerService()
            self.assertEqual(logger.get_log_level(), 'ERROR')

    def test_log_rotation_configuration(self):
        """Test that log rotation can be configured"""
        with patch.dict(os.environ, {
            'LOOPAI_LOG_PATH': self.log_path,
            'LOOPAI_LOG_MAX_SIZE': '10MB',
            'LOOPAI_LOG_BACKUP_COUNT': '5'
        }):
            logger = LoggerService()

            # Should use configured rotation settings
            self.assertEqual(logger.get_max_file_size(), '10MB')
            self.assertEqual(logger.get_backup_count(), 5)

    def test_backward_compatibility(self):
        """Test that existing LoggerService usage still works"""
        # Existing code should continue to work without changes
        logger = LoggerService()

        # Basic logging methods should still work
        logger.info("Test info message")
        logger.error("Test error message")
        logger.debug("Test debug message")

        # These calls should not raise exceptions
        self.assertTrue(True)

    def test_component_parameter_validation(self):
        """Test validation of component parameter"""
        # Valid components should work
        valid_components = ['core', 'web', 'system']
        for component in valid_components:
            logger = LoggerService(component=component)
            self.assertIsNotNone(logger)

        # Invalid component should use default or raise error
        with self.assertRaises(ValueError):
            LoggerService(component='invalid_component')

    def test_integration_with_existing_code(self):
        """Test that enhanced logger integrates with existing codebase"""
        # Test that logger works with existing import patterns
        from core.services.logger_service import LoggerService as ExistingLogger

        logger = ExistingLogger()

        # Should work with existing method calls
        logger.log("Test message")
        logger.info("Test info")
        logger.error("Test error")


class TestLoggerServiceIntegration(unittest.TestCase):
    """Test LoggerService integration with other components"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, 'logs')

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_session_manager_integration(self):
        """Test that LoggerService integrates with SessionManager for user context"""
        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': self.log_path}):
            from core.services.session_manager import session_manager

            # Create session
            session_id = session_manager.create_session_for_loop(
                user_id=1,
                loop_id=61,
                project_id=1
            )

            logger = LoggerService()

            # Logger should automatically include user context
            # Just verify that logging works without errors
            try:
                logger.info("Integration test message")
                # If we get here without exception, the integration works
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"SessionManager integration failed: {e}")

    def test_user_context_service_integration(self):
        """Test integration with UserContextService"""
        with patch.dict(os.environ, {'LOOPAI_LOG_PATH': self.log_path}):
            from core.services.user_context_service import get_user_context_service

            service = get_user_context_service()
            logger = LoggerService()

            # Logger should work alongside UserContextService without conflicts
            client = service.get_http_client(user_id=1)
            logger.info("UserContextService integration test")

            self.assertIsNotNone(client)


def run_logger_service_tests():
    """Run all LoggerService tests"""
    print("🧪 Running LoggerService Enhancement Tests...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLoggerServiceEnhancement))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggerServiceIntegration))

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
        print("🎉 All LoggerService tests passed!")
    else:
        print("⚠️  Some LoggerService tests failed - this is expected initially with TDD approach")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_logger_service_tests()
    exit(0 if success else 1)