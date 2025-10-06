## ./loopai_src/core/services/featherless_service.py
import json
import re
from time import sleep
from typing import Union, Any, Optional

from openai import OpenAI
from dotenv import load_dotenv

from app_global_config import is_valid_json
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.service_interface import ServiceInterface
from core.services.session_manager import session_manager
from web.services.json_helper import JsonHelper

load_dotenv()

class FeatherlessService(ServiceInterface):
    RETRY_ATTEMPTS = 5
    RETRY_DELAY = 5  # seconds

    def __init__(self, model: str):
        super().__init__(model)
        self.response = None
        self.logger = LoggerService()

    def get_response(
        self,
        model: str,
        system_content: dict,
        user_content: BroadcastData,
        temperature: float
    ) -> Union[Optional[str], Any]:
        session = session_manager
        self.logger.info("[FeatherlessService::get_response] Requesting response from Featherless API...")
        self.logger.info(f"[FeatherlessService::get_response] model: {model}")
        self.logger.info(f"[FeatherlessService::get_response] url: {session.get_env('FEATHERLESS_API_URL')}")

        featherless_url = session.get_env('FEATHERLESS_API_URL')
        featherless_key = session.get_env('FEATHERLESS_API_KEY')

        if not featherless_url or not featherless_key:
            raise ValueError(f"Missing Featherless API configuration: URL={featherless_url}, KEY={'set' if featherless_key else 'missing'}")

        open_ai_client = OpenAI(
            base_url=featherless_url,
            api_key=featherless_key,
            timeout=120
        )

        last_exception = None
        for attempt in range(1, self.RETRY_ATTEMPTS + 1):
            self.logger.info(f"[FeatherlessService::get_response] Attempt {attempt} of {self.RETRY_ATTEMPTS}")
            try:
                self.response = self.fetch_response_with_retries(
                    open_ai_client,
                    model,
                    system_content,
                    user_content,
                    temperature,
                    5,
                    2
                )

                self.logger.info(
                    f"[FeatherlessService::get_response] Get response successfully on attempt {attempt}: {str(self.response)}"
                )

                if hasattr(self.response, 'model_dump'):
                    unfiltered = self.response.model_dump()['choices'][0]['message']['content']

                    result_content = re.sub(
                        r'^```json\s*|\s*```$', '',
                        unfiltered, flags=re.MULTILINE
                    )

                    self.logger.info(
                        f"[FeatherlessService::get_response] Cleaned response content: {result_content}"
                    )
                else:
                    result_content = self.response.choices[0].message.content

                if len(result_content) == 0:
                    raise Exception("Empty LLM response")

                return result_content

            except Exception as e:
                self.logger.error(
                    f"[FeatherlessService::get_response] Attempt {attempt} failed with error: {str(e)}"
                    f"[FeatherlessService::get_response] Problematic response: {str(self.response)}"
                    f"[FeatherlessService::get_response] No response available\n\n"
                )
                last_exception = e

                if attempt < self.RETRY_ATTEMPTS:
                    sleep(self.RETRY_DELAY)
                else:
                    raise last_exception

    def fetch_response_with_retries(self, client, model, system_content, user_content, temperature, max_retries, pause_time):
        """
        Repeats the API call X times with a pause if the response is empty.

        Parameters:
            client: API client instance.
            model: Chat model name.
            system_content: System message content.
            user_content: User message content.
            temperature: Max tokens allowed in response.
            max_retries: Number of maximum retries.
            pause_time: Pause time (in seconds) between retries.

        Returns:
            The response if successful, or None if none of the retries succeed.
        """

        for attempt in range(max_retries):
            try:
                if "o3-mini" in model:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": json.dumps(system_content)},
                            {"role": "user", "content": user_content.to_json()}
                        ],
                        timeout=300,
                        response_format={"type": "json_object"}
                    )
                else:
                    # Make the request
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": json.dumps(system_content)},
                            {"role": "user", "content": user_content.to_json()}
                        ],
                        timeout=600,
                        temperature=temperature,
                        presence_penalty=0.5,  # Encourage new topics
                        frequency_penalty=0.5, # Reduce repetition
                        response_format={"type": "json_object"}
                    )

                # Check if response is not empty
                if response:
                    return response  # Return the response if valid

                # If empty, print a message and retry
                self.logger.info(f"Attempt {attempt + 1}/{max_retries}: Empty response, retrying in {pause_time} seconds...")
                sleep(pause_time)

            except Exception as e:
                # Handle exceptions (e.g., network issues) and retry
                self.logger.error(f"Attempt {attempt + 1}/{max_retries}: Error occurred: {e}. Retrying in {pause_time} seconds...")

        # If all retries fail, return None
        self.logger.info(f"All {max_retries} attempts failed. No valid response received.")
        return None