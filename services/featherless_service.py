# ./loopai_src/core/services/featherless_service.py

import json
import os

from openai import OpenAI
from core.models.broadcast_data import BroadcastData
from dotenv import load_dotenv
from core.services.service_interface import ServiceInterface

load_dotenv()
FEATHERLESS_API_URL = os.getenv('FEATHERLESS_API_URL', 'featherless_url')
FEATHERLESS_API_KEY = os.getenv('FEATHERLESS_API_KEY', 'dummy_key')


class FeatherlessService(ServiceInterface):


    def __init__(self, model: str):
        super().__init__(model)
        self.client = OpenAI(
            base_url=FEATHERLESS_API_URL,
            api_key=FEATHERLESS_API_KEY,
            timeout=120
        )

    def get_response(self, model, system_content, user_content: BroadcastData, max_tokens):

        self.logger.info(f"[FeatherlessService::get_response] Requesting response from Featherless API...")
        self.logger.info(f"[FeatherlessService::get_response] typeof user_content: {type(user_content)}")
        self.logger.info(f"[FeatherlessService::get_response] user_content: {str(user_content)}")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": json.dumps(system_content)},
                    {"role": "user", "content": json.dumps(user_content.__json__())}
                ],
                max_tokens=max_tokens,
                timeout=120
            )

            result_content = response.model_dump()['choices'][0]['message']['content']

            self.logger.info(f"[FeatherlessService::get_response] Response received successfully: \n{str(result_content)}\n\n")

            return result_content

        except Exception as e:
            self.logger.error(f"[FeatherlessService::get_response] Error: {str(e)}")
            raise e


