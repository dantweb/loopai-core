# src/looper/executors/gpt_executor.py
import json
import os
import openai
import pandas as pd
from config import is_valid_json
from core.databus import global_vars
from core.looper.executors.executor_interface import ExecutorInterface


class GptExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.openai = openai.OpenAI(api_key=global_vars.USER_GPT_API_KEY)

    def prepare_prompt(self, input_data: list, prompt_template: str):
        if isinstance(input_data[0], pd.DataFrame):
            request_content = input_data[0].to_dict(orient='records')
        else:
            request_content = input_data[0]

        request_content_json = json.dumps(request_content)
        prompt_template['requestContent'] = request_content #it was input_data[0] before
        return prompt_template

    def run(self, model, system_content, user_content, max_tokens):
        result = self.getResponseFromOpenAI(model, system_content, user_content, max_tokens)
        if result == 'Suggestion failed.':
            self.logger_service.log(json.dumps(result))
            raise Exception("Suggestion failed.")
        while not is_valid_json(result):
            max_tokens = round(max_tokens * 1.14)
            if max_tokens > 4096:
                raise Exception(f"Too many tokens ({max_tokens})")
            result = self.getResponseFromOpenAI(model, system_content, user_content, max_tokens)

        json_result = json.loads(result)
        json_result['tokens_used'] = max_tokens

        return json_result

    def getResponseFromOpenAI(self, model, system_content, user_content, max_tokens):
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
            return result.choices[0].message.content
        except Exception as e:
            self.logger_service.error(f"Error during topic suggestion: {str(e)}")
            return "Suggestion failed."
