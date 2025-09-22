# src/looper/executors/gpt_executor_interface.py
from abc import ABC, abstractmethod
from typing import Any
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.session_dependent import SessionDependent


class ExecutorInterface(ABC, SessionDependent):
    @abstractmethod
    def __init__(self, model: str):
        SessionDependent.__init__(self)
        self.parent_step = None
        self.logger = LoggerService()
        self.logger_service = self.logger

    @abstractmethod
    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        pass

    @abstractmethod
    async def run(self,
            model,
            system_content,
            user_content,
            fine_tuning, *args: Any,
            **kwargs: Any) -> BroadcastData:
        pass

    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
