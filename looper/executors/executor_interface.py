# src/looper/executors/gpt_executor_interface.py
from abc import ABC, abstractmethod

from core.services.logger_service import LoggerService


class ExecutorInterface(ABC):
    @abstractmethod
    def __init__(self, model: str):
        self.parent_step = None
        self.logger_service = LoggerService()

    @abstractmethod
    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        pass

    @abstractmethod
    def run(self, model, system_content, user_content, max_tokens) -> str:
        pass

    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
