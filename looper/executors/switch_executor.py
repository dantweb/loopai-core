import replicate
import requests

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.models.step_model import load_executor_class
from core.services.logger_service import LoggerService


class SwitchExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.logger_service = LoggerService()


    def prepare_prompt(self, input_data: BroadcastData, prompt_template):
        return input_data


    def run(self, model, system_content, user_content, max_tokens):

        broadcast_data = BroadcastData(user_content)
        switch_generator = broadcast_data.find_value_recursive_by_key('switch_executor')
        switch = next(switch_generator, None)
        if switch is None:
            raise Exception("[SwtichExecutor] switch_executor is None.")

        executor_object = load_executor_class(switch)
        result = executor_object.run(
            model,
            system_content,
            user_content,
            max_tokens
        )

        if result == 'Suggestion failed.':
            raise Exception("Suggestion failed.")

        self.logger_service.info(f"[SwtichExecutor::run] SwtichExecutor response type: {type(result)}")

        return result
