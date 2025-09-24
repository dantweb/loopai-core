##filepath: ./loopai_src/core/adapters/adapter_interface.py

from abc import abstractmethod, ABC
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.session_dependent import SessionDependent


class AdapterInterface(SessionDependent):
    @abstractmethod
    def __init__(self):
        super().__init__()
        self.logger = LoggerService(component='core')

    def get_input(self) -> str:
        pass

    def read(self, session_id: str, step_id: str) -> BroadcastData:
        pass

    def write(self, step_id, data: BroadcastData) -> bool:
        pass
