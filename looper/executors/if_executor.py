# src/looper/executors/if_executor.py
import importlib.util
import os
from core.looper.executors.executor_interface import ExecutorInterface


class IfExecutor(ExecutorInterface):
    def __init__(self, model: str):
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):
        # Not needed for IfExecutor
        pass

    async def run(self, model, system_content, user_content, max_tokens):
        try:
            # Dynamically import the module and function
            module_path = os.path.join(os.getcwd(), system_content['module_path'])
            spec = importlib.util.spec_from_file_location("module.name", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            func = getattr(module, system_content['function_name'])
            return func(user_content)
        except Exception as e:
            return {"result": str(e), "success": False}
