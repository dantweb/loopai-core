import json
import os
from typing import List, Any, Dict, Union, Set, Optional
from PIL.Image import Image

from core.adapters.adapter_interface import AdapterInterface
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.loop_path_resolver import loop_path_resolver


class FileAdapterInterface(AdapterInterface):
    filesystem_path: str = ''

    def __init__(self):
        super().__init__()
        self.file_mode = 'a'

    def set_append(self):
        self.file_mode = 'a'

    def set_replace(self):
        self.file_mode = 'w'

    def get_full_path(self, file_path_template: str) -> str:
        return loop_path_resolver.get_full_path(self.session_manager, file_path_template)

    def get_new_filename(self, filename: str) -> str:
        base, extension = os.path.splitext(filename)
        index = 1
        new_filename = f"{base}-{index}{extension}"
        # Increment the index until a non-existing file name is found
        while os.path.exists(new_filename):
            index += 1
            new_filename = f"{base}-{index}{extension}"
        filename = new_filename

        return filename

    def convert_to_json_recursively(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: self.convert_to_json_recursively(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.convert_to_json_recursively(element) for element in data]
        elif isinstance(data, str):
            try:
                return self.convert_to_json_recursively(json.loads(data))
            except (json.JSONDecodeError, TypeError):
                return data
        else:
            return data

    from PIL.Image import Image  # Make sure to import this at the top of your file

    def filter_binary_data(self, data) -> Any:
        """
        Recursively filters out binary data (e.g., images, bytes) from the data.
        Supports dicts, lists, and BroadcastData instances.
        """
        # Handle scalar values
        if isinstance(data, (str, int, float, bool, type(None))):
            return data

        # Handle binary data types
        elif isinstance(data, (bytes, bytearray, Image)):
            return None  # Filter out binary data

        # Handle dictionaries
        elif isinstance(data, dict):
            filtered_dict = {}
            for key, value in data.items():
                filtered_value = self.filter_binary_data(value)
                if filtered_value is not None:
                    filtered_dict[key] = filtered_value
            return BroadcastData(filtered_dict)

        # Handle lists
        elif isinstance(data, list):
            filtered_list = []
            for item in data:
                filtered_item = self.filter_binary_data(item)
                if filtered_item is not None:
                    filtered_list.append(filtered_item)
            return BroadcastData(filtered_list)

        # Handle BroadcastData instances
        elif isinstance(data, BroadcastData):
            filtered_data = self.filter_binary_data(data.data)
            return filtered_data

        # Handle any other types (filter them out)
        else:
            return None  # Filter out unrecognized types

    def check_file_exists(self, filename: str) -> bool:
        if os.path.exists(filename):
            self.logger.log(f"New file has been successfully saved: {filename}")
            return True
        else:
            msg = f"Failed to save image: {filename}"
            self.logger.error(msg)
            raise IOError(msg)


    def extract_data_to_write(self, data: Any, fields: List[str]) -> Optional[
        Union[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Extract data that contains the required fields.

        :param data: The input data which can be a dict, list, or any nested combination of both.
        :param fields: The required fields to find within the data.
        :return: The list of dictionaries or a dictionary containing the required fields.
        """
        bc = BroadcastData(data)
        found_items = []
        self._recursive_collect(bc.data, set(fields), found_items)
        found_items = self.remove_duplicates(found_items)
        return found_items


    def _recursive_collect(self, data: Any, required_fields: Set[str], found_items: List[Dict[str, Any]]) -> None:
        """
        Recursively search through the data to collect all items containing the required fields.

        :param data: The input data to search through, which can be dict, list, etc.
        :param required_fields: The required fields that need to be present in a dictionary.
        :param found_items: A list to collect all found valid dictionaries.
        """
        if isinstance(data, dict):
            # If the data is a dict, check if it contains the required fields
            if required_fields.issubset(data.keys()):
                self.logger.info(f"[extract_data_to_write::_recursive_collect] Found valid item: {data}")
                found_items.append(data)
            else:
                # Recursively search through the dictionary values
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        self._recursive_collect(value, required_fields, found_items)
        elif isinstance(data, list):
            # If the data is a list, recursively search through each item
            for item in data:
                if isinstance(item, (dict, list)):
                    self._recursive_collect(item, required_fields, found_items)

    def remove_duplicates(self, input_list: Optional[List[Dict[Any, Any]]]) -> List[Dict[Any, Any]]:
        """
        Remove duplicate dictionaries from the input list while preserving the original order.

        :param input_list: The list of dictionaries from which to remove duplicates.
        :return: A new list with duplicates removed, maintaining the original order.
        """
        if input_list is None:
            self.logger.warning("Input list is None; returning an empty list.")
            return []

        seen = set()
        output_list = []
        for item in input_list:
            # Convert the dictionary to a tuple of sorted items to make it hashable
            item_tuple = tuple(sorted(item.items()))
            if item_tuple not in seen:
                output_list.append(item)
                seen.add(item_tuple)
        return output_list


def clean_env_content(env_content: str) -> str:
    # Define the regex pattern to match comments (lines starting with `#` or those following a value)
    # Remove only `#` and everything after it on the same line.
    pattern = r"#.*"

    # Substitute all comments with an empty string
    import re
    cleaned_content = re.sub(pattern, "", env_content)

    # Remove empty lines or lines with only whitespaces
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())

    return cleaned_content


def write_to_fs_log(data):
    import json
    import os

    log_dir = "/app/var/tmp/log-dev"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "fs_out.log")

    logger = LoggerService()

    try:
        with open(log_file, "a") as f:
            json_data = json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)
            f.write(json_data)
    except Exception as e:
        logger.error(f"Error writing log data: {e}")
