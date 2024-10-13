from abc import abstractmethod

from core.models.broadcast_data import BroadcastData


class AdapterInterface:
    @abstractmethod
    def __init__(self, source: str):
        pass

    def get_input(self) -> str:
        pass

    def read(self, session_id: str, step_id: str) -> BroadcastData:
        pass

    def write(self, step_id, data: BroadcastData) -> bool:
        pass
