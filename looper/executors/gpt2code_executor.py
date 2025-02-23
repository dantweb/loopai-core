# src/looper/executors/gpt_executor.py
import json
import os

import openai
from dotenv import load_dotenv

from app_global_config import is_valid_json
from core.looper.executors.executor_interface import ExecutorInterface
from core.looper.executors.gpt_executor import GptExecutor

load_dotenv()


class Gpt2codeExecutor(GptExecutor):
    def prepare_prompt(self, input_data: list, prompt_template: str):
        request_content = input_data
        # Prepare the prompt based on input_data and the prompt_template
        prompt_template['requestContent'] = request_content #it was input_data[0] befoire
        return prompt_template

    def run(self, model, system_content, user_content, max_tokens):
        result = self.getResponseFromOpenAI(model, system_content, user_content, max_tokens)
        if result == 'Suggestion failed.':
            self.logger_service.log(json.dumps(result))
            raise Exception("Suggestion failed.")
        while not is_valid_json(result):
            max_tokens = round(max_tokens * 1.1)
            self.logger_service.log(f"increase tokens to {max_tokens}")
            if max_tokens > 4096:
                raise Exception(f"Too many tokens ({max_tokens})")
            result = self.getResponseFromOpenAI(model, system_content, user_content, max_tokens)

        json_result = json.loads(result)
        json_result['tokens_used'] = max_tokens

        return json_result
