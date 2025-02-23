import json
import os
import subprocess
from dotenv import load_dotenv

from app_global_config import is_valid_json
from core.adapters.file_adapter_interface import FileAdapterInterface, get_full_path
from core.looper.executors.executor_interface import ExecutorInterface

load_dotenv()


class BashExecutor(ExecutorInterface):
    def __init__(self, model: str):
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):
        # Prepare the command to be executed based on the input data and config
        return input_data

    def run(self, model, system_content, user_content, max_tokens, config):
        bash_script_path = config.get('bash_script_path')
        if not bash_script_path:
            raise ValueError("Bash script path not provided in the config.")

        command = get_full_path(bash_script_path)

        if not os.path.exists(command):
            raise ValueError("Bash script path does not exist.")

        try:
            self.logger_service.log(f"Executing command: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.logger_service.log(f"Command stdout: {result.stdout}")
            self.logger_service.log(f"Command stderr: {result.stderr}")
            self.logger_service.log(f"Command return code: {result.returncode}")
            return {
                "result": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {"result": str(e), "success": False}
