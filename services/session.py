import uuid
import threading
import copy
import os
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


class SessionManager:
    """
    Enhanced SessionManager providing multi-user session isolation for concurrent loop execution.

    Features:
    - Thread and gevent-local storage for proper isolation
    - Hierarchical environment variable management (Project → Loop → Step)
    - Session lifecycle management with cleanup
    - Execution mode awareness (public vs authenticated)
    - Request data storage for RequestAdapter integration
    - Backward compatibility with existing code
    """

    def __init__(self):
        # Legacy single-session state (for backward compatibility)
        self._loop_index = None
        self._global_step_name = None
        self._global_loop_index = None
        self._step_name = None
        self._user_id: Optional[int] = None
        self._loop_id: Optional[int] = None
        self._environment: Optional[dict] = None
        self._session_id: str = str(uuid.uuid4())
        self._project_id: Optional[int] = None
        self._bc_collection = []

        # Enhanced multi-user session support
        self._local = threading.local()
        self._lock = threading.RLock()
        self._global_sessions: Dict[str, dict] = {}
        self._execution_mode = 'authenticated'  # Default to authenticated mode

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
                'request_data': None,
                'execution_mode': 'authenticated'
            }

    def _use_legacy_mode(self) -> bool:
        """Determine if we should use legacy single-session mode for backward compatibility"""
        # Use legacy mode if no local session exists and we have legacy state
        local_storage = self._get_local_storage()
        has_local_session = hasattr(local_storage, 'session_data')
        has_legacy_state = (self._user_id is not None or
                           self._loop_id is not None or
                           self._environment is not None)
        return not has_local_session and has_legacy_state

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
                'request_data': None,
                'execution_mode': self._execution_mode
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
                local_storage = self._get_local_storage()
                if hasattr(local_storage, 'session_data'):
                    current_session_id = local_storage.session_data.get('session_id')
                    if current_session_id and current_session_id in self._global_sessions:
                        del self._global_sessions[current_session_id]
                    # Clear local data
                    delattr(local_storage, 'session_data')

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

    def set_execution_mode(self, mode: str):
        """Set execution mode (public or authenticated)"""
        self._execution_mode = mode
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['execution_mode'] = mode

    def is_realtime_logging_enabled(self) -> bool:
        """Check if real-time logging should be enabled based on execution mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            mode = local_storage.session_data.get('execution_mode', 'authenticated')
        else:
            mode = self._execution_mode
        return mode == 'authenticated'

    def get_hierarchical_environment(self, user_id: int, loop_id: int, step_name: str = None) -> dict:
        """
        Load hierarchical environment variables: Project → Loop → Step inheritance
        Each level can override the previous level's variables.
        """
        from core.adapters.file_adapter_interface import get_loop_config_base_path_by_user_and_loop

        # Start with base environment variables - skip OS environment for testing
        env = {}

        # Get loop config path
        loop_config_path = get_loop_config_base_path_by_user_and_loop(str(user_id), str(loop_id))

        # Load loop-level .env file
        try:
            loop_env_file = os.path.join(loop_config_path, '.env')
            if os.path.exists(loop_env_file):
                with open(loop_env_file, 'r') as f:
                    loop_env_content = f.read()
                    loop_env = self._parse_env_content(loop_env_content)
                    env.update(loop_env)
        except Exception as e:
            # For debugging in tests
            pass

        # Load step-level .env file if step_name is provided
        if step_name:
            try:
                step_env_file = os.path.join(loop_config_path, f'{step_name}.env')
                if os.path.exists(step_env_file):
                    with open(step_env_file, 'r') as f:
                        step_env_content = f.read()
                        step_env = self._parse_env_content(step_env_content)
                        env.update(step_env)
            except Exception as e:
                # For debugging in tests
                pass

        return env

    def _parse_env_content(self, content: str) -> dict:
        """Parse environment file content into dictionary"""
        env = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
        return env

    def get_step_name(self) -> Optional[str]:
        """Get current step name"""
        if self._use_legacy_mode():
            return self._step_name

        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('step_name')

        return self._step_name

    def get_session_id(self):
        """Get session ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data['session_id']
        return self._session_id

    def regenerate_session_id(self):
        self._session_id = str(uuid.uuid4())
        self._step_name = None
        self._user_id: Optional[int] = None
        self._loop_id: Optional[int] = None
        self._loop_index = None
        self._environment: Optional[dict] = None
        self._global_step_name = None
        self._global_loop_index = None
        self._project_id: Optional[int] = None

    def set_environment(self, environment):
        """Set environment - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            # Deep copy environment to ensure isolation between sessions
            local_storage.session_data['environment'] = copy.deepcopy(environment) if environment else None
        else:
            self._environment = environment

    def get_env(self, value_name: str):
        """Get environment variable - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            env = local_storage.session_data.get('environment')
            if not env or value_name not in env:
                return None
            return env[value_name]

        if not self._environment:
            return None
        if value_name not in self._environment:
            return None
        return self._environment[value_name]

    def set_loop_id(self, loop_id: int):
        """Set loop ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['loop_id'] = loop_id
        else:
            self._loop_id = loop_id

    def set_user_id(self, user_id: int):
        """Set user ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['user_id'] = user_id
        else:
            self._user_id = user_id

    def get_user_id(self) -> Optional[int]:
        """Get user ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('user_id')
        return self._user_id

    def set_project_id(self, project_id: int):
        """Set project ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['project_id'] = project_id
        else:
            self._project_id = project_id

    def get_project_id(self) -> Optional[int]:
        """Get project ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('project_id')
        return self._project_id

    def get_loop_id(self) -> Optional[int]:
        """Get loop ID - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('loop_id')
        return self._loop_id

    def get_loop_index(self) -> Optional[int]:
        """Get loop index - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('loop_index')
        return self._loop_index

    def set_loop_index(self, index):
        """Set loop index - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['loop_index'] = index
        else:
            self._loop_index = index

    def get_environment(self) -> Optional[dict]:
        """Get environment - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('environment')
        return self._environment

    def set_step_name(self, step_name: str):
        """Set step name - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['step_name'] = step_name
        else:
            self._step_name = step_name

    def set_global_loop_index(self, loop_index: int):
        """Set global loop index - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['global_loop_index'] = loop_index
        else:
            self._global_loop_index = loop_index

    def set_global_step_name(self, step_name: str):
        """Set global step name - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['global_step_name'] = step_name
        else:
            self._global_step_name = step_name

    def get_global_step_name(self):
        """Get global step name - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('global_step_name')
        return self._global_step_name

    def collect_broadcast(self, bc: BroadcastData):
        """Collect broadcast data - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            # Handle BroadcastData properly - check if it has 'result' key
            if isinstance(bc, dict) and 'result' in bc:
                local_storage.session_data['bc_collection'].append(bc['result'])
            else:
                # Store the BroadcastData object directly
                local_storage.session_data['bc_collection'].append(bc)
        else:
            # Legacy mode - try to extract 'result' or store directly
            if isinstance(bc, dict) and 'result' in bc:
                self._bc_collection.append(bc['result'])
            else:
                self._bc_collection.append(bc)

    def get_broadcast_collection(self) -> list:
        """Get broadcast collection - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('bc_collection', [])
        return self._bc_collection

    def get_bc_collection_json(self) -> list[Any]:
        """Get broadcast collection as JSON - supports both legacy and enhanced mode"""
        bc_list = []
        if self.has_current_session():
            local_storage = self._get_local_storage()
            bc_collection = local_storage.session_data.get('bc_collection', [])
        else:
            bc_collection = self._bc_collection

        for bc in bc_collection:
            if hasattr(bc, 'to_dict'):
                bc_list.append(bc.to_dict())
            else:
                bc_list.append(bc)
        return bc_list

    def clear_broadcast_collection(self):
        """Clear broadcast collection - supports both legacy and enhanced mode"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['bc_collection'] = []
        else:
            self._bc_collection = []

    def get_request_data(self) -> Optional[dict]:
        """Get request data - enhanced mode with backward compatibility"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            return local_storage.session_data.get('request_data')

        # Fallback to bridge method for backward compatibility
        try:
            from core.services.thread_safe_session import thread_safe_session_manager
            return thread_safe_session_manager.get_request_data()
        except ImportError:
            return None
        except Exception:
            return None

    def set_request_data(self, request_data: dict):
        """Set request data - enhanced mode with backward compatibility"""
        if self.has_current_session():
            local_storage = self._get_local_storage()
            local_storage.session_data['request_data'] = request_data
        else:
            # Fallback to bridge method for backward compatibility
            try:
                from core.services.thread_safe_session import thread_safe_session_manager
                return thread_safe_session_manager.set_request_data(request_data)
            except ImportError:
                pass
            except Exception:
                pass


# Singleton instance for global usage
session_manager = SessionManager()

