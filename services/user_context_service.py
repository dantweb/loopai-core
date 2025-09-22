#!/usr/bin/env python3
"""
UserContextService

Provides user-aware HTTP client management and request context propagation
for multi-user scenarios. This service ensures that HTTP requests made by
different users are properly isolated and contextualized.

Key Features:
- User-isolated HTTP client instances with connection pooling
- Request context propagation (headers, timeouts, retries)
- Integration with SessionManager for automatic context detection
- Resource cleanup and lifecycle management
- Thread-safe operations for concurrent user requests

Usage:
    service = get_user_context_service()
    client = service.get_http_client(user_id=1)
    response = service.make_request('GET', 'http://api.example.com', user_id=1)
"""

import threading
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.services.session import session_manager
from core.services.logger_service import LoggerService


class UserContextService:
    """
    Service providing user-aware HTTP client management with session isolation.

    This service maintains separate HTTP client instances for each user to ensure
    proper isolation and context propagation in multi-user scenarios.
    """

    def __init__(self):
        self.logger = LoggerService()
        self._lock = threading.RLock()
        self._user_clients: Dict[int, requests.Session] = {}
        self._user_contexts: Dict[int, Dict[str, Any]] = {}
        # Use the global singleton session manager
        self._session_manager = session_manager

    def get_http_client(self, user_id: int) -> requests.Session:
        """
        Get or create an HTTP client for a specific user.

        Args:
            user_id: User ID for client isolation

        Returns:
            requests.Session: User-specific HTTP client

        Raises:
            ValueError: If user_id is invalid
        """
        if user_id is None or user_id < 1:
            raise ValueError(f"Invalid user_id: {user_id}")

        with self._lock:
            if user_id not in self._user_clients:
                self._user_clients[user_id] = self._create_user_client(user_id)
                self.logger.info(f"[UserContextService] Created HTTP client for user {user_id}")

            return self._user_clients[user_id]

    def _create_user_client(self, user_id: int) -> requests.Session:
        """
        Create a new HTTP client configured for a specific user.

        Args:
            user_id: User ID for client configuration

        Returns:
            requests.Session: Configured HTTP client
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Add retry adapter
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Apply user-specific context if available
        context = self._user_contexts.get(user_id, {})
        if context:
            # Set default headers
            default_headers = context.get('default_headers', {})
            session.headers.update(default_headers)

            # Set timeout if specified
            timeout = context.get('timeout')
            if timeout:
                session.request = self._wrap_with_timeout(session.request, timeout)

        # Add user identification
        session.headers.update({
            'User-Agent': f'LoopAI-User-{user_id}',
            'X-LoopAI-User-ID': str(user_id)
        })

        return session

    def _wrap_with_timeout(self, original_request, timeout):
        """Wrap request method with default timeout"""
        def request_with_timeout(*args, **kwargs):
            if 'timeout' not in kwargs:
                kwargs['timeout'] = timeout
            return original_request(*args, **kwargs)
        return request_with_timeout

    def get_current_user_http_client(self) -> requests.Session:
        """
        Get HTTP client for the current user based on session context.

        Returns:
            requests.Session: HTTP client for current user

        Raises:
            RuntimeError: If no user context is available in session
        """
        user_id = self._session_manager.get_user_id()
        if user_id is None:
            raise RuntimeError("No user context available in current session")

        return self.get_http_client(user_id)

    def set_user_context(self, user_id: int, context: Dict[str, Any]):
        """
        Set context configuration for a specific user.

        Args:
            user_id: User ID
            context: Context configuration dictionary
                    - default_headers: Dict of default HTTP headers
                    - timeout: Default request timeout in seconds
                    - max_retries: Maximum number of request retries
        """
        with self._lock:
            self._user_contexts[user_id] = context.copy()
            self.logger.info(f"[UserContextService] Set context for user {user_id}: {list(context.keys())}")

            # If client already exists, update it with new context
            if user_id in self._user_clients:
                self._update_client_context(user_id, context)

    def _update_client_context(self, user_id: int, context: Dict[str, Any]):
        """Update existing client with new context"""
        client = self._user_clients[user_id]

        # Update headers
        default_headers = context.get('default_headers', {})
        client.headers.update(default_headers)

        # Note: Timeout and retry updates would require recreating the client
        # For now, we log that a restart may be needed for full context update
        if 'timeout' in context or 'max_retries' in context:
            self.logger.info(f"[UserContextService] Context update for user {user_id} may require client recreation")

    def get_user_context(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get context configuration for a specific user.

        Args:
            user_id: User ID

        Returns:
            Dict or None: User context configuration
        """
        with self._lock:
            return self._user_contexts.get(user_id)

    def make_request(self, method: str, url: str, user_id: int, **kwargs) -> requests.Response:
        """
        Make an HTTP request using user-specific client.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            user_id: User ID for client selection
            **kwargs: Additional request parameters

        Returns:
            requests.Response: HTTP response
        """
        client = self.get_http_client(user_id)

        self.logger.info(f"[UserContextService] Making {method} request to {url} for user {user_id}")

        try:
            response = client.request(method, url, **kwargs)
            self.logger.info(f"[UserContextService] Request completed with status {response.status_code}")
            return response
        except Exception as e:
            self.logger.error(f"[UserContextService] Request failed for user {user_id}: {str(e)}")
            raise

    def make_request_from_session(self) -> requests.Response:
        """
        Make HTTP request using data stored in current session.

        This method is designed for integration with RequestAdapter.

        Returns:
            requests.Response: HTTP response

        Raises:
            RuntimeError: If no request data is available in session
        """
        request_data = self._session_manager.get_request_data()
        if not request_data:
            raise RuntimeError("No request data available in current session")

        user_id = self._session_manager.get_user_id()
        if user_id is None:
            raise RuntimeError("No user context available in current session")

        # Extract request parameters
        method = request_data.get('method', 'GET')
        url = request_data.get('url')
        if not url:
            raise RuntimeError("No URL specified in session request data")

        # Prepare request arguments
        kwargs = {}
        if 'headers' in request_data:
            kwargs['headers'] = request_data['headers']
        if 'data' in request_data:
            kwargs['data'] = request_data['data']
        if 'json' in request_data:
            kwargs['json'] = request_data['json']
        if 'params' in request_data:
            kwargs['params'] = request_data['params']

        return self.make_request(method, url, user_id, **kwargs)

    def has_user_client(self, user_id: int) -> bool:
        """
        Check if a user has an active HTTP client.

        Args:
            user_id: User ID to check

        Returns:
            bool: True if user has active client
        """
        with self._lock:
            return user_id in self._user_clients

    def cleanup_user_resources(self, user_id: int):
        """
        Clean up HTTP client resources for a specific user.

        Args:
            user_id: User ID for resource cleanup
        """
        with self._lock:
            # Close and remove HTTP client
            if user_id in self._user_clients:
                client = self._user_clients[user_id]
                try:
                    client.close()
                except Exception as e:
                    self.logger.error(f"[UserContextService] Error closing client for user {user_id}: {e}")

                del self._user_clients[user_id]
                self.logger.info(f"[UserContextService] Cleaned up HTTP client for user {user_id}")

            # Remove user context
            if user_id in self._user_contexts:
                del self._user_contexts[user_id]
                self.logger.info(f"[UserContextService] Cleaned up context for user {user_id}")

    def cleanup_all_resources(self):
        """Clean up all user resources"""
        with self._lock:
            user_ids = list(self._user_clients.keys())
            for user_id in user_ids:
                self.cleanup_user_resources(user_id)

            self.logger.info("[UserContextService] Cleaned up all user resources")

    def get_active_users(self) -> list:
        """Get list of users with active HTTP clients"""
        with self._lock:
            return list(self._user_clients.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self._lock:
            return {
                'active_users': len(self._user_clients),
                'user_ids': list(self._user_clients.keys()),
                'contexts_configured': len(self._user_contexts)
            }


# Singleton instance
_user_context_service = None
_service_lock = threading.Lock()


def get_user_context_service() -> UserContextService:
    """
    Get singleton instance of UserContextService.

    Returns:
        UserContextService: Singleton service instance
    """
    global _user_context_service

    if _user_context_service is None:
        with _service_lock:
            if _user_context_service is None:
                _user_context_service = UserContextService()
                logger = LoggerService()
                logger.info("[UserContextService] Singleton instance created")

    return _user_context_service