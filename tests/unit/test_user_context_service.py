#!/usr/bin/env python3
"""
UserContextService Unit Tests

Tests the UserContextService that provides:
1. User-aware HTTP client management with session isolation
2. Request context propagation for multi-user scenarios
3. Integration with SessionManager for user/loop context
4. Resource cleanup and connection pooling per user

Following TDD approach: These tests define the expected behavior
and will initially fail until the UserContextService is created.
"""

import unittest
import threading
import time
from unittest.mock import patch, MagicMock, Mock
from concurrent.futures import ThreadPoolExecutor

# Import the service we'll be creating
# This will initially fail until we create the service
try:
    from core.services.user_context_service import UserContextService, get_user_context_service
except ImportError:
    UserContextService = None
    get_user_context_service = None

from core.services.session_manager import SessionManager


class TestUserContextService(unittest.TestCase):
    """Test UserContextService for user-aware HTTP requests"""

    def setUp(self):
        """Set up test environment"""
        if UserContextService is None:
            self.skipTest("UserContextService not yet implemented")

        self.service = UserContextService()
        self.session_manager = SessionManager()

    def test_user_isolated_http_client(self):
        """Test that each user gets an isolated HTTP client"""
        # Create sessions for different users
        session_1 = self.session_manager.create_session_for_loop(user_id=1, loop_id=61, project_id=1)
        session_2 = self.session_manager.create_session_for_loop(user_id=2, loop_id=62, project_id=2)

        # Get HTTP clients for different users
        client_1 = self.service.get_http_client(user_id=1)
        client_2 = self.service.get_http_client(user_id=2)

        # Clients should be different instances
        self.assertIsNotNone(client_1)
        self.assertIsNotNone(client_2)
        self.assertNotEqual(id(client_1), id(client_2))

        # Same user should get the same client instance (connection pooling)
        client_1_again = self.service.get_http_client(user_id=1)
        self.assertEqual(id(client_1), id(client_1_again))

    def test_concurrent_http_requests(self):
        """Test concurrent HTTP requests from different users don't interfere"""
        results = {}

        def make_request(user_id: int, loop_id: int):
            # Create session for this user/loop
            self.session_manager.create_session_for_loop(
                user_id=user_id,
                loop_id=loop_id,
                project_id=user_id
            )

            # Get user-specific HTTP client
            client = self.service.get_http_client(user_id=user_id)

            # Mock HTTP request
            with patch.object(client, 'request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'user_id': user_id, 'loop_id': loop_id}
                mock_request.return_value = mock_response

                # Make request with user context
                response = self.service.make_request(
                    method='GET',
                    url='http://example.com/api',
                    user_id=user_id,
                    headers={'User-Agent': f'LoopAI-User-{user_id}'}
                )

                results[user_id] = {
                    'client_id': id(client),
                    'response_data': response.json(),
                    'user_id': user_id
                }

        # Run concurrent requests for different users
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_request, user_id, user_id + 60)
                for user_id in range(1, 4)
            ]
            [f.result() for f in futures]

        # Verify isolation
        self.assertEqual(len(results), 3)
        for user_id in range(1, 4):
            result = results[user_id]
            self.assertEqual(result['user_id'], user_id)
            self.assertEqual(result['response_data']['user_id'], user_id)

        # Verify different client instances
        client_ids = [results[i]['client_id'] for i in range(1, 4)]
        self.assertEqual(len(set(client_ids)), 3, "Each user should have different client")

    def test_request_context_propagation(self):
        """Test that request context (headers, timeouts) is properly propagated"""
        user_id = 1
        self.session_manager.create_session_for_loop(
            user_id=user_id,
            loop_id=61,
            project_id=1
        )

        # Set user-specific context
        self.service.set_user_context(user_id=user_id, context={
            'default_headers': {
                'Authorization': 'Bearer user1-token',
                'Content-Type': 'application/json'
            },
            'timeout': 30,
            'max_retries': 3
        })

        # Get client and verify context is applied
        client = self.service.get_http_client(user_id=user_id)
        context = self.service.get_user_context(user_id=user_id)

        self.assertIsNotNone(context)
        self.assertEqual(context['timeout'], 30)
        self.assertEqual(context['max_retries'], 3)
        self.assertIn('Authorization', context['default_headers'])

    def test_session_integration(self):
        """Test integration with SessionManager for automatic context detection"""
        from core.services.session_manager import session_manager

        # Create session using the same session manager instance
        session_id = session_manager.create_session_for_loop(
            user_id=1,
            loop_id=61,
            project_id=1
        )

        # Service should automatically detect user context from session
        client = self.service.get_current_user_http_client()
        self.assertIsNotNone(client)

        # Verify it's the same client as user-specific request
        user_client = self.service.get_http_client(user_id=1)
        self.assertEqual(id(client), id(user_client))

    def test_resource_cleanup(self):
        """Test that HTTP client resources are properly cleaned up"""
        user_id = 1

        # Create client
        client = self.service.get_http_client(user_id=user_id)
        self.assertIsNotNone(client)

        # Verify client exists in service registry
        self.assertTrue(self.service.has_user_client(user_id=user_id))

        # Clean up resources
        self.service.cleanup_user_resources(user_id=user_id)

        # Verify client is removed
        self.assertFalse(self.service.has_user_client(user_id=user_id))

        # New client should be a different instance
        new_client = self.service.get_http_client(user_id=user_id)
        self.assertNotEqual(id(client), id(new_client))

    def test_error_handling(self):
        """Test error handling for invalid user contexts"""
        # Test with invalid user ID
        with self.assertRaises(ValueError):
            self.service.get_http_client(user_id=None)

        with self.assertRaises(ValueError):
            self.service.get_http_client(user_id=-1)

        # Test making request without session context (session_manager is a
        # process-wide singleton, so earlier tests may have left a user in it)
        with patch.object(self.service._session_manager, 'get_user_id', return_value=None):
            with self.assertRaises(RuntimeError):
                self.service.get_current_user_http_client()

    def test_singleton_pattern(self):
        """Test that service follows singleton pattern"""
        if get_user_context_service is None:
            self.skipTest("get_user_context_service not yet implemented")

        service1 = get_user_context_service()
        service2 = get_user_context_service()

        self.assertEqual(id(service1), id(service2))
        self.assertIsInstance(service1, UserContextService)


