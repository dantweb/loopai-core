import uuid
import threading
import copy
from typing import Optional, Any, Dict
from core.models.broadcast_data import BroadcastData

# Gevent support
try:
    import gevent
    from gevent.local import local as gevent_local
    GEVENT_AVAILABLE = True
except ImportError:
    GEVENT_AVAILABLE = False
    gevent = None
    gevent_local = None


class ThreadSafeSessionManager:
    """
    Thread-safe session manager that allows concurrent loop execution
    by maintaining per-thread or per-session isolated state.
    """

    def __init__(self):
        self._local = threading.local()
        self._lock = threading.RLock()
        self._global_sessions: Dict[str, dict] = {}

        # Initialize gevent-local storage if available
        if GEVENT_AVAILABLE:
            self._gevent_local = gevent_local()

    def _is_in_gevent_context(self) -> bool:
        """Detect if we're running in a gevent greenlet"""
        if not GEVENT_AVAILABLE:
            return False
        try:
            current = gevent.getcurrent()
            # If we get a greenlet that's not the main thread, we're in gevent context
            return current is not gevent.get_hub().parent
        except:
            return False

    def _get_local_storage(self):
        """Get appropriate local storage based on execution context"""
        if self._is_in_gevent_context():
            return self._gevent_local
        return self._local

    def _ensure_local_session(self):
        """Ensure local session data exists (gevent or thread-local)"""
        local_storage = self._get_local_storage()
        if not hasattr(local_storage, 'session_data'):
            local_storage.session_data = {
                'session_id': str(uuid.uuid4()),
                'user_id': None,
                'loop_id': None,
                'project_id': None,
                'environment': None,
                'step_name': None,
                'loop_index': None,
                'global_step_name': None,
                'global_loop_index': None,
                'bc_collection': [],
                'request_data': None
            }

    def get_session_id(self) -> str:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data['session_id']

    def regenerate_session_id(self):
        """Generate new session ID and reset all session data"""
        with self._lock:
            self._ensure_local_session()
            local_storage = self._get_local_storage()
            old_session_id = local_storage.session_data.get('session_id')

            # Remove old session from global registry if it exists
            if old_session_id and old_session_id in self._global_sessions:
                del self._global_sessions[old_session_id]

            # Reset all session data
            new_session_id = str(uuid.uuid4())
            local_storage.session_data = {
                'session_id': new_session_id,
                'user_id': None,
                'loop_id': None,
                'project_id': None,
                'environment': None,
                'step_name': None,
                'loop_index': None,
                'global_step_name': None,
                'global_loop_index': None,
                'bc_collection': [],
                'request_data': None
            }

            # Register new session (copy to avoid reference sharing)
            self._global_sessions[new_session_id] = local_storage.session_data.copy()

    def create_session_for_loop(self, user_id: int, loop_id: int, project_id: int = None) -> str:
        """Create a new isolated session for a specific loop execution"""
        with self._lock:
            session_id = str(uuid.uuid4())
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'loop_id': loop_id,
                'project_id': project_id,
                'environment': None,
                'step_name': None,
                'loop_index': None,
                'global_step_name': None,
                'global_loop_index': None,
                'bc_collection': [],
                'request_data': None
            }

            # Store in global registry and local storage as separate copies
            self._global_sessions[session_id] = session_data.copy()
            local_storage = self._get_local_storage()
            local_storage.session_data = session_data

            return session_id

    def get_session_by_id(self, session_id: str) -> Optional[dict]:
        """Get session data by session ID"""
        with self._lock:
            return self._global_sessions.get(session_id)

    def cleanup_session(self, session_id: str = None):
        """Clean up session data"""
        with self._lock:
            if session_id:
                if session_id in self._global_sessions:
                    del self._global_sessions[session_id]
            else:
                # Clean up current local session
                self._ensure_local_session()
                local_storage = self._get_local_storage()
                current_session_id = local_storage.session_data.get('session_id')
                if current_session_id and current_session_id in self._global_sessions:
                    del self._global_sessions[current_session_id]
                # Clear local data
                if hasattr(local_storage, 'session_data'):
                    delattr(local_storage, 'session_data')

    def set_environment(self, environment: dict):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        # Deep copy environment to ensure isolation between sessions
        local_storage.session_data['environment'] = copy.deepcopy(environment) if environment else None

    def get_env(self, value_name: str) -> Any:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        env = local_storage.session_data.get('environment')
        if not env or value_name not in env:
            return None
        return env[value_name]

    def set_loop_id(self, loop_id: int):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['loop_id'] = loop_id

    def set_user_id(self, user_id: int):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['user_id'] = user_id

    def get_user_id(self) -> Optional[int]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('user_id')

    def set_project_id(self, project_id: int):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['project_id'] = project_id

    def get_project_id(self) -> Optional[int]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('project_id')

    def get_loop_id(self) -> Optional[int]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('loop_id')

    def get_loop_index(self) -> Optional[int]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('loop_index')

    def set_loop_index(self, index: int):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['loop_index'] = index

    def get_environment(self) -> Optional[dict]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('environment')

    def set_step_name(self, step_name: str):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['step_name'] = step_name

    def set_global_loop_index(self, loop_index: int):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['global_loop_index'] = loop_index

    def set_global_step_name(self, step_name: str):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['global_step_name'] = step_name

    def get_global_step_name(self) -> Optional[str]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('global_step_name')

    def collect_broadcast(self, bc: BroadcastData):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['bc_collection'].append(bc['result'])

    def get_broadcast_collection(self) -> list:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('bc_collection', [])

    def get_bc_collection_json(self) -> list[Any]:
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        bc_list = []
        bc_collection = local_storage.session_data.get('bc_collection', [])
        for bc in bc_collection:
            if hasattr(bc, 'to_dict'):
                bc_list.append(bc.to_dict())
            else:
                bc_list.append(bc)
        return bc_list

    def clear_broadcast_collection(self):
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['bc_collection'] = []

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions for monitoring"""
        with self._lock:
            return len(self._global_sessions)

    def has_current_session(self) -> bool:
        """Check if current local context has an active session"""
        try:
            local_storage = self._get_local_storage()
            return hasattr(local_storage, 'session_data') and local_storage.session_data is not None
        except:
            return False

    def list_active_sessions(self) -> list:
        """List all active session IDs for debugging"""
        with self._lock:
            return list(self._global_sessions.keys())

    def set_request_data(self, request_data: dict):
        """Store HTTP request data in session for RequestAdapter access"""
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        local_storage.session_data['request_data'] = request_data

    def get_request_data(self) -> Optional[dict]:
        """Get HTTP request data from session"""
        self._ensure_local_session()
        local_storage = self._get_local_storage()
        return local_storage.session_data.get('request_data')


# Create singleton instance
thread_safe_session_manager = ThreadSafeSessionManager()