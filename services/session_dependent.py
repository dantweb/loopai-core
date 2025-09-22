from abc import ABC
from typing import Optional
from .session import SessionData


class SessionDependent(ABC):
    """
    Abstract base class for components that depend on session context.
    Provides standardized session access and graceful fallback handling.
    """

    def __init__(self):
        self._session_manager = None

    @property
    def session_manager(self):
        """Get session manager instance"""
        if self._session_manager is None:
            from .session import session_manager
            self._session_manager = session_manager
        return self._session_manager

    def get_current_session(self) -> Optional[SessionData]:
        """
        Get current session with graceful fallback.
        Returns None if no session is available.
        """
        try:
            return self.session_manager.get_current_session()
        except Exception:
            return None

    def has_session(self) -> bool:
        """Check if current session is available"""
        return self.get_current_session() is not None

    def get_session_attribute(self, attribute: str, default=None):
        """
        Get session attribute with fallback.

        Args:
            attribute: Session attribute name
            default: Default value if session not available or attribute missing
        """
        session = self.get_current_session()
        if session is None:
            return default
        return getattr(session, attribute, default)

    def get_user_id(self) -> Optional[int]:
        """Get current user ID from session"""
        return self.get_session_attribute('user_id')

    def get_loop_id(self) -> Optional[int]:
        """Get current loop ID from session"""
        return self.get_session_attribute('loop_id')

    def get_project_id(self) -> Optional[int]:
        """Get current project ID from session"""
        return self.get_session_attribute('project_id')

    def get_agent_id(self) -> Optional[int]:
        """Get current agent ID from session"""
        return self.get_session_attribute('agent_id')

    def get_execution_id(self) -> Optional[str]:
        """Get current execution ID from session"""
        return self.get_session_attribute('execution_id')

    def add_broadcast_data(self, data, data_type: str = "default"):
        """
        Add data to session broadcast collection with graceful fallback.

        Args:
            data: Data to broadcast
            data_type: Type of broadcast data
        """
        session = self.get_current_session()
        if session is not None:
            try:
                session.add_broadcast_data(data, data_type)
            except Exception as e:
                print(f"Failed to add broadcast data: {e}")

    def get_broadcast_collection(self) -> list:
        """Get broadcast collection from session with fallback"""
        session = self.get_current_session()
        if session is not None:
            return getattr(session, 'broadcast_collection', [])
        return []

    def get_broadcast_data_json(self) -> list:
        """Get JSON broadcast data from session with fallback"""
        session = self.get_current_session()
        if session is not None:
            return getattr(session, 'broadcast_data_json', [])
        return []