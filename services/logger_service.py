# .src/services/logger_service.py
from datetime import datetime
import config
import threading
from flask_socketio import SocketIO, emit

socketio = SocketIO()

class LoggerService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance') or cls._instance is None:
            with cls._lock:
                if not hasattr(cls, '_instance') or cls._instance is None:
                    cls._instance = super(LoggerService, cls).__new__(cls, *args, **kwargs)
                    cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        self.log_lock = threading.Lock()
        self.logs = []
        self.__initialized = True

    def log(self, message, action='log'):
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        web_session_id = config.WEB_SESSION_ID
        log_message = f"[{timestamp}] [{web_session_id}] {action}: {message}"
        with self.log_lock:
            self.logs.append(log_message)
            print(log_message)  # Optionally print the log to the console as well
            socketio.emit('log', {'message': log_message})  # Emit log message via SocketIO

    def info(self, message):
        self.log(message, 'info')

    def warning(self, message):
        self.log(message, 'warning')

    def error(self, message):
        self.log(message, 'error')

    def get_logs(self):
        with self.log_lock:
            return list(self.logs)
