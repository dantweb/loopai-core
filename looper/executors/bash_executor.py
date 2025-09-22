import os
import subprocess
import asyncio
from core.adapters.file_adapter_interface import get_full_path, get_file_system_by_user_and_loop
from core.looper.executors.executor_interface import ExecutorInterface

class BashExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
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

    async def run_bash_on_host_async(self, script_path: str, working_dir: str):
        """
        Execute a bash script asynchronously using asyncio subprocess to avoid blocking the event loop.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                'bash', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            return {
                'stdout': stdout.decode('utf-8') if stdout else '',
                'stderr': stderr.decode('utf-8') if stderr else '',
                'return_code': process.returncode
            }

        except asyncio.TimeoutError:
            # Kill the process if it times out
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            return {
                'error': 'Bash script execution timed out',
                'return_code': -1
            }
        except Exception as e:
            return {
                'error': f'Bash script execution failed: {str(e)}',
                'return_code': -1
            }

    async def run(self, model, system_content, user_content, fine_tuning, config, **kwargs):
        bash_script_path = config.get('bash_script_path')
        self.logger_service.log(f"Bash script path: {bash_script_path}")

        if not bash_script_path:
            raise ValueError("Bash script path not provided in the config.")

        # Resolve the full path of the script using the provided helper
        full_script_path = get_full_path(bash_script_path)
        self.logger_service.log(f"Full script path: {full_script_path}")

        if not os.path.exists(full_script_path):
            raise ValueError("Bash script does not exist at the resolved path.")

        # Get filesystem path for the loop using SessionDependent methods
        user_id = self.get_user_id()
        loop_id = self.get_loop_id()
        self.logger_service.log(f"User ID: {user_id}, Loop ID: {loop_id}")
        filesystem_path = get_file_system_by_user_and_loop(user_id, loop_id)
        self.logger_service.log(f"Using filesystem root: {filesystem_path}")

        try:
            # Execute bash script using async subprocess to avoid blocking the event loop
            return await self.run_bash_on_host_async(full_script_path, filesystem_path)
        except Exception as e:
            self.logger_service.log(f"Execution error: {str(e)}")
            return {
                "result": str(e),
                "success": False
            }
