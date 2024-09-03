from abc import abstractmethod


class AdapterInterface:
    @abstractmethod
    def __init__(self, source: str):
        pass

    def get_input(self) -> str:
        pass

    def read(self, session_id: str, step_id: str):
        pass

    def write(self, step_id, data):
        pass
