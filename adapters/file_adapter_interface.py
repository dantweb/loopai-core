import json
import os
import config
from abc import ABC, abstractmethod
from typing import List, Any, AnyStr
from core.databus import global_vars
from PIL.Image import Image

from core.services.logger_service import LoggerService
from core.services.session import session_id


class FileAdapterInterface(ABC):
    filesystem_path: str = ''

    def __init__(self):
        self.file_mode = 'a'
        self.logger_service = LoggerService()

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

    def filter_binary_data(self, data):
        filtered_data = {}
        for key, value in data.items():
            # Check for PIL Image objects
            if isinstance(value, Image):
                continue
            # Check for bytes or bytearray
            if isinstance(value, (bytes, bytearray)):
                continue
            # Add additional checks for image paths or URLs if needed
            filtered_data[key] = value
        return filtered_data

    def check_file_exists(self, filename: str) -> bool:
        if os.path.exists(filename):
            self.logger_service.log(f"Image saved successfully: {filename}")
            return True
        else:
            msg = f"Failed to save image: {filename}"
            self.logger_service.error(msg)
            raise IOError(msg)


def get_file_system_by_user_and_loop(user_id: str, loop_id: str):
    path = os.path.join(
        config.LOOPAI_WEB_USERS_FILESYSTEM_PATH,
        str(user_id),
        'loops',
        str(loop_id),
        'filesystem'
    )
    return path


def get_loop_config_base_path_by_user_and_loop(user_id: str, loop_id: str):
    path = os.path.join(
        config.LOOPAI_WEB_USERS_FILESYSTEM_PATH,
        str(user_id),
        'loops',
        str(loop_id),
        'config'
    )
    return path


def get_full_path(file_path_template: str) -> str:
    if not isinstance(global_vars.global_step_name, str) or not isinstance(global_vars.global_loop_index, str):
        raise ValueError("global step name must be a string and global loop index must be an str")

    path = f"loop.{global_vars.global_step_name}.{global_vars.global_loop_index}"

    last_part_of_the_path: str = file_path_template.replace(
        '{{SESSION_ID}}', session_id[:5]
    ).replace(
        '{{FOREACH_STEP_UUID}}', str(global_vars.global_loop_index)
    ).replace('{{PATH}}', path)

    base_path = config.LOOPAI_SINGLE_FILESYSTEM_PATH
    if config.WEB_OR_CLI == 'web':
        base_path = get_file_system_by_user_and_loop(config.GLOBAL_USER_ID, config.GLOBAL_LOOP_ID)

    full_path = base_path + last_part_of_the_path

    return full_path
