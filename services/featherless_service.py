# ./loopai_src/core/services/featherless_service.py

# from openai import OpenAI
#
# client = OpenAI(
#   base_url="https://api.featherless.ai/v1",
#   api_key="rc_a250b328f44aff98d14d875fa030a122b3ffc84424b86511e30132c554abce85",
# )
#
# response = client.chat.completions.create(
#   model='meta-llama/Meta-Llama-3.1-8B-Instruct',
#   messages=[
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "Hello!"}
#   ],
# )
# print(response.model_dump()['choices'][0]['message']['content'])


import json
from openai import OpenAI
import os

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService

from dotenv import load_dotenv

load_dotenv()
FEATHERLESS_API_KEY = os.getenv('FEATHERLESS_API_KEY', 'dummy_key')
FEATHERLESS_API_URL = os.getenv('FEATHERLESS_API_URL', 'featherless_url')

logger = LoggerService()

class FeatherlessService:
    def __init__(self, model: str):
        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key="rc_a250b328f44aff98d14d875fa030a122b3ffc84424b86511e30132c554abce85"
        )
        self.model = model

    def get_response(self, model, system_content, user_content: BroadcastData, max_tokens):
        logger.info(f"[FeatherlessService::get_response] Requesting response from Featherless API...")
        logger.info(f"[FeatherlessService::get_response] typeof user_content: {type(user_content)}")
        logger.info(f"[FeatherlessService::get_response] user_content: {str(user_content)}")
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": json.dumps(system_content)},
                    {"role": "user", "content": json.dumps(user_content.__json__())}
                ],
                max_tokens=max_tokens
            )
            result_content = response.model_dump()['choices'][0]['message']['content']
            logger.info(f"[FeatherlessService::get_response] Response received successfully: \n{result_content}\n\n")
            return result_content
        except Exception as e:
            logger.error(f"[FeatherlessService::get_response] Error: {str(e)}")
            raise e
