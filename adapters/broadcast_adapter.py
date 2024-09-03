# src/adapters/broadcast_adapter.py
import json
import traceback
from typing import Any, Dict

from PIL.Image import Image
from psycopg2.extras import DictCursor

from core.adapters.file_adapter_interface import FileAdapterInterface
from core.services.session import session_id
from core.services.postgres_db_connect import get_db_cursor


class BroadcastAdapter(FileAdapterInterface):
    def __init__(self, source=None):
        super().__init__()
        self.source = source
        self.output_format = None
        self.field = None
        self.image_file = None

    def read(self, ref_step_id: str, self_step_id: str = '', ignore_read_status: bool = False) -> Any | None:

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
                if row:
                    result = self.prepare_result(row)
                    self.mark_row_as_read(row, self_step_id)
                    return result
                return None

        except Exception as e:
            traceback.print_exc()
            self.logger_service.error(self, f"Error reading from database: {e}")
            return None

    def write(self, step_id: str, data: dict) -> bool:
        data = self.filter_binary_data(data)
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
                        json.dumps(data)
                    )
                )
                return True
        except Exception as e:
            traceback.print_exc()
            self.logger_service.error(f"Error writing to database: {e}")
            return False

    def setAdditionalParams(self, output_format: str, field: str):
        self.output_format = output_format
        self.field = field

    def prepare_result(self, row):
        converted_row = self.convert_to_json_recursively(row)

        if self.field is None or '/' not in self.field:
            raise Exception(f"{self.__class__} has no fields defined for splitting")

        splittedFields = self.field.split('/')

        # Traverse the nested fields
        requested_field = converted_row
        for field in splittedFields:
            if isinstance(requested_field, dict) and field in requested_field:
                requested_field = requested_field[field]
            else:
                continue
                # raise KeyError(f"Field '{field}' not found in the row")

        return requested_field

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
                self.logger_service.info(f"Row with id {row_id} was marked as read by {step_id}.")
        except Exception as e:
            self.logger_service.error(f"An error occurred while deleting the row: {str(e)}")

    def delete_entries_by_session_id(self) -> None:
        # Method to delete all entries with the given session_id
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM loopai_broadcast WHERE sessionid = %s"
                cursor.execute(query, (session_id,))
                self.logger_service.info(f"All entries with session_id {session_id} have been deleted.")
        except Exception as e:
            self.logger_service.error(f"An error occurred while deleting entries: {str(e)}")
