import os
import subprocess
from dotenv import load_dotenv

from core.adapters.file_adapter_interface import get_full_path, get_file_system_by_user_and_loop
from core.looper.executors.executor_interface import ExecutorInterface
from core.services.session import session_manager

load_dotenv()


class BashExecutor(ExecutorInterface):

    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        # Default Docker image if not specified in config
        self.default_image = "python:3.10-slim"


    def prepare_prompt(self, input_data: list, prompt_template: str):
        return input_data

    def run_bash_in_container(self, script_name, user_id: str, loop_id: str):
        # 1. Get the filesystem path for the specific user and loop
        filesystem_path = get_file_system_by_user_and_loop(user_id, loop_id)
        container_name = f'loop_{loop_id}'

        try:
            # 1. Create and start the container
            create_container_cmd = [
                'docker', 'run', '-d',  # Detached mode to keep container running
                '--name', container_name,
                '-v', f'{filesystem_path}/.:/var/www/filesystem',
                '-v', f'{filesystem_path}/.ssh:/root/.ssh',
                'alpine:latest',
                '/bin/sh', '-c', 'sleep infinity'  # Keep container running
            ]

            subprocess.run(create_container_cmd, check=True)

            # 2. Copy filesystem contents
            copy_filesystem_cmd = [
                'docker', 'cp',
                f'{filesystem_path}/.',
                f'{container_name}:/var/www/filesystem'
            ]
            subprocess.run(copy_filesystem_cmd, check=True)

            # 3. Run bash script inside the container
            run_script_cmd = [
                'docker', 'exec',
                container_name,
                '/bin/sh', '-c',
                f'''
                set -e
                apk add --no-cache bash git
                cd /var/www/filesystem/
                ls -la
                bash "{script_name}"
                '''
            ]

            # Execute the script and capture output
            result = subprocess.run(
                run_script_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5-minute timeout
            )

            copy_to_host_cmd = [
                'docker', 'cp',
                f'{container_name}:/var/www/filesystem/.',
                f'{filesystem_path}/.'
            ]
            subprocess.run(copy_to_host_cmd, check=True)

            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }

        except subprocess.CalledProcessError as e:
            # Detailed error handling
            print("Execution failed:")
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
                'error': 'Container execution timed out',
                'return_code': -1
            }
        finally:
            # Ensure container is removed
            subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)

    def run(self, model, system_content, user_content, fine_tuning, config, **kwargs):
        # Get bash script path
        bash_script_path = config.get('bash_script_path')
        self.logger_service.log(f"Bash script path: {bash_script_path}")

        if not bash_script_path:
            raise ValueError("Bash script path not provided in the config.")

        # Resolve full path of the script
        command = get_full_path(bash_script_path)
        self.logger_service.log(f"Full command path: {command}")

        if not os.path.exists(command):
            raise ValueError("Bash script path does not exist.")

        user_id = session_manager.get_user_id()
        loop_id = session_manager.get_loop_id()

        try:
            # Execute bash script in Docker container
            return self.run_bash_in_container(
                bash_script_path,
                user_id,
                loop_id
            )

        except Exception as e:
            self.logger_service.log(f"Execution error: {str(e)}")
            return {
                "result": str(e),
                "success": False
            }
