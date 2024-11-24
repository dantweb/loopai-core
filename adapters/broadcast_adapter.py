# src/adapters/broadcast_adapter.py
import json
import re
import traceback
from typing import Any, Dict

from PIL.Image import Image
from psycopg2.extras import DictCursor

from core.adapters.file_adapter_interface import FileAdapterInterface
from core.services.session import session_id
from core.services.postgres_db_connect import get_db_cursor
from core.services.logger_service import LoggerService
from core.models.broadcast_data import BroadcastData


logger_service = LoggerService()


def try_extract_data(data):
    data_to_write = try_extract_data_with_fields(data)
    if data_to_write is None:
        data_to_write = try_extract_data_with_pattern(data)

    return data_to_write


class BroadcastAdapter(FileAdapterInterface):
    def __init__(self, source=None):
        super().__init__()
        self.source = source
        self.output_format = None
        self.field = None
        self.image_file = None

    def read(self, self_step_id: str, ref_step_id: str = '', ignore_read_status: bool = False) -> Any | None:
        logger_service.info(f"[BroadcastAdapter::read] Reading DB step {self_step_id} from step {ref_step_id}")
        if ignore_read_status:
            query = """
                    SELECT * FROM loopai_broadcast
                    WHERE sessionid = %s AND stepid = %s
                    """
        else:
            query = """
                SELECT * FROM loopai_broadcast
                WHERE sessionid = %s AND stepid = %s AND readby = ''
            """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, (session_id, ref_step_id))
                row = cursor.fetchone()
                self.logger.info(f"[BroadcastAdapter::read] row: {str(row)}")
                if row:
                    # Deserialize the `data` field if it's a JSON string
                    # Deserialize the `data` field if it's a JSON string
                    if 'data' in row and isinstance(row['data'], str):
                        try:
                            row['data'] = json.loads(row['data'])
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Error deserializing data field: {e}")
                            return None

                    # Validate structure
                    if self.field.split('/')[0] not in row['data']:
                        self.logger.error(
                            f"Expected top-level key '{self.field.split('/')[0]}' not found in data: {row['data']}")
                        return None

                    # Prepare the broadcast data
                    broadcast_data = self.prepare_result(row['data'])
                    self.logger.info(f"[BroadcastAdapter::read] row has data: {broadcast_data}")
                    self.mark_row_as_read(row, self_step_id)
                    return broadcast_data

                return None

        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error reading from database: {e}")
            return None

    def write(self, step_id: str, data: BroadcastData) -> bool:
        self.logger.info(f"[BroadcastAdapter::write] Writing to DB step '{step_id}': data type '{type(data)}'")
        self.logger.info(f"[BroadcastAdapter::write] data of type {type(data)} : '{data}'")

        # data_to_write = try_extract_data(data)
        data_to_write = BroadcastData({ 'saved': data })

        if data_to_write is None:
            raise Exception("Error: No data possible to extract to write.")

        try:
            with get_db_cursor() as cursor:
                query = """
                INSERT INTO loopai_broadcast (sessionid, stepid, data)
                VALUES (%s, %s, %s)
                """
                cursor.execute(
                    query,
                    (
                        session_id,
                        step_id,
                        json.dumps(data_to_write.__json__())
                    )
                )
                return True
        except Exception as e:
            traceback.print_exc()
            logger_service.error(f"Error writing to database: {e}")
            return False


    def setAdditionalParams(self, output_format: str, field: str):
        self.output_format = output_format
        self.field = field

    def get_nested_data(self, data, field):
        """
        Traverse a nested dictionary using a '/'-delimited field path.

        Args:
            data (dict): The dictionary to search.
            field (str): A '/'-delimited string of keys.

        Returns:
            Any: The value found at the given field path or None if not found.
        """
        keys = field.split('/')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                if self.logger:
                    self.logger.error(f"Key '{key}' not found in current data: {data}")
                return None
        return data

    def prepare_result(self, input_data):
        """
        Prepare the result by extracting data based on the field path.

        Args:
            input_data (dict): The input data.

        Returns:
            BroadcastData: An instance of BroadcastData containing the extracted data or None.
        """
        if not self.field:
            if self.logger:
                self.logger.error("Field path is not set.")
            return None

        # Get the nested data
        data = self.get_nested_data(input_data, self.field)

        # Return BroadcastData with the value
        return BroadcastData(data) if data else None


    def mark_row_as_read(self, row: Dict, step_id: str) -> None:
        # Implement your database deletion logic here
        # Example (assuming you have a database connection and a primary key field):
        try:
            # Assuming 'id' is the primary key in your row
            row_id = row['id'] if isinstance(row, dict) else row
            # Replace this with your actual database deletion logic
            with get_db_cursor() as cursor:
                query = "UPDATE loopai_broadcast SET readby = %s WHERE id = %s"
                cursor.execute(query, (step_id, row_id,))
                self.logger.info(f"Row with id {row_id} was marked as read by {step_id}.")
        except Exception as e:
            self.logger.error(f"An error occurred while deleting the row: {str(e)}")

    def delete_entries_by_session_id(self) -> None:
        # Method to delete all entries with the given session_id
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM loopai_broadcast WHERE sessionid = %s"
                cursor.execute(query, (session_id,))
                self.logger.info(f"All entries with session_id {session_id} have been deleted.")
        except Exception as e:
            self.logger.error(f"An error occurred while deleting entries: {str(e)}")


def try_extract_data_with_fields(data: BroadcastData) -> BroadcastData:
    data_to_write = None
    if 'result' in data and data.get('result') is not None:
        logger_service.info(f"[BroadcastAdapter::write] result : '{data.get('result')}'")
        logger_service.info(
            f"[BroadcastAdapter::write] type of result.response : \"{type(data.get('result'))}\"")
        data_to_write = data.get('result')

    if data_to_write is None and 'response' in data:
        data_to_write = data.get('response')
        return data_to_write

    if data_to_write is None and data.has('title'):
        data_to_write = data
        return BroadcastData(data_to_write)

    return BroadcastData(data)



def try_extract_data_with_pattern(broken_json):
    # Regular expression to extract the result.response or response.result data
    pattern = r"'result':\s*{\s*'response':\s*(\{[^}]*\}|\[[^\]]*\])"

    # Search for the pattern
    match = re.search(pattern, broken_json)

    if match:
        response_data = match.group(1)
        try:
            # Attempt to parse the extracted string as JSON
            structured_data = json.loads(response_data.replace("'", "\""))  # Replace single quotes with double quotes
            return structured_data
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
    else:
        print("No match found.")