# src/adapters/text_adapter.py
import os
import json
from core.adapters.file_adapter_interface import FileAdapterInterface
from typing import List
from core.models.broadcast_data import BroadcastData

from core.services.session_manager import session_manager


class TextAdapter(FileAdapterInterface):
    def __init__(self, source: str):
        super().__init__()
        self.source = source
        self.path = self.get_full_path(self.source)


    async def read(self, p1: str, p2: str, ignore_read_status: bool = False, *args) -> BroadcastData:
        """
        Reads a text file and attempts to parse it as JSON.
        If parsing succeeds, returns a BroadcastData with the parsed data.
        If parsing fails, returns a BroadcastData with 'text' containing the file content.
        Also adds 'source' and 'filename' fields to the BroadcastData.

        :param p1: Parameter 1 (unused in this context).
        :param p2: Parameter 2 (unused in this context).
        :param ignore_read_status: Flag to ignore read status.
        :param args: Additional arguments (if any).
        :return: BroadcastData instance with the read data.
        """

        self.logger.info(f"[TextAdapter::read] Reading data from file: {self.path}")
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                content = file.read()

            self.logger.info(f"[TextAdapter::read] Content: {content}")
            # try:
            #     # Attempt to parse the content as JSON
            #     data_dict = json.loads(content)
            #     self.logger.info("Successfully parsed JSON from the file.")
            # except json.JSONDecodeError:
            #     # Parsing failed, treat content as plain text
            #     self.logger.warning("Failed to parse JSON. Treating content as plain text.")
            #     data_dict = {'text': content}

            data_dict = {'text': content}

            self.logger.info(f"[TextAdapter::read] Data type read: {type(data_dict)}")
            broadcast_data = BroadcastData(data_dict)

            # Add 'source' and 'filename' fields
            broadcast_data.set('source', self.__class__.__name__)
            broadcast_data.set('filename', os.path.basename(self.path))

            return broadcast_data

        except FileNotFoundError:
            self.logger.error(f"Error: The file at {self.source} was not found.")
            return BroadcastData()
        except IOError as e:
            self.logger.error(f"Error: An IOError occurred: {e}")
            return BroadcastData()

    async def write(self, step_id: str, data: BroadcastData) -> bool:
        """
        Writes the content of BroadcastData to a text file in JSON format.

        :param step_id: Identifier for the current step.
        :param data: BroadcastData instance containing the data to write.
        :return: True if the file was written successfully, False otherwise.
        """

        self.logger.info(f"[TextAdapter::write] Writing data to file: {self.path}")
        self.logger.info(f"[TextAdapter::write] Data: {str(data)}")
        self.logger.info(f"[TextAdapter::write] Data type: {type(data)}")
        path: str = self.path
        directory: str = os.path.dirname(path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        # Add session_id to the data
        data.set('session_id', session_manager.get_session_id())

        # Filter binary data if needed
        data_filtered: BroadcastData = self.filter_binary_data(data)
        self.logger.info(f"[TextAdapter::write] Filtered data type: {type(data)}")
        self.logger.info(f"[TextAdapter::write] Filtered data : {str(data)}")
        self.logger.info(f"[TextAdapter::write] Filtered data properties : {data.properties}")

        data_to_write = data_filtered

        if data_to_write is None:
            raise Exception("Error: No data to write.")

        self.logger.info(f"[TextAdapter::write] going to write extracted data : {data_to_write} to file {path}")

        try:
            with open(path, 'w', encoding='utf-8') as file:
                json_string = json.dumps(data_to_write.__json__(), ensure_ascii=True)
                json_string = json_string.replace('\\n', '\n')
                file.write(json_string)

            self.logger.info(f"[TextAdapter::write] Data has been successfully saved to the file: {path}")
            return self.check_file_exists(path)
        except Exception as e:
            self.logger.error(f"Error: An IOError occurred: {e}")
            return False