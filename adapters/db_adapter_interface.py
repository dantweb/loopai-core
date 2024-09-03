from abc import ABC, abstractmethod
from typing import Any


class DbAdapterInterface(ABC):

    @abstractmethod
    def read(self, session_id: str, step_id: str):
        """
        Reads data from the database based on session_id and step_id.

        :param session_id: The session ID to filter the read operation.
        :param step_id: The step ID to filter the read operation.
        :return: The data retrieved from the database.
        """
        pass

    @abstractmethod
    def write(self, data: Any) -> bool:
        """
        Writes data to the database.

        :param data: The data to write to the database.
        :return: True if the write operation was successful, False otherwise.
        """
        pass
