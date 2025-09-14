# ./loopai_src/core/services/logger_service.py
import logging
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler

import app_global_config as config
import threading

from core.services.session import session_manager
from web.services.socket_io_service import send_message_to_user

class LoggerService:
    _instance = None
    _lock = threading.Lock()
    _num_of_logs_to_return = 10
    _logger = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance') or cls._instance is None:
            with cls._lock:
                if not hasattr(cls, '_instance') or cls._instance is None:
                    cls._instance = super(LoggerService, cls).__new__(cls, *args, **kwargs)
                    cls._instance.__initialized = False

        return cls._instance

    def __init__(self, user_id=None):
        self.user_id = user_id or session_manager.get_user_id()
        if self.__initialized:
            return
        self.log_lock = threading.Lock()
        self.logs = []
        self.__initialized = True

        self._logger = logging.getLogger(__name__)
        self._handler = RotatingFileHandler('core.log', maxBytes=10000, backupCount=3)
        self._handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
        self._handler.setFormatter(formatter)
        self._logger.addHandler(self._handler)
        self._logger.setLevel(logging.DEBUG)
        self._logger.debug("Logging configured")

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
        web_user_id = session_manager.get_user_id()
        loop_id = session_manager.get_loop_id()
        log_message = f"[{timestamp}] [server] UserID=[{web_user_id}] {action}: {filtered_message}"

        if config.WEB_OR_CLI == 'web':
            # Send the log message to the user if needed.
            if self.user_id:
                send_message_to_user(self.user_id, action, {'message': filtered_message, 'loop_id': loop_id})

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
