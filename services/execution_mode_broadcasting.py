#!/usr/bin/env python3
"""
Execution Mode-Aware Broadcasting Service

Provides execution mode-aware broadcasting that filters real-time log messages
based on the execution context:

- **Authenticated Mode** (Frontend users): Enable real-time broadcasting
- **Public Mode** (API endpoints): Disable broadcasting for performance

Key Features:
- Automatic execution mode detection from SessionManager
- Route-based execution mode inference
- Thread-safe broadcasting for concurrent users
- Graceful fallback when SocketIO is unavailable
- Integration with LoggerService and SessionManager
- Performance optimization through message filtering

Usage:
    service = get_broadcasting_service()
    if service.should_broadcast():
        service.broadcast_log_message(user_id, 'info', 'Message', loop_id)
"""

import threading
import re
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from core.services.session import session_manager
from core.services.logger_service import LoggerService


class ExecutionModeBroadcastingService:
    """
    Service providing execution mode-aware broadcasting with session integration.

    This service determines whether real-time log broadcasting should be enabled
    based on the execution context (authenticated frontend vs public API).
    """

    def __init__(self):
        self.logger = LoggerService(component='core')
        self._lock = threading.RLock()
        self._session_manager = session_manager

    def should_broadcast(self) -> bool:
        """
        Determine if real-time broadcasting should be enabled based on execution mode.

        Returns:
            bool: True if broadcasting should be enabled, False otherwise
        """
        try:
            # Get execution mode from current session
            execution_mode = self.get_current_execution_mode()

            # Only broadcast in authenticated mode
            should_broadcast = execution_mode == 'authenticated'

            self.logger.debug(f"[ExecutionModeBroadcasting] Mode: {execution_mode}, Should broadcast: {should_broadcast}")
            return should_broadcast

        except Exception as e:
            # Default to not broadcasting on error
            self.logger.error(f"[ExecutionModeBroadcasting] Error checking broadcast mode: {e}")
            return False

    def get_current_execution_mode(self) -> str:
        """
        Get the current execution mode from SessionManager.

        Returns:
            str: Execution mode ('public' or 'authenticated')
        """
        try:
            # Check if SessionManager has real-time logging enabled
            if self._session_manager.is_realtime_logging_enabled():
                return 'authenticated'
            else:
                return 'public'
        except Exception:
            # Default to public mode (no broadcasting) on error
            return 'public'

    def detect_execution_mode_from_route(self, route: str) -> str:
        """
        Detect execution mode based on API route path.

        Args:
            route: API route path

        Returns:
            str: Detected execution mode ('public' or 'authenticated')
        """
        # Public API routes (no real-time logging needed)
        public_patterns = [
            r'^/api/public/loop/',
            r'^/api/public/agent/',
            r'^/api/public/runloop/',
        ]

        for pattern in public_patterns:
            if re.match(pattern, route):
                return 'public'

        # All other routes are considered authenticated
        return 'authenticated'

    def detect_execution_mode_from_request(self) -> str:
        """
        Detect execution mode from current Flask request context.

        Returns:
            str: Detected execution mode ('public' or 'authenticated')
        """
        try:
            # Import Flask here to avoid circular imports
            from flask import request

            if hasattr(request, 'path') and request.path:
                return self.detect_execution_mode_from_route(request.path)
        except Exception as e:
            self.logger.debug(f"[ExecutionModeBroadcasting] Could not detect route from request: {e}")

        # Default to authenticated mode
        return 'authenticated'

    def broadcast_log_message(self, user_id: int, action: str, message: str, loop_id: Optional[int] = None):
        """
        Broadcast log message if broadcasting is enabled for current execution mode.

        Args:
            user_id: User ID to send message to
            action: Log action type (info, error, debug, etc.)
            message: Log message content
            loop_id: Optional loop ID
        """
        if not self.should_broadcast():
            # Skip broadcasting in public mode
            self.logger.debug(f"[ExecutionModeBroadcasting] Skipping broadcast - public mode")
            return

        try:
            # Import here to avoid circular imports
            from web.services.socket_io_service import send_message_to_user

            # Prepare message payload
            payload = {'message': message}
            if loop_id is not None:
                payload['loop_id'] = loop_id

            # Send message via SocketIO
            send_message_to_user(user_id, action, payload)

            self.logger.debug(f"[ExecutionModeBroadcasting] Broadcasted {action} message to user {user_id}")

        except Exception as e:
            # Graceful fallback - log error but don't fail
            self.logger.error(f"[ExecutionModeBroadcasting] Failed to broadcast message: {e}")

    def broadcast_if_enabled(self, user_id: int, action: str, message: str, loop_id: Optional[int] = None) -> bool:
        """
        Broadcast message only if broadcasting is enabled, with return status.

        Args:
            user_id: User ID to send message to
            action: Log action type
            message: Log message content
            loop_id: Optional loop ID

        Returns:
            bool: True if message was broadcast, False if skipped
        """
        if self.should_broadcast():
            self.broadcast_log_message(user_id, action, message, loop_id)
            return True
        return False

    def set_execution_mode_for_session(self, mode: str):
        """
        Set execution mode for current session.

        Args:
            mode: Execution mode ('public' or 'authenticated')
        """
        try:
            self._session_manager.set_execution_mode(mode)
            self.logger.debug(f"[ExecutionModeBroadcasting] Set execution mode to: {mode}")
        except Exception as e:
            self.logger.error(f"[ExecutionModeBroadcasting] Failed to set execution mode: {e}")

    def get_broadcasting_stats(self) -> Dict[str, Any]:
        """
        Get broadcasting service statistics.

        Returns:
            dict: Statistics about broadcasting service
        """
        current_mode = self.get_current_execution_mode()
        should_broadcast = self.should_broadcast()

        return {
            'current_execution_mode': current_mode,
            'broadcasting_enabled': should_broadcast,
            'has_active_session': self._session_manager.has_current_session(),
            'realtime_logging_enabled': self._session_manager.is_realtime_logging_enabled() if self._session_manager.has_current_session() else False
        }

    def is_public_api_request(self, route: str) -> bool:
        """
        Check if a route is a public API request.

        Args:
            route: API route path

        Returns:
            bool: True if route is public API
        """
        return self.detect_execution_mode_from_route(route) == 'public'

    def is_authenticated_request(self, route: str) -> bool:
        """
        Check if a route is an authenticated request.

        Args:
            route: API route path

        Returns:
            bool: True if route requires authentication
        """
        return self.detect_execution_mode_from_route(route) == 'authenticated'

    def enable_broadcasting_for_session(self):
        """Enable broadcasting for current session (set to authenticated mode)"""
        self.set_execution_mode_for_session('authenticated')

    def disable_broadcasting_for_session(self):
        """Disable broadcasting for current session (set to public mode)"""
        self.set_execution_mode_for_session('public')


