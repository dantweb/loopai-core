# src/looper/executors/gpt_executor.py
import json
import requests
from io import BytesIO

import openai
from PIL import Image
from dotenv import load_dotenv
from openai import api_key

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.session import session_manager

load_dotenv()

from core.services.logger_service import LoggerService
logger = LoggerService()

class Dalle2Executor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model

        open_ai_sdk_api_key = (
                session_manager.get_env("USER_GPT_API_KEY")
                or session_manager.get_env("OPENAI_API_KEY")
                or session_manager.get_env("OPEN_AI_SDK_API_KEY")
        )

        self.openai = openai.OpenAI(api_key=open_ai_sdk_api_key)

    def prepare_prompt(self, input_data: BroadcastData, prompt_template):
        logger.info(f"[DalleExecutor::prepare_prompt] preparing prompt for GPT...")
        logger.info(f"[DalleExecutor::prepare_prompt] input_data: {input_data}")
        logger.info(f"[DalleExecutor::prepare_prompt] input_data type: {type(input_data)}")

        if input_data is None or input_data == '':
            raise Exception("Input data is empty.")


        if isinstance(input_data, BroadcastData):
            request_content_json = json.dumps(input_data.__json__())
        elif isinstance(input_data, str):
            request_content_json = input_data[:500]
        else:
            request_content_json = json.dumps(input_data)

        if request_content_json == '' or request_content_json is None or request_content_json == '{}':
            raise Exception("[dalle2_executor] Request content is empty.")

        prompt_template['requestContent'] = request_content_json
        logger.info(f"[DalleExecutor::prepare_prompt] generated prompt_template : {prompt_template}")
        return prompt_template

    def run(self, model, system_content, user_content, max_tokens):
        result = self.generate_image_from_dalle(model, user_content)

        if result == 'Suggestion failed.':
            raise Exception("Suggestion failed.")

        self.logger_service.info(f"[DalleExecutor::run] DalleExecutor response type: {type(result)}")

        return result

    def generate_image_from_dalle(self, model, user_content, width: int = 1024, height: int = 1024):

        try:
            # Use the closest supported size
            supported_sizes = [(256, 256), (512, 512), (1024, 1024)]
            selected_size = min(supported_sizes, key=lambda s: abs(s[0] - width) + abs(s[1] - height))
            size_param = f"{selected_size[0]}x{selected_size[1]}"
            self.logger_service.log(f"Creating image for prompt {str(user_content)} with ")
            self.logger_service.log(f"size {size_param}")
            prompt = json.dumps(user_content.__json__())
            response = openai.images.generate(
                model=model,
                prompt=prompt[:500],
                size=size_param,
                quality="standard",
                n=1,
            )
            self.logger_service.info(f"[dalle2_executor] Generated image response: {response}")
            image_url = response.data[0].url
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            return img
        except Exception as e:
            self.logger_service.error(f"Error during image generation: {str(e)} \n\n prompt was type {user_content} : {user_content}")
            return None
