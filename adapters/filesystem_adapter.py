# src/adapters/filesystem_adapter.py
import json
import os

import app_global_config as config
from core.adapters.file_adapter_interface import FileAdapterInterface, get_file_system_by_user_and_loop, write_to_fs_log
from core.models.broadcast_data import BroadcastData
from core.services.session import session_manager


class FilesystemAdapter(FileAdapterInterface):

    def __init__(self, source: str):
        super().__init__()
        self.source = source
        self.base_path = config.LOOPAI_SINGLE_FILESYSTEM_PATH
        self.user_id = session_manager.get_user_id()
        self.loop_id = session_manager.get_loop_id()
        if config.WEB_OR_CLI == 'web':
            self.base_path = get_file_system_by_user_and_loop(self.user_id, self.loop_id)

        self.logger.debug(f"[FilesystemAdapter::__init__] user_id: {self.user_id}, loop_id: {self.loop_id}")
        self.logger.debug(f"[FilesystemAdapter::__init__] base_path: {self.base_path}")

        self.absolute_path: str = self.base_path + self.source
        self.root_path = config.LOOPAI_ROOT


    async def read(self, step_id, second_parameter=None) -> BroadcastData:
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
                        file_paths.append({'path': relative_path, 'file_content': file_content})
                        file_count += 1
                        self.logger.debug(f"[FilesystemAdapter::read] Successfully read file {file_count}: {relative_path} ({len(file_content)} chars)")

                    except Exception as e:
                        self.logger.error(f"[FilesystemAdapter::read] Error reading file {file_path}: {e}")
                else:
                    self.logger.warning(f"[FilesystemAdapter::read] Can't read file (not a file): {file_path}")

        self.logger.debug(f"[FilesystemAdapter::read] Total files read: {file_count}")
        self.logger.debug(f"[FilesystemAdapter::read] Returning BroadcastData with {len(file_paths)} files")

        return BroadcastData({'result': file_paths})


    async def write(self, step_id: str, data: BroadcastData) -> bool:
        self.logger.log("FilesystemAdapter::write:: trying to extract files")
        print("[FilesystemAdapter::write]:: trying to extract files")
        updated_files = self.extract_files(data)
        write_to_fs_log({"input_data": data.data})
        write_to_fs_log({"updated_files_found": updated_files})
        self.logger.log(f"FilesystemAdapter::write:: input data: {str(data.data)}")
        try:
            for file_info in updated_files:
                relative_file_path = file_info['path']
                file_operation = file_info.get('file_operation', 'update')
                file_content = file_info['file_content']
                file_path = os.path.join(self.absolute_path, relative_file_path)

                if not file_path.startswith(self.absolute_path):
                    raise Exception(f"Attempted to write outside of code_dir: {self.absolute_path}")

                if file_operation == 'delete':
                    os.remove(file_path)

                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                if not isinstance(file_content, str):
                    write_to_fs_log({ "error": "wrong content type"})


                with open(file_path, 'w') as f:
                    f.write(json.dumps(file_content))
                    self.logger.log(f"File {file_path} was saved successfully")

            return True
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")
            return False


    def find_updated_files(self, data, parent_key=None):
        """
        Recursive function to locate all occurrences of 'updated_files'.
        """
        if isinstance(data, BroadcastData):
            data = data.to_dict()

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "updated_files" and isinstance(value, list):
                    self.logger.debug(f"Found 'updated_files' under key '{parent_key or 'root'}'")
                    yield from value  # Yield all items
                else:
                    write_to_fs_log({"found type of item": str(type(value))})
                    yield from self.find_updated_files(value, parent_key=key)

        elif isinstance(data, list):
            for item in data:
                yield from self.find_updated_files(item, parent_key)


    def extract_files(self, broadcast_data: BroadcastData):
        # Validate that broadcast data isn't empty
        if not broadcast_data.data:
            self.logger.error("Broadcast data is empty. No files to extract.")
            return []

        extracted_files = []
        found = self.find_updated_files(broadcast_data.data)
        for file_data in found:
            # Validate individual file entries
            if not isinstance(file_data, dict):
                self.logger.error(f"Skipping invalid file_data: {file_data}")
                continue

            # Ensure mandatory fields: `path` and `file_content`
            if "path" not in file_data or "file_content" not in file_data:
                self.logger.error(f"Skipping file_data without required fields: {file_data}")
                continue

            # Path normalization and safety validation
            path = file_data.get("path")
            norm_path = os.path.normpath(path)

            if norm_path.startswith("..") or os.path.isabs(norm_path):
                self.logger.error(f"Suspicious path detected (skipping): {path}")
                continue


            self.logger.log(f"Valid file_data extracted: {file_data}")
            extracted_files.append(file_data)

        self.logger.info(f"Total files extracted: {len(extracted_files)}")
        return extracted_files
