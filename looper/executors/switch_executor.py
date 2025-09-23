##filepath: ./loopai_src/core/looper/executors/switch_executor.py

import json

import replicate
import requests

from core.looper.executors.executor_interface import ExecutorInterface
from core.looper.executors.gpt_executor import fix_json
from core.models.broadcast_data import BroadcastData
from core.models.step_model import load_executor_class
from core.services.logger_service import LoggerService


class SwitchExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):
        self.logger.info("[LlmExecutor::prepare_prompt] Preparing prompt for LLM...")

        if not input_data:
            raise ValueError("Input data is empty.")

        # if isinstance(input_data[0], pd.DataFrame):
        #     request_content = input_data[0].to_dict(orient='records')
        # else:
        #     request_content = input_data[0]
        request_content = input_data

        prompt_template['requestContent'] = request_content
        self.logger.info(f"[LlmExecutor::prepare_prompt] Generated prompt_template: {prompt_template}")

        return prompt_template


    async def run(self, model, system_content, user_content, max_tokens):

        broadcast_data_json = fix_json(json.loads(str(user_content.flatten_data())))
        self.logger.info(f"[SwtichExecutor::run] SwtichExecutor input type: {type(broadcast_data_json)}")
        broadcast_data = BroadcastData(broadcast_data_json)
        broadcast_data = broadcast_data.flatten_data()

        self.logger.info(f"[SwtichExecutor::run] SwtichExecutor broadcast_data type: {type(broadcast_data)}")
        self.logger.info(f"[SwtichExecutor::run] SwtichExecutor broadcast_data: {str(broadcast_data)}")

        switch_generator = broadcast_data.find_value_recursive_by_key('switch_executor')
        switch = next(switch_generator, None)
        if switch is None:
            raise Exception("[SwtichExecutor] switch_executor is None.")

        executor_object = load_executor_class(switch)
        self.logger.info(f"[SwtichExecutor::run] SwtichExecutor class {executor_object} is loaded")

        result = await executor_object.run(
            model,
            system_content,
            user_content,
            max_tokens
        )

        if result == 'Suggestion failed.':
            raise Exception("Suggestion failed.")

        self.logger.info(f"[SwtichExecutor::run] SwtichExecutor response type: {type(result)}")

        return result
