# src/adapters/text_adapter.py
import os
import json
from core.adapters.file_adapter_interface import FileAdapterInterface
from typing import List

from core.services.session import session_id


class TextAdapter(FileAdapterInterface):
    def __init__(self, source: str):
        super().__init__()
        self.source = source
        self.path = self.get_full_path(self.source)

    def read(self, p1, p2, ignore_read_status=False, *args) -> List[str]:
        """
        Reads a text file and returns its contents as a list of strings.

        :param args: Additional arguments (if any).
        :return: List of strings where each string is a line from the file.
        """
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return [line.strip() for line in lines]
        except FileNotFoundError:
            self.logger_service.error(f"Error: The file at {self.source} was not found.")
            return []
        except IOError as e:
            self.logger_service.error(f"Error: An IOError occurred: {e}")
            return []

    def write(self, step_id, data) -> bool:
        if os.path.exists(self.path):
            self.path = self.get_new_filename(self.path)

        directory = os.path.dirname(self.path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        data['session_id'] = session_id
        data = self.filter_binary_data(data)
        if 'result' in data and 'response' in data['result']:
            data = data['result']['response']

        try:
            with open(self.path, 'w', encoding='utf-8') as file:
                json_string = json.dumps(data, indent=4)
                json_string = json_string.replace('\\n', '\n')
                file.write(json_string)
            return self.check_file_exists(self.path)
        except Exception as e:
            self.logger_service.error(f"Error: An IOError occurred: {e}")