class TestUserContextServiceIntegration(unittest.TestCase):
    """Test UserContextService integration with existing adapters"""

    def setUp(self):
        """Set up test environment"""
        if UserContextService is None:
            self.skipTest("UserContextService not yet implemented")

        self.service = UserContextService()
        self.session_manager = SessionManager()

    def test_request_adapter_integration(self):
        """Test integration with RequestAdapter for user-aware HTTP requests"""
        from core.services.session_manager import session_manager

        # This test would verify that RequestAdapter uses UserContextService
        # for making HTTP requests in a user-aware manner

        user_id = 1
        session_id = session_manager.create_session_for_loop(
            user_id=user_id,
            loop_id=61,
            project_id=1
        )

        # Set request data in session (simulating RequestAdapter behavior)
        request_data = {
            'method': 'POST',
            'url': 'http://example.com/api',
            'headers': {'Content-Type': 'application/json'},
            'data': {'test': 'data'}
        }
        session_manager.set_request_data(request_data)

        # Service should be able to make request using session data
        with patch.object(self.service, 'make_request') as mock_make_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_make_request.return_value = mock_response

            # This would be called by RequestAdapter
            response = self.service.make_request_from_session()

            self.assertEqual(response.status_code, 200)
            mock_make_request.assert_called_once()

    def test_adapter_delegation_pattern(self):
        """Test that adapters delegate to UserContextService instead of implementing user logic"""
        from core.services.session_manager import session_manager

        # This test would verify that adapters use the service
        # rather than implementing their own user-aware logic

        user_id = 1
        session_manager.create_session_for_loop(
            user_id=user_id,
            loop_id=61,
            project_id=1
        )

        # Verify service provides the interface adapters need
        client = self.service.get_current_user_http_client()
        self.assertIsNotNone(client)

        # Verify service can handle adapter-style requests
        with patch.object(self.service, 'make_request') as mock_make_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_make_request.return_value = mock_response

            # Simulate adapter making request through service
            response = self.service.make_request(
                method='GET',
                url='http://example.com',
                user_id=user_id
            )

            self.assertEqual(response.status_code, 200)


def run_user_context_service_tests():
    """Run all UserContextService tests"""
    print("🧪 Running UserContextService Tests...")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestUserContextService))
    suite.addTests(loader.loadTestsFromTestCase(TestUserContextServiceIntegration))

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
        print("🎉 All UserContextService tests passed!")
    else:
        print("⚠️  Some UserContextService tests failed - this is expected initially with TDD approach")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_user_context_service_tests()
    exit(0 if success else 1)