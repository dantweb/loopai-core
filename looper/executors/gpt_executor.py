# src/looper/executors/gpt_executor.py
import json
import re
import os
import openai
import pandas as pd
from config import is_valid_json
from core.databus import global_vars
from core.looper.executors.executor_interface import ExecutorInterface
from core.services.logger_service import LoggerService

logger = LoggerService()

class GptExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.openai = openai.OpenAI(api_key=global_vars.USER_GPT_API_KEY)

    def prepare_prompt(self, input_data: list, prompt_template: str):
        logger.info(f"[GptExecutor::prepare_prompt] preparing prompt for GPT...")
        logger.info(f"[GptExecutor::prepare_prompt] input_data: {input_data}")

        if isinstance(input_data[0], pd.DataFrame):
            request_content = input_data[0].to_dict(orient='records')
        else:
            request_content = input_data[0]

        request_content_json = json.dumps(request_content)

        if request_content_json is None:
            request_content_json = request_content
            if request_content_json is None:
                raise Exception("Request content is empty.")

        prompt_template['requestContent'] = request_content #it was input_data[0] before
        return prompt_template

    def run(self, model, system_content, user_content, max_tokens):
        logger.info(f"[GptExecutor::run] ..going to call GPT with model: {model}, tkns {max_tokens}")
        result = self.getResponseFromOpenAI(model, system_content, user_content, max_tokens)

        self.logger_service.info(f"[GptExecutor::run] GPT response type: {type(result)}")
        self.logger_service.info(f"[GptExecutor::run] tokens used : {max_tokens}")
        self.logger_service.info(f"\n\n[GptExecutor::run] result:")
        self.logger_service.info(result)
        self.logger_service.info(f"\n\n[GptExecutor::run] end result...")

        try:
            cleaned_result = clean_json_string(result)
            json_result = json.loads(cleaned_result)
            self.logger_service.log(f"[GptExecutor::run] Result is a valid JSON !!!")
        except json.JSONDecodeError as e:
            json_result = fix_json(result)
            if not is_valid_json(result):
                raise Exception("Invalid JSON response from OpenAI")

        json_result['tokens_used'] = max_tokens

        return json_result

    def getResponseFromOpenAI(self, model, system_content, user_content, max_tokens):
        logger = LoggerService()
        logger.info(f"[GptExecutor::getResponseFromOpenAI] trying to get response from OpenAI...")
        try:
            result = self.openai.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": json.dumps(system_content)
                    },
                    {
                        "role": "user",
                        "content": json.dumps(user_content)
                    }
                ],
                max_tokens=max_tokens
            )
            self.logger_service.info(f"We have a response from OpenAI...")
            return result.choices[0].message.content
        except Exception as e:
            self.logger_service.error(f"Error during topic suggestion: {str(e)}")
            return "Suggestion failed."


def clean_json_string(json_string):
    # Remove problematic characters
    json_string = re.sub(r'[^a-zA-Z0-9_{}[\]":,.\s-]', '', json_string)
    return json_string

def fix_json(json_string):
    try:
        # Try to parse the JSON string
        return json.loads(json_string)
    except json.JSONDecodeError:
        logger.info(f"[GptExecutor::fix_json] JSONDecodeError: trying to fix json: {json_string}")
        cleaned_json_string = clean_json_string(json_string)
        try:
            # Try to parse the cleaned JSON string
            return json.loads(cleaned_json_string)
        except json.JSONDecodeError as e:
            # If it still fails, raise an error
            raise ValueError(f"Invalid JSON: {e}")
