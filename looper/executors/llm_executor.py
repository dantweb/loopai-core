# src/looper/executors/llm_executor.py
import json
import re
import pandas as pd
from config import is_valid_json
from core.databus import global_vars
from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.featherless_service import FeatherlessService

logger = LoggerService()


class LlmExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.featherless = FeatherlessService(model)

    def prepare_prompt(self, input_data: list, prompt_template: str):
        self.logger.info("[LlmExecutor::prepare_prompt] Preparing prompt for LLM...")

        if not input_data:
            raise ValueError("Input data is empty.")

        if isinstance(input_data[0], pd.DataFrame):
            request_content = input_data[0].to_dict(orient='records')
        else:
            request_content = input_data[0]

        prompt_template['requestContent'] = request_content
        self.logger.info(f"[LlmExecutor::prepare_prompt] Generated prompt_template: {prompt_template}")

        return prompt_template

    def run(self, model, system_content, user_content, max_tokens) -> BroadcastData:
        logger.info(f"[LlmExecutor::run] Calling LLM with model: {model}")

        valid_response = False
        count = 0
        response = None

        while not valid_response:
            count += 1
            response = self.send_prompt_to_llm(model, system_content, user_content, max_tokens)
            valid_response = is_valid_json(response) and count < 5

        if not is_valid_json(response) or count >= 5:
            self.logger.error(f"[LlmExecutor::run] Invalid JSON response from LLM")
            raise ValueError("Invalid JSON response from LLM")

        try:
            cleaned_response = self.clean_json_string(response)
            broadcast_data = BroadcastData(cleaned_response)

            self.logger.info(f"[LlmExecutor::run] Broadcast data created successfully: {str(broadcast_data)}")
        except json.JSONDecodeError as e:
            fixed_response = self.fix_json(response)
            if not is_valid_json(fixed_response):
                raise ValueError("Invalid JSON response from LLM")
            broadcast_data = BroadcastData(fixed_response)

        return broadcast_data

    def send_prompt_to_llm(self, model, system_content, user_content: BroadcastData, max_tokens):
        logger.info(f"[LlmExecutor::send_prompt_to_llm] Sending request to LLM service...")
        return self.featherless.get_response(model, system_content, user_content, max_tokens)


    @staticmethod
    def clean_json_string(json_string: str) -> str:
        # Remove any unwanted characters that might break JSON format
        json_string = re.sub(r'[^a-zA-Z0-9{}[\]":,.\s-]', '', json_string)

        # Ensure commas and braces are balanced
        json_string = json_string.replace(',}', '}').replace(',]', ']')

        # Check for unbalanced braces or brackets and try to fix them
        open_braces = json_string.count('{')
        close_braces = json_string.count('}')
        open_brackets = json_string.count('[')
        close_brackets = json_string.count(']')

        # Add missing braces or brackets
        if open_braces > close_braces:
            json_string += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            json_string = '{' * (close_braces - open_braces) + json_string

        if open_brackets > close_brackets:
            json_string += ']' * (open_brackets - close_brackets)
        elif close_brackets > open_brackets:
            json_string = '[' * (close_brackets - open_brackets) + json_string

        return json_string


    def fix_json(self, json_string: str) -> dict:
        try:
            # Attempt to load the JSON
            return json.loads(json_string)
        except json.JSONDecodeError:
            # If there's a decode error, apply additional cleaning
            json_string = self.clean_json_string(json_string)
            try:
                return json.loads(json_string)
            except json.JSONDecodeError as e:
                # If it still fails, raise a clear error or log it
                raise ValueError(f"Unable to fix JSON: {str(e)}")