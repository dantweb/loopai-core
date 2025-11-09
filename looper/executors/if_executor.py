# src/looper/executors/if_executor.py
import importlib.util
import os
from core.looper.executors.executor_interface import ExecutorInterface


class IfExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):
        # Not needed for IfExecutor
        pass

    def run(self, model, system_content, user_content, fine_tuning, config, **kwargs):
        try:
            func = getattr(self.module, config['condition_func'])
            arguments_list = config['condition_func_args']
            self.logger.log(f"[IfExecutor::run] condition_func: {func} {str(arguments_list)}")
            return func(arguments_list, self.session_manager)
        except Exception as e:
            return {"result": str(e), "success": False}
