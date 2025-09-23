from abc import ABC
from typing import Optional
import threading

from core.services.session_manager import SessionManager


class SessionDependent(ABC):
    """
    Abstract base class for components that depend on session context.
    Provides standardized session access and graceful fallback handling.
    """

    def __init__(self):
        super().__init__()
        self._session_manager = None

    @property
    def session_manager(self):
        """Get session manager instance"""
        if self._session_manager is None:
            from .session_manager import session_manager
            self._session_manager = session_manager
        return self._session_manager

    def has_session(self) -> bool:
        """Check if current thread has an active session"""
        try:
            return self.session_manager.has_current_session()
        except Exception:
            return False

    def get_user_id(self) -> Optional[int]:
        """Get current user ID from thread-local session"""
        try:
            return self.session_manager.get_user_id() if self.has_session() else None
        except Exception:
            return None

    def get_loop_id(self) -> Optional[int]:
        """Get current loop ID from thread-local session"""
        try:
            return self.session_manager.get_loop_id() if self.has_session() else None
        except Exception:
            return None

    def get_project_id(self) -> Optional[int]:
        """Get current project ID from thread-local session"""
        try:
            return self.session_manager.get_project_id() if self.has_session() else None
        except Exception:
            return None

    def get_session_id(self) -> Optional[str]:
        """Get current session ID from thread-local session"""
        try:
            return self.session_manager.get_session_id() if self.has_session() else None
        except Exception:
            return None

    def get_environment_var(self, key: str, default: str = None) -> Optional[str]:
        """Get environment variable from session with fallback"""
        try:
            return self.session_manager.get_env(key) if self.has_session() else default
        except Exception:
            return default

    def add_broadcast_data(self, data):
        """Add data to session broadcast collection with graceful fallback"""
        try:
            if self.has_session():
                self.session_manager.collect_broadcast(data)
        except Exception as e:
            print(f"Failed to add broadcast data: {e}")

    def get_broadcast_collection(self) -> list:
        """Get broadcast collection from current thread session"""
        try:
            return self.session_manager.get_broadcast_collection() if self.has_session() else []
        except Exception:
            return []

    def get_broadcast_data_json(self) -> list:
        """Get JSON broadcast data from current thread session"""
        try:
            return self.session_manager.get_bc_collection_json() if self.has_session() else []
        except Exception:
            return []

    def get_current_session_info(self) -> dict:
        """Get current session information for debugging/logging"""
        if not self.has_session():
            return {"has_session": False, "thread_id": threading.current_thread().ident}

        return {
            "has_session": True,
            "user_id": self.get_user_id(),
            "loop_id": self.get_loop_id(),
            "project_id": self.get_project_id(),
            "session_id": self.get_session_id(),
            "thread_id": threading.current_thread().ident
        }

    def get_current_session_manager(self) -> SessionManager:
        return self.session_manager
