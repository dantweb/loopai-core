# .src/services/logger_service.py
from datetime import datetime
import config
import threading
# from flask_socketio import emit
# from web.services.socket_io_service import socket
from web.services.socket_io_service import send_message_to_user

import logging


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
        self.user_id = user_id

        if self.__initialized:
            return
        self.log_lock = threading.Lock()
        self.logs = []
        self.__initialized = True

    def log(self, message, action='log'):
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        logging.info(f"Emitting {action} message: {message}")
        web_user_id = config.GLOBAL_USER_ID
        log_message = f"[{timestamp}] UserID=[{web_user_id}] {action}: {message}"

        if config.WEB_OR_CLI == 'web':
            # now we remove this broadcasting thingy:
            # socket.emit(action, {'data': log_message})

            # Send the log message to the user
            if web_user_id:
                # Emit the log message to the user
                send_message_to_user(web_user_id, 'log', {'message': message})

        self.logs.append(log_message)
        print(log_message)

    def info(self, message):
        self.log(message, 'info')

    def warning(self, message):
        self.log(message, 'warning')

    def error(self, message):
        self.log(message, 'error')

    def get_logs(self):
        """Returns the last `n` logs as defined by `_num_of_logs_to_return`."""
        with self.log_lock:
            return self.logs[-self._num_of_logs_to_return:]

    def set_num_of_logs_to_return(self, num):
        """Sets the number of logs to return in the `get_logs` method."""
        with self.log_lock:
            self._num_of_logs_to_return = num

# You can now adjust how many logs you want to return using the `set_num_of_logs_to_return` method.
