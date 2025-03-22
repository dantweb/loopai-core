import json
from io import BytesIO
import replicate
import requests
from PIL import Image
from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.session import session_manager

from core.services.logger_service import LoggerService

class ReplicateExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.logger_service = LoggerService()

    def prepare_prompt(self, input_data: BroadcastData, prompt_template):
        self.logger_service.info(f"[ReplicateExecutor::prepare_prompt] preparing prompt for Replicate...")
        self.logger_service.info(f"[ReplicateExecutor::prepare_prompt] input_data: {input_data}")
        self.logger_service.info(f"[ReplicateExecutor::prepare_prompt] input_data type: {type(input_data)}")

        if input_data is None or input_data == '':
            raise Exception("Input data is empty.")

        if isinstance(input_data, BroadcastData):
            request_content_json = json.dumps(input_data.__json__())
        elif isinstance(input_data, str):
            request_content_json = input_data[:500]
        else:
            request_content_json = json.dumps(input_data)

        if request_content_json == '' or request_content_json is None or request_content_json == '{}':
            raise Exception("[ReplicateExecutor] Request content is empty.")

        prompt_template['requestContent'] = request_content_json
        self.logger_service.info(f"[ReplicateExecutor::prepare_prompt] generated prompt_template: {prompt_template}")
        return prompt_template

    def run(self, model, system_content, user_content, max_tokens):
        result = self.generate_image_from_replicate(model, user_content)

        if result == 'Suggestion failed.':
            raise Exception("Suggestion failed.")

        self.logger_service.info(f"[ReplicateExecutor::run] ReplicateExecutor response type: {type(result)}")

        return result

    def generate_image_from_replicate(self, model, user_content, width: int = 1024, height: int = 1024):
        REPLICATE_API_TOKEN = session_manager.get_env('REPLICATE_API_TOKEN')

        client = replicate.Client(api_token=REPLICATE_API_TOKEN)

        try:
            # Log the input parameters
            self.logger_service.info(f"[ReplicateExecutor] Generating image with model: {model}")
            self.logger_service.info(f"[ReplicateExecutor] User content: {user_content}")
            self.logger_service.info(f"[ReplicateExecutor] Width: {width}, Height: {height}")

            # Call the Replicate API
            output = client.run(
                model,
                input={
                    "prompt": str(user_content),  # Ensure the prompt is a string and truncate if necessary
                    "width": width,                    # Pass the requested width
                    "height": height,                  # Pass the requested height
                }
            )

            # Log the API response
            self.logger_service.info(f"[ReplicateExecutor] API response: {output}")

            # Check if the output is valid
            if not output or not isinstance(output, list) or not output[0]:
                raise ValueError("Invalid API response: No image URL found.")

            # Fetch the generated image URL
            image_url = output[0]  # Assuming the first item in the output is the image URL
            self.logger_service.info(f"[ReplicateExecutor] Generated image URL: {image_url}")

            # Download the image
            response = requests.get(image_url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Open the image using PIL
            img = Image.open(BytesIO(response.content))
            self.logger_service.info(f"[ReplicateExecutor] Image successfully downloaded and opened: {img}")

            return img

        except Exception as e:
            self.logger_service.error(
                f"Error during image generation: {str(e)} \n\n Prompt was type {type(user_content)} : {user_content}"
            )
            return None