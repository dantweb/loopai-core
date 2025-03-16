import uuid

class SessionManager:
    def __init__(self):
        self._session_id = str(uuid.uuid4())

    def get_session_id(self):
        return self._session_id

    def regenerate_session_id(self):
        self._session_id = str(uuid.uuid4())


# Singleton instance for global usage
session_manager = SessionManager()
