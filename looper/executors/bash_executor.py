import os
import uuid
import subprocess
from dotenv import load_dotenv

from app_global_config import is_valid_json
from core.adapters.file_adapter_interface import FileAdapterInterface, get_full_path
from core.looper.executors.executor_interface import ExecutorInterface

load_dotenv()


class BashExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        # Default Docker image if not specified in config
        self.default_image = "python:3.10-slim"

    def prepare_prompt(self, input_data: list, prompt_template: str):
        return input_data

    def run_bash_in_container(self, image_name, script_host_path, script_container_path="/tmp/script.sh",
                              additional_args=""):
        # Generate unique container name
        container_name = f"temp_executor_{uuid.uuid4().hex[:8]}"

        try:
            # Mount the host's Docker socket and install Docker CLI
            docker_run_cmd = [
                "docker", "run", "-dit",
                "-v", "/var/run/docker.sock:/var/run/docker.sock",  # Mount Docker socket
                "-v", "$(which docker):/usr/bin/docker",  # Mount Docker CLI
                "--privileged",  # Give container privileged access
                "--name", container_name,
                image_name,
                "/bin/bash"
            ]

            # 1. Create and start a container with Docker socket access
            subprocess.run(docker_run_cmd, check=True)

            # 2. Ensure Docker is installed in the container
            install_docker_cmd = """
            # Install Docker CLI if not present
            if ! command -v docker &> /dev/null; then
                apt-get update && apt-get install -y docker.io
            fi
            """

            # 3. Copy the script into the container
            subprocess.run(
                ["docker", "cp", script_host_path, f"{container_name}:{script_container_path}"],
                check=True
            )

            # 4. Make the script executable and run it with Docker access
            exec_cmd = f"""
            {install_docker_cmd}
            chmod +x {script_container_path}
            {script_container_path} {additional_args}
            """

            result = subprocess.run(
                ["docker", "exec", container_name, "bash", "-c", exec_cmd],
                capture_output=True,
                text=True,
                check=True
            )

            # 5. Process and return output
            output = result.stdout.strip()
            return {
                "result": output,
                "stderr": result.stderr,
                "success": True
            }

        except subprocess.CalledProcessError as e:
            self.logger_service.log(f"Docker execution error: {e.stderr}")
            return {
                "result": str(e),
                "stderr": e.stderr,
                "success": False
            }

        finally:
            # 6. Clean up: Stop and remove the container
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )


    def run(self, model, system_content, user_content, fine_tuning, config):
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

        # Get Docker image from config, fallback to default
        docker_image = config.get('docker_image', self.default_image)

        # Additional arguments from config
        additional_args = config.get('additional_args', '')

        try:
            # Execute bash script in Docker container
            return self.run_bash_in_container(
                image_name=docker_image,
                script_host_path=command,
                additional_args=additional_args
            )

        except Exception as e:
            self.logger_service.log(f"Execution error: {str(e)}")
            return {
                "result": str(e),
                "success": False
            }
