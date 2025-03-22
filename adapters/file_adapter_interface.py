import json
import os
import app_global_config as config
from abc import ABC, abstractmethod
from typing import List, Any, AnyStr, Dict, Union, Set, Optional
from PIL.Image import Image

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.session import session_manager


class FileAdapterInterface(ABC):
    filesystem_path: str = ''

    def __init__(self):
        self.file_mode = 'a'
        self.logger = LoggerService()

    @abstractmethod
    def read(self, file_path: str) -> List[str]:
        pass

    @abstractmethod
    def write(self, file_path: str, data: List[str]) -> None:
        pass

    def set_append(self):
        self.file_mode = 'a'

    def set_replace(self):
        self.file_mode = 'w'


    def get_full_path(self, file_path_template: str) -> str:
        return get_full_path(file_path_template)


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
        self.logger.info(f"[extract_data_to_write] Searching for valid data with fields: {fields}")
        required_fields = set(fields)
        found_items = []

        # Use the recursive search to collect all valid items
        self._recursive_collect(data, required_fields, found_items)

        if not found_items:
            self.logger.error("[extract_data_to_write] No valid data found.")
            return None

        # Return the list of found items or a single dictionary if only one item found
        return found_items if len(found_items) > 1 else found_items[0]

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

def get_file_system_by_user_and_loop(user_id: str, loop_id: str):

    if config.WEB_OR_CLI == 'cli':
        path_root = config.LOOPAI_SINGLE_FILESYSTEM_PATH
    else:
        path_root = config.LOOPAI_WEB_USERS_FILESYSTEM_PATH

    path = os.path.join(
        path_root,
        str(user_id),
        'loops',
        str(loop_id),
        'filesystem'
    )
    return path


def get_loop_config_base_path_by_user_and_loop(user_id: str, loop_id: str):

    if config.WEB_OR_CLI == 'cli':
        path_root = config.LOOPAI_SINGLE_FILESYSTEM_PATH
    else:
        path_root = config.LOOPAI_WEB_USERS_FILESYSTEM_PATH

    path = os.path.join(
        path_root,
        str(user_id),
        'loops',
        str(loop_id),
        'config'
    )

    return path


def get_full_path(file_path_template: str) -> str:
    loop_index = session_manager.get_loop_index()
    step = session_manager.get_global_step_name()
    path = f"loop.{step}.{loop_index}"
    user_id = session_manager.get_user_id()
    loop_id = session_manager.get_loop_id()


    last_part_of_the_path: str = file_path_template.replace(
        '{{SESSION_ID}}', session_manager.get_session_id()[:8]
    ).replace(
        '{{FOREACH_STEP_UUID}}', str(loop_index)
    ).replace('{{PATH}}', path)

    base_path = get_file_system_by_user_and_loop(user_id, loop_id)

    full_path = base_path + last_part_of_the_path

    return full_path

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