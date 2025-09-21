# ./loopai_src/core/services/logger_service.py
import logging
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

import app_global_config as config
import threading

from core.services.session import session_manager
from core.services.thread_safe_session import thread_safe_session_manager
from web.services.socket_io_service import send_message_to_user

def get_session_manager():
    """Get the appropriate session manager based on execution context"""
    try:
        # First try the enhanced session manager (works in both thread and gevent contexts)
        if session_manager.has_current_session():
            return session_manager

        # If thread-safe session manager has active session, use it (backward compatibility)
        if thread_safe_session_manager.has_current_session():
            return thread_safe_session_manager
    except:
        pass
    # Fall back to global session manager
    return session_manager


class GeventSessionBridge:
    """Bridge that allows GeventSessionContext to work with existing session manager interface"""

    def __init__(self, gevent_session_context):
        self.context = gevent_session_context

    def get_user_id(self):
        return self.context.get_user_id()

    def get_loop_id(self):
        return self.context.get_loop_id()

    def get_project_id(self):
        return self.context.get_project_id()

    def get_session_id(self):
        return self.context.get_session_id()

class LoggerService:
    # For backward compatibility - single legacy instance
    _instance = None
    # Component-specific instances for enhanced usage
    _component_instances: Dict[str, 'LoggerService'] = {}
    _lock = threading.Lock()
    _num_of_logs_to_return = 10
    _logger = None

    def __new__(cls, user_id=None, component: str = 'core'):
        # Validate component
        valid_components = ['core', 'web', 'system']
        if component not in valid_components:
            raise ValueError(f"Invalid component '{component}'. Must be one of: {valid_components}")

        # If component is explicitly provided and not 'core', use component-specific instance
        if component != 'core':
            if component not in cls._component_instances:
                with cls._lock:
                    if component not in cls._component_instances:
                        instance = super(LoggerService, cls).__new__(cls)
                        instance.__initialized = False
                        instance._component = component
                        cls._component_instances[component] = instance
            return cls._component_instances[component]

        # Legacy behavior: maintain single instance for 'core' component
        if not hasattr(cls, '_instance') or cls._instance is None:
            with cls._lock:
                if not hasattr(cls, '_instance') or cls._instance is None:
                    cls._instance = super(LoggerService, cls).__new__(cls)
                    cls._instance.__initialized = False
                    cls._instance._component = 'core'

        return cls._instance

    def __init__(self, user_id=None, component: str = 'core'):
        # Store user_id per thread since this is a singleton
        if not hasattr(self, '_thread_user_ids'):
            self._thread_user_ids = {}

        if user_id:
            thread_id = threading.get_ident()
            self._thread_user_ids[thread_id] = user_id

        if hasattr(self, '_LoggerService__initialized') and self.__initialized:
            return

        self.log_lock = threading.Lock()
        self.logs = []
        self._component = getattr(self, '_component', component)
        self.__initialized = True

        # Use enhanced configuration if available, otherwise fall back to legacy
        if hasattr(self, '_configure_enhanced_logger'):
            try:
                self._configure_enhanced_logger()
            except Exception as e:
                # Fall back to legacy configuration if enhanced fails
                self._configure_legacy_logger()
                print(f"Enhanced logging configuration failed, using legacy: {e}")
        else:
            self._configure_legacy_logger()

        self._logger.debug(f"Logging configured for component '{self._component}'")

    def _configure_legacy_logger(self):
        """Configure logger using legacy settings for backward compatibility"""
        self._logger = logging.getLogger(__name__)
        self._handler = RotatingFileHandler('core.log', maxBytes=10000, backupCount=3)
        self._handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
        self._handler.setFormatter(formatter)
        self._logger.addHandler(self._handler)
        self._logger.setLevel(logging.DEBUG)

    def _get_current_user_id(self):
        """Get current user ID from either thread-local user_id or session manager"""
        # First, check if this thread has a stored user_id
        if hasattr(self, '_thread_user_ids'):
            thread_id = threading.get_ident()
            if thread_id in self._thread_user_ids:
                return self._thread_user_ids[thread_id]

        # Otherwise, get from the appropriate session manager
        current_session = get_session_manager()
        return current_session.get_user_id()

    def _filter_message(self, message: str) -> str:
        """
        Filters out long base64 content for fields like 'image_base64'.
        This function finds segments like:
            'image_base64': '<base64_content>'
        and if the base64 content is longer than 24 characters, it replaces it with:
            'image_base64': '<first 24 chars>...(More <remaining_length>)'
        """
        # This regex matches the field and divides the value into two groups:
        # group(2) contains the first 24 characters and group(3) the rest.
        pattern = re.compile(r"('image_base64':\s*')([^']{24})([^']*)(')")
        def repl(match):
            first24 = match.group(2)
            remaining = match.group(3)
            if remaining:
                return f"{match.group(1)}{first24}...(More {len(remaining)}){match.group(4)}"
            return match.group(0)
        return pattern.sub(repl, message)

    def log(self, message: str, action: str = 'log'):
        # Apply filtering to the log message.
        filtered_message = self._filter_message(message)
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")

        # Use the appropriate session manager
        current_session = get_session_manager()
        web_user_id = current_session.get_user_id()
        loop_id = current_session.get_loop_id()

        log_message = f"[{timestamp}] [server] UserID=[{web_user_id}] {action}: {filtered_message}"

        if config.WEB_OR_CLI == 'web':
            # Send the log message to the user if needed.
            current_user_id = self._get_current_user_id()
            if current_user_id:
                send_message_to_user(current_user_id, action, {'message': filtered_message, 'loop_id': loop_id})

        self.logs.append(log_message)
        self._logger.debug(str(log_message))

    def info(self, message: str):
        self.log(str(message), 'info')

    def warning(self, message: str):
        self.log(str(message), 'warning')

    def debug(self, message: str):
        self.log(str(message), 'debug')

    def error(self, message: str):
        self.log(str(message), 'error')

    def get_logs(self):
        """Returns the last `n` logs as defined by `_num_of_logs_to_return`."""
        with self.log_lock:
            return self.logs[-self._num_of_logs_to_return:]

    def set_num_of_logs_to_return(self, num: int):
        """Sets the number of logs to return in the `get_logs` method."""
        with self.log_lock:
            self._num_of_logs_to_return = num

    # Enhanced LoggerService methods

    def _configure_enhanced_logger(self):
        """Configure logger with environment-based settings"""
        # Get log configuration from environment
        log_path = self.get_log_path()
        log_file = self.get_log_file()
        log_level = self.get_log_level()
        max_size = self._parse_file_size(os.environ.get('LOOPAI_LOG_MAX_SIZE', '1MB'))
        backup_count = int(os.environ.get('LOOPAI_LOG_BACKUP_COUNT', '3'))

        # Ensure log directory exists
        self.ensure_log_directory()

        # Configure logger
        component = getattr(self, '_component', 'core')
        logger_name = f"loopai.{component}"
        self._logger = logging.getLogger(logger_name)

        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Create rotating file handler
        self._handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        # Set log level
        level = getattr(logging, log_level.upper(), logging.DEBUG)
        self._handler.setLevel(level)
        self._logger.setLevel(level)

        # Enhanced formatter with component and user context
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(threadName)s : %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self._handler.setFormatter(formatter)
        self._logger.addHandler(self._handler)

    def get_log_path(self) -> str:
        """Get log directory path from environment or use default"""
        return os.environ.get('LOOPAI_LOG_PATH', '/app/var/logs')

    def get_log_file(self) -> str:
        """Get component-specific log file path"""
        log_path = self.get_log_path()
        component = getattr(self, '_component', 'core')
        return os.path.join(log_path, f'{component}.log')

    def get_log_level(self) -> str:
        """Get log level from environment or use default"""
        return os.environ.get('LOOPAI_LOG_LEVEL', 'DEBUG')

    def get_max_file_size(self) -> str:
        """Get maximum file size setting"""
        return os.environ.get('LOOPAI_LOG_MAX_SIZE', '10MB')

    def get_backup_count(self) -> int:
        """Get backup count setting"""
        return int(os.environ.get('LOOPAI_LOG_BACKUP_COUNT', '3'))

    def ensure_log_directory(self):
        """Ensure log directory exists"""
        log_path = self.get_log_path()
        os.makedirs(log_path, exist_ok=True)

    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string (e.g., '10MB') to bytes"""
        size_str = size_str.upper().strip()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes if no unit
            return int(size_str)

    def get_component(self) -> str:
        """Get logger component name"""
        return getattr(self, '_component', 'core')

    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics"""
        return {
            'component': self.get_component(),
            'log_file': self.get_log_file(),
            'log_level': self.get_log_level(),
            'max_file_size': self.get_max_file_size(),
            'backup_count': self.get_backup_count(),
            'active_threads': len(self._thread_user_ids) if hasattr(self, '_thread_user_ids') else 0
        }


# Enhanced singleton functions
_logger_service_instances: Dict[str, LoggerService] = {}
_service_lock = threading.Lock()


def get_logger_service(component: str = 'core') -> LoggerService:
    """
    Get singleton LoggerService instance for specified component.

    Args:
        component: Component name (core, web, system)

    Returns:
        LoggerService: Component-specific logger instance
    """
    global _logger_service_instances

    # Validate component
    valid_components = ['core', 'web', 'system']
    if component not in valid_components:
        raise ValueError(f"Invalid component '{component}'. Must be one of: {valid_components}")

    if component not in _logger_service_instances:
        with _service_lock:
            if component not in _logger_service_instances:
                # Create instance with enhanced configuration
                instance = LoggerService(component=component)
                _logger_service_instances[component] = instance

    return _logger_service_instances[component]
