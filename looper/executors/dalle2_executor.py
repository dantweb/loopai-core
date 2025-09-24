# src/looper/executors/dalle2_executor.py
import json
from io import BytesIO
import requests
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData

load_dotenv()

from core.services.logger_service import LoggerService
logger = LoggerService(component='core')

class Dalle2Executor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model

        current_session = self.get_current_session_manager()
        open_ai_sdk_api_key = current_session.get_env("OPENAI_API_KEY") if current_session else ''
        logger.debug(f"[DalleExecutor::__init__] open_ai_sdk_api_key: {open_ai_sdk_api_key}")
        self.client = OpenAI(api_key=open_ai_sdk_api_key)

    def prepare_prompt(self, input_data: BroadcastData, prompt_template):
        logger.info(f"[DalleExecutor::prepare_prompt] preparing prompt for GPT...")
        logger.info(f"[DalleExecutor::prepare_prompt] input_data: {input_data}")
        logger.info(f"[DalleExecutor::prepare_prompt] input_data type: {type(input_data)}")

        if input_data is None or input_data == '':
            raise Exception(f"[DalleExecutor::prepare_prompt] Input data is empty. Parent step {self.parent_step}")


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

    def run(self, model, system_content, user_content, fine_tuning = {}, **kwargs):
        result = self.generate_image_from_dalle(model, user_content)

        if result == 'Suggestion failed.':
            raise Exception("Suggestion failed.")

        self.logger.info(f"[DalleExecutor::run] DalleExecutor response type: {type(result)}")

        return result

    def generate_image_from_dalle(self, model, user_content, width: int = 1024, height: int = 1024):

        try:
            # Use the closest supported size
            supported_sizes = [(256, 256), (512, 512), (1024, 1024)]
            selected_size = min(supported_sizes, key=lambda s: abs(s[0] - width) + abs(s[1] - height))
            size_param = f"{selected_size[0]}x{selected_size[1]}"
            logger.log(f"[Dalle2Executor::generate_image_from_dalle] Creating image for prompt {str(user_content)} with ")
            logger.log(f"[Dalle2Executor::generate_image_from_dalle] size {size_param}")
            prompt = json.dumps(user_content.__json__())
            response = self.client.images.generate(
                model=model,
                prompt=prompt[:500],
                size=size_param,
                quality="standard",
                n=1,
            )
            self.logger.info(f"[dalle2_executor] Generated image response: {response}")
            image_url = response.data[0].url
            self.logger.info(f"[dalle2_executor] Generated image URL: {image_url}")
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))

            bd = BroadcastData()
            base64_encoded = bd.convert_to_base64(img)
            return BroadcastData({"image_base64": base64_encoded})
        except Exception as e:
            self.logger.error(f"Error during image generation: {str(e)} \n\n prompt was type {user_content} : {user_content}")
            return None
