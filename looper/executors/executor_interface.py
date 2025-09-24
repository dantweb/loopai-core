# ./loopai_src/core/looper/executors/gpt_executor_interface.py
from abc import ABC, abstractmethod
from typing import Any
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.session_dependent import SessionDependent


class ExecutorInterface(SessionDependent):
    @abstractmethod
    def __init__(self):
        super().__init__()
        self.parent_step = None
        self.logger = LoggerService(component='core')

    @abstractmethod
    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        pass

    @abstractmethod
    def run(self,
            model,
            system_content,
            user_content,
            fine_tuning, *args: Any,
            **kwargs: Any) -> BroadcastData:
        pass

    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
