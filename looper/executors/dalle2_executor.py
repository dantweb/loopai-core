# src/looper/executors/gpt_executor.py
import json
import os
import requests
from io import BytesIO

import openai
from PIL import Image
from dotenv import load_dotenv
from core.databus import global_vars
from config import is_valid_json
from core.looper.executors.executor_interface import ExecutorInterface

load_dotenv()


class Dalle2Executor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.openai = openai.OpenAI(api_key=global_vars.USER_GPT_API_KEY)

    def prepare_prompt(self, input_data: list, prompt_template):
        request_content = input_data[0].to_json()
        # Prepare the prompt based on input_data and the prompt_template
        prompt_template = prompt_template.replace("{{DESCRIPTION}}", request_content)
        return prompt_template

    def run(self, model, system_content, user_content, max_tokens):
        result = self.generate_image_from_dalle(model, user_content)

        if result == 'Suggestion failed.':
            raise Exception("Suggestion failed.")

        return result

    def generate_image_from_dalle(self, model, formulated_prompt, width: int = 1024, height: int = 1024):
        try:
            # Use the closest supported size
            supported_sizes = [(256, 256), (512, 512), (1024, 1024)]
            selected_size = min(supported_sizes, key=lambda s: abs(s[0] - width) + abs(s[1] - height))
            size_param = f"{selected_size[0]}x{selected_size[1]}"
            self.logger_service.log(f"Creating image for {formulated_prompt} with ")
            response = openai.images.generate(
                model=model,
                prompt=formulated_prompt,
                size=size_param,
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            return img
        except Exception as e:
            self.logger_service.error(f"Error during image generation: {str(e)} \n\n promptf {formulated_prompt}")
            return None
