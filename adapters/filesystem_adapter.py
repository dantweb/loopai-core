# src/adapters/filesystem_adapter.py
import os
import app_global_config as config
from core.adapters.file_adapter_interface import FileAdapterInterface, get_file_system_by_user_and_loop
from core.models.broadcast_data import BroadcastData


class FilesystemAdapter(FileAdapterInterface):

    def __init__(self, source: str, global_user_id, global_loop_id):
        super().__init__()
        self.source = source
        self.base_path = config.LOOPAI_SINGLE_FILESYSTEM_PATH
        if config.WEB_OR_CLI == 'web':
            self.base_path = get_file_system_by_user_and_loop(global_user_id, global_loop_id)

        self.absolute_path: str = self.base_path + self.source
        self.root_path = config.LOOPAI_ROOT

    def read(self, step_id, second_parameter=None) -> BroadcastData:
        file_paths = []
        for root, _, files in os.walk(self.absolute_path):
            for file in files:
                if '__pycache__' in root or '.git' in root or '.idea' in root or '.venv' in root or 'vendor' in root:
                    continue
                file_path = os.path.join(root, file)

                if os.path.isfile(file_path):
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                else:
                    self.logger.log(f"Can't read file {file_path}")

                relative_path = os.path.relpath(file_path, self.absolute_path)
                file_paths.append({'path': relative_path, 'file_content': file_content})

        return BroadcastData({'result': file_paths})

    def write(self, step_id: str, data: BroadcastData) -> bool:
        if 'result' in data:
            if 'response' in data['result']:
                if 'updated_files' in data['result']['response']:
                    updated_files = data['result']['response']['updated_files']
                else:
                    updated_files = data['result']['response']
            if 'updated_files' in data['result']:
                updated_files = data['result']['updated_files']
        else:
            self.logger.error(data)
            raise Exception(f"no response in data result")

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
                with open(file_path, 'w') as f:
                    f.write(file_content)
                self.logger.log(f"File {file_path} was saved successfully")

            return True
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")
            return False
