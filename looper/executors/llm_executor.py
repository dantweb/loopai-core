# src/looper/executors/llm_executor.py
import json
import re
from app_global_config import is_valid_json
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

        # if isinstance(input_data[0], pd.DataFrame):
        #     request_content = input_data[0].to_dict(orient='records')
        # else:
        #     request_content = input_data[0]
        request_content = input_data

        prompt_template['requestContent'] = request_content
        self.logger.info(f"[LlmExecutor::prepare_prompt] Generated prompt_template: {prompt_template}")

        return prompt_template

    async def run(self, model, system_content, user_content, temperature=0.7, **kwargs) -> BroadcastData:
        logger.info(f"[LlmExecutor::run] Calling LLM with model: {model}")

        valid_response = False
        count = 0
        response = None

        while (not valid_response) and count < 10:
            response = await self.send_prompt_to_llm(model, system_content, user_content, temperature)
            valid_response = is_valid_json(response)
            if valid_response:
                count = 99
                self.logger.info(f"[LlmExecutor::run] Valid __first__ JSON response from LLM ! ")
            else:
                cleaned_response = self.clean_json_string(response)
                if is_valid_json(cleaned_response):
                    response = cleaned_response
                    valid_response = True
                    count = 99
                    self.logger.info(f"[LlmExecutor::run] Valid JSON response from LLM from __clean_json_string! ")
                else:
                    self.logger.error(f"[LlmExecutor::run] Invalid JSON response from LLM ... retrying ...")
                    user_content['error'] = ("Your response cannot be converted to a valid JSON." 
                                             "Please try again. Avoid using special or escaped symbols"
                                             "Keep it ASCII complient.")
                    self.logger.error(f"[LlmExecutor::run] content of system_content: {str(user_content)}")

                    count += 1

        if not (valid_response and count >= 5):
            self.logger.error(f"[LlmExecutor::run] Invalid JSON response from LLM")
            raise ValueError("Invalid JSON response from LLM")

        try:
            broadcast_data = BroadcastData(self.fix_json(response))
            self.logger.info(f"[LlmExecutor::run] Broadcast data created successfully 1 : {str(broadcast_data)}")

        except json.JSONDecodeError as e:
            fixed_response = self.fix_json(response)
            if not is_valid_json(fixed_response):
                raise ValueError("Invalid JSON response from LLM")
            broadcast_data = BroadcastData(fixed_response)

        return broadcast_data

    async def send_prompt_to_llm(self, model, system_content, user_content: BroadcastData, temperature=0.7):

        if temperature is None:
            temperature = 0.7

        # Ensure temperature is a float and within valid range
        try:
            temperature = float(temperature)
        except (TypeError, ValueError):
            temperature = 0.7

        # Clamp temperature between 0.0 and 1.0
        temperature = max(0.0, min(1.0, temperature))

        logger.info(f"[LlmExecutor::send_prompt_to_llm] Sending request to LLM service...")

        return await self.featherless.get_response(model, system_content, user_content, temperature)


    @staticmethod
    def clean_json_string(json_string: str) -> str:
        # Normalize whitespace
        json_string = re.sub(r'\s+', ' ', json_string).strip()

        # Remove unwanted characters that might break JSON format, excluding HTML tags
        json_string = re.sub(r'[^-a-zA-Z0-9{}[\]":,.\s<>/]', '', json_string)

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