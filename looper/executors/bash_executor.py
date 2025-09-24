##filepath: ./loopai_src/core/looper/executors/bash_executor.py

import os
import subprocess
from core.looper.executors.executor_interface import ExecutorInterface
from core.services.loop_path_resolver import loop_path_resolver

class BashExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):
        return input_data

    def run_bash_on_host(self, script_path: str, working_dir: str):
        """
        Execute a bash script directly on the host using the specified working directory.
        """
        try:
            result = subprocess.run(
                ['bash', script_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # Timeout after 5 minutes
                cwd=working_dir  # Set the working directory for execution
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.CalledProcessError as e:
            print("Error executing bash script:")
            print(f"Return Code: {e.returncode}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return {
                'stdout': e.stdout,
                'stderr': e.stderr,
                'return_code': e.returncode,
                'error': str(e)
            }
        except subprocess.TimeoutExpired:
            return {
                'error': 'Bash script execution timed out',
                'return_code': -1
            }

    def run(self, model, system_content, user_content, fine_tuning, config, **kwargs):
        bash_script_path = config.get('bash_script_path')
        self.logger.log(f"Bash script path: {bash_script_path}")

        if not bash_script_path:
            raise ValueError("Bash script path not provided in the config.")

        full_script_path = loop_path_resolver.get_full_path(self.session_manager, bash_script_path)
        self.logger.log(f"Full script path: {full_script_path}")

        if not os.path.exists(full_script_path):
            raise ValueError("Bash script does not exist at the resolved path.")

        user_id = self.session_manager.get_user_id()
        loop_id = self.session_manager.get_loop_id()
        self.logger.log(f"User ID: {user_id}, Loop ID: {loop_id}")
        filesystem_path = loop_path_resolver.get_file_system_by_user_and_loop(user_id, loop_id)
        self.logger.log(f"Using filesystem root: {filesystem_path}")

        try:
            # Execute bash script synchronously
            return self.run_bash_on_host(full_script_path, filesystem_path)
        except Exception as e:
            self.logger.log(f"Execution error: {str(e)}")
            return {
                "result": str(e),
                "success": False
            }