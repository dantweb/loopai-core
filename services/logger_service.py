# ./loopai_src/core/services/logger_service.py
import re
from datetime import datetime
import app_global_config as config
import threading
from web.services.socket_io_service import send_message_to_user

class LoggerService:
    _instance = None
    _lock = threading.Lock()
    _num_of_logs_to_return = 10  # Default number of logs to return

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance') or cls._instance is None:
            with cls._lock:
                if not hasattr(cls, '_instance') or cls._instance is None:
                    cls._instance = super(LoggerService, cls).__new__(cls, *args, **kwargs)
                    cls._instance.__initialized = False
        return cls._instance

    def __init__(self, user_id=None):
        self.user_id = user_id or config.GLOBAL_USER_ID
        if self.__initialized:
            return
        self.log_lock = threading.Lock()
        self.logs = []
        self.__initialized = True

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
        web_user_id = config.GLOBAL_USER_ID
        log_message = f"[{timestamp}] UserID=[{web_user_id}] {action}: {filtered_message}"

        if config.WEB_OR_CLI == 'web':
            # Send the log message to the user if needed.
            if self.user_id:
                send_message_to_user(self.user_id, action, {'message': filtered_message})

        self.logs.append(log_message)
        print(log_message)

    def info(self, message: str):
        self.log(message, 'info')

    def warning(self, message: str):
        self.log(message, 'warning')

    def debug(self, message: str):
        self.log(message, 'debug')

    def error(self, message: str):
        self.log(message, 'error')

    def get_logs(self):
        """Returns the last `n` logs as defined by `_num_of_logs_to_return`."""
        with self.log_lock:
            return self.logs[-self._num_of_logs_to_return:]

    def set_num_of_logs_to_return(self, num: int):
        """Sets the number of logs to return in the `get_logs` method."""
        with self.log_lock:
            self._num_of_logs_to_return = num
