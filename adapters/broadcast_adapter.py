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

                    saved_data = row['data']

                    self.logger.info(f"[BroadcastAdapter::read] type of data : {type(saved_data)}")

                    # Prepare the broadcast data
                    broadcast_data = self.prepare_result(saved_data)

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
        Traverse a potentially nested dictionary (or JSON-like structure)
        using a '/'-delimited field path. If a value is encountered that is a string,
        try to parse it as JSON and continue traversal on the parsed object.
        """
        import json
        keys = field.split('/')

        self.logger.info(f"[BroadcastAdapter::get_nested_data] Starting with keys: {keys}")
        self.logger.info("[BroadcastAdapter::get_nested_data] Initial data structure:")
        describe_structure(data)

        def recurse(current_data, remaining_keys):
            self.logger.info(f"[BroadcastAdapter::get_nested_data] Current level data type: {type(current_data)}")
            self.logger.info(f"[BroadcastAdapter::get_nested_data] Remaining keys: {remaining_keys}")

            if not remaining_keys:
                self.logger.info("[BroadcastAdapter::get_nested_data] No remaining keys, returning current_data.")
                return current_data

            # If current_data is a string, try parsing it as JSON before proceeding
            if isinstance(current_data, str):
                self.logger.info(
                    f"[BroadcastAdapter::get_nested_data] Current data is a string: '{current_data[:50]}...' (truncated)")
                # Attempt to convert single quotes to double quotes (workaround)
                current_data = current_data.replace("'", '"')
                try:
                    current_data = json.loads(current_data)
                    self.logger.info("[BroadcastAdapter::get_nested_data] Successfully parsed string as JSON.")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON: {e}")
                    return None

            if not isinstance(current_data, dict):
                self.logger.error(f"Expected dict but got {type(current_data)}: {current_data}")
                return None

            key = remaining_keys[0]
            self.logger.info(
                f"[BroadcastAdapter::get_nested_data] Looking for key: '{key}' in current data keys: {list(current_data.keys())}")

            if key not in current_data:
                self.logger.error(f"Key '{key}' not found in current data: {current_data}")
                return None

            self.logger.info(f"[BroadcastAdapter::get_nested_data] Key '{key}' found. Descending deeper...")
            return recurse(current_data[key], remaining_keys[1:])

        return recurse(data, keys)

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

        bd = BroadcastData(input_data)

        # Get the nested data
        data = self.get_nested_data(bd.to_dict(), self.field)

        if isinstance(data, str):
            data = {self.field.split('/')[-1]: data}

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



def describe_structure(data, indent=0):
    """
    Recursively describe the structure of a dict (or other containers like lists).
    Prints out keys, types, and sizes where applicable.
    """
    prefix = '    ' * indent  # Indentation for readability

    if isinstance(data, dict):
        # It's a dictionary, iterate through its keys
        print(f"{prefix}* dict with {len(data)} keys:")
        for key, value in data.items():
            print(f"{prefix}  - Key: '{key}'")
            describe_structure(value, indent + 1)
    elif isinstance(data, list):
        # It's a list, show length and then describe each element's structure
        print(f"{prefix}* list of length {len(data)}:")
        # If you don't want to print info for every element (e.g., too large lists),
        # you can limit the iteration or just show a sample.
        for i, item in enumerate(data):
            print(f"{prefix}  - Index {i}:")
            describe_structure(item, indent + 2)
    else:
        # It's a simple value: int, float, str, bool, etc.
        # Show the type and size if it's a string
        if isinstance(data, str):
            size_info = f"(length {len(data)})"
        elif isinstance(data, (list, dict)):
            # handled above, but if we got here inadvertently, no special size needed
            size_info = ""
        else:
            # For numeric or boolean types, no size, just type
            size_info = ""
        print(f"{prefix}* {type(data).__name__} {size_info}: {data}")