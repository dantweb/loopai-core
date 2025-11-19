# src/adapters/filesystem_adapter.py
import json
import os

import app_global_config as config
from core.adapters.file_adapter_interface import FileAdapterInterface, write_to_fs_log
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.loop_path_resolver import loop_path_resolver

logger = LoggerService(component='core')

class FilesystemAdapter(FileAdapterInterface):

    def __init__(self, source: str):
        super().__init__()
        self.source = source
        self.base_path = config.LOOPAI_SINGLE_FILESYSTEM_PATH
        self.user_id = self.get_user_id()
        self.loop_id = self.get_loop_id()
        if config.WEB_OR_CLI == 'web':
            self.base_path = loop_path_resolver.get_file_system_by_user_and_loop(str(self.user_id), str(self.loop_id))

        self.logger.debug(f"[FilesystemAdapter::__init__] user_id: {self.user_id}, loop_id: {self.loop_id}")
        self.logger.debug(f"[FilesystemAdapter::__init__] base_path: {self.base_path}")

        self.absolute_path: str = self.base_path + self.source
        self.root_path = config.LOOPAI_ROOT


    def read(self, step_id, second_parameter=None) -> BroadcastData:
        self.logger.debug(f"[FilesystemAdapter::read] Starting read for step_id: {step_id}")
        self.logger.debug(f"[FilesystemAdapter::read] Second parameter: {second_parameter}")
        self.logger.debug(f"[FilesystemAdapter::read] Source: {self.source}")
        self.logger.debug(f"[FilesystemAdapter::read] Base path: {self.base_path}")
        self.logger.debug(f"[FilesystemAdapter::read] Absolute path: {self.absolute_path}")
        self.logger.debug(f"[FilesystemAdapter::read] Path exists: {os.path.exists(self.absolute_path)}")

        if not os.path.exists(self.absolute_path):
            self.logger.warning(f"[FilesystemAdapter::read] Directory does not exist: {self.absolute_path}")
            return BroadcastData({'result': []})

        file_paths = []
        file_count = 0

        for root, _, files in os.walk(self.absolute_path):
            self.logger.debug(f"[FilesystemAdapter::read] Walking directory: {root}")
            self.logger.debug(f"[FilesystemAdapter::read] Found {len(files)} files: {files}")

            for file in files:
                if '__pycache__' in root or '.git' in root or '.idea' in root or '.venv' in root or 'vendor' in root:
                    self.logger.debug(f"[FilesystemAdapter::read] Skipping ignored directory: {root}")
                    continue

                file_path = os.path.join(root, file)
                self.logger.debug(f"[FilesystemAdapter::read] Processing file: {file_path}")

                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            file_content = f.read()

                        relative_path = os.path.relpath(file_path, self.absolute_path)
                        file_paths.append({'code_dir': self.source,  'path': relative_path, 'file_content': file_content})
                        file_count += 1
                        self.logger.debug(f"[FilesystemAdapter::read] Successfully read file {file_count}: {relative_path} ({len(file_content)} chars)")

                    except Exception as e:
                        self.logger.error(f"[FilesystemAdapter::read] Error reading file {file_path}: {e}")
                else:
                    self.logger.warning(f"[FilesystemAdapter::read] Can't read file (not a file): {file_path}")

        self.logger.debug(f"[FilesystemAdapter::read] Total files read: {file_count}")
        self.logger.debug(f"[FilesystemAdapter::read] Returning BroadcastData with {len(file_paths)} files")

        return BroadcastData({'updated_files': file_paths})


    def write(self, step_id: str, data: BroadcastData) -> bool:
        self.logger.log("FilesystemAdapter::write:: trying to extract files")
        print("[FilesystemAdapter::write]:: trying to extract files")
        updated_files = data.find_value_recursive_by_key("updated_files")
        write_to_fs_log({"input_data": data})
        write_to_fs_log({"updated_files_found": updated_files})
        self.logger.log(f"FilesystemAdapter::write:: input data: {str(data)}")
        self.logger.log(f"FilesystemAdapter::write:: updated_files_found: {str(updated_files)}")
        self.logger.log(f"FilesystemAdapter::write:: total updated_files_found number: {len(updated_files)}")

        if not isinstance(updated_files, list):
            if isinstance(updated_files, dict) or isinstance(updated_files, BroadcastData):
                if 'path' in updated_files:
                    updated_files = [updated_files]
                else:
                    updated_files = []
            else:
                self.logger.error(f"[FilesystemAdapter::write] Adapter has not found any files to write.")
                return False

        # FIX: Properly unwrap nested list structure [[file1, file2, ...]] to [file1, file2, ...]
        # The find_value_recursive_by_key sometimes returns a list containing a list of files
        if isinstance(updated_files, list) and len(updated_files) == 1 and isinstance(updated_files[0], list):
            updated_files = updated_files[0]
            self.logger.log(f"FilesystemAdapter::write:: unwrapped nested list, now have {len(updated_files)} files")

        try:
            for file_info in updated_files:
                if isinstance(file_info, list) and 'path' in file_info[0]:
                    file_info = file_info[0]

                self.logger.log(f"FilesystemAdapter::write:: considering this entity as a file {file_info}")
                if isinstance(file_info, list):
                    self.logger.log(f"FilesystemAdapter::write:: considering this entity as a list {file_info}")
                    file_info = file_info[0]

                if not isinstance(file_info, dict):
                    self.logger.error(f"[FilesystemAdapter::write] File for loopID={self.loop_id} is not a dict: {file_info}")
                    write_to_fs_log({ "error": "wrong type"})
                    continue

                if 'path' not in file_info:
                    self.logger.error(f"[FilesystemAdapter::write] File for loopID={self.loop_id} does not have a path: {file_info}")
                    write_to_fs_log({ "error": "no path"})

                relative_file_path = file_info['path']
                file_operation = file_info.get('file_operation', 'update')
                file_content = file_info['file_content']
                file_path = os.path.join(self.absolute_path, relative_file_path)

                if not file_path.startswith(self.absolute_path) or ".." in file_path:
                    raise Exception(f"Attempted to write outside of code_dir: {self.absolute_path}")

                if file_operation == 'delete':
                    os.remove(file_path)
                    return True

                os.makedirs(os.path.dirname(file_path), exist_ok=True)


                with open(file_path, 'w') as f:
                    f.write(json.dumps(file_content))
                    self.logger.log(f"[FilesystemAdapter::write] File for loopID={self.loop_id} path={file_path} was saved successfully")

            return True
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")
            return False