# Singleton instance management
_broadcasting_service_instance = None
_service_lock = threading.Lock()


def get_broadcasting_service() -> ExecutionModeBroadcastingService:
    """
    Get singleton ExecutionModeBroadcastingService instance.

    Returns:
        ExecutionModeBroadcastingService: Singleton service instance
    """
    global _broadcasting_service_instance

    if _broadcasting_service_instance is None:
        with _service_lock:
            if _broadcasting_service_instance is None:
                _broadcasting_service_instance = ExecutionModeBroadcastingService()
                logger = LoggerService(component='core')
                logger.debug("[ExecutionModeBroadcasting] Singleton instance created")

    return _broadcasting_service_instance


def should_broadcast_for_current_session() -> bool:
    """
    Convenience function to check if broadcasting should be enabled for current session.

    Returns:
        bool: True if broadcasting should be enabled
    """
    service = get_broadcasting_service()
    return service.should_broadcast()


def broadcast_log_if_enabled(user_id: int, action: str, message: str, loop_id: Optional[int] = None) -> bool:
    """
    Convenience function to broadcast log message if enabled.

    Args:
        user_id: User ID to send message to
        action: Log action type
        message: Log message content
        loop_id: Optional loop ID

    Returns:
        bool: True if message was broadcast, False if skipped
    """
    service = get_broadcasting_service()
    return service.broadcast_if_enabled(user_id, action, message, loop_id)