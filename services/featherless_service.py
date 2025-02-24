import json
import os
import re
import time

from openai import OpenAI
from dotenv import load_dotenv

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.service_interface import ServiceInterface

load_dotenv()

FEATHERLESS_API_URL = os.getenv('FEATHERLESS_API_URL', 'featherless_url')
FEATHERLESS_API_KEY = os.getenv('FEATHERLESS_API_KEY', 'dummy_key')

class FeatherlessService(ServiceInterface):
    RETRY_ATTEMPTS = 5
    RETRY_DELAY = 5  # seconds

    def __init__(self, model: str):
        super().__init__(model)
        self.response = None
        self.logger = LoggerService()
        self.client = OpenAI(
            base_url=FEATHERLESS_API_URL,
            api_key=FEATHERLESS_API_KEY,
            timeout=120
        )

    def get_response(
        self,
        model: str,
        system_content: dict,
        user_content: BroadcastData,
        max_tokens: int
    ) -> str:
        self.logger.info("[FeatherlessService::get_response] Requesting response from Featherless API...")
        self.logger.info(f"[FeatherlessService::get_response] Type of user_content: {type(user_content)}")
        self.logger.info(f"[FeatherlessService::get_response] user_content: {user_content}")
        self.logger.info(f"[FeatherlessService::get_response] model: {model}")
        self.logger.info(f"[FeatherlessService::get_response] url: {os.getenv('FEATHERLESS_API_URL')}")

        last_exception = None
        for attempt in range(1, self.RETRY_ATTEMPTS + 1):
            self.logger.info(f"[FeatherlessService::get_response] Attempt {attempt} of {self.RETRY_ATTEMPTS}")
            try:

                self.response = self.fetch_response_with_retries(
                    self.client,
                    model,
                    system_content,
                    user_content,
                    max_tokens,
                    5,
                    10
                )

                self.logger.info(
                    f"[FeatherlessService::get_response] Get response successfully on attempt {attempt}: {self.response}"
                )

                # Extract and clean the response content.
                unfiltered = self.response.model_dump()['choices'][0]['message']['content']
                result_content = re.sub(
                    r'^```json\s*|\s*```$', '',
                    unfiltered, flags=re.MULTILINE
                )

                self.logger.info(
                    f"[FeatherlessService::get_response] Cleaned response content: {result_content}"
                )
                return result_content

            except Exception as e:
                self.logger.error(
                    f"[FeatherlessService::get_response] Attempt {attempt} failed with error: {str(e)}"
                )
                self.logger.error(f"[FeatherlessService::get_response] Problematic response: {str(self.response)}")
                self.logger.error("[FeatherlessService::get_response] No response available")
                last_exception = e

                if attempt < self.RETRY_ATTEMPTS:
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise last_exception

    def fetch_response_with_retries(self, client, model, system_content, user_content, max_tokens, max_retries, pause_time):
        """
        Repeats the API call X times with a pause if the response is empty.

        Parameters:
            client: API client instance.
            model: Chat model name.
            system_content: System message content.
            user_content: User message content.
            max_tokens: Max tokens allowed in response.
            max_retries: Number of maximum retries.
            pause_time: Pause time (in seconds) between retries.

        Returns:
            The response if successful, or None if none of the retries succeed.
        """
        for attempt in range(max_retries):
            try:
                # Make the request
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": json.dumps(system_content)},
                        {"role": "user", "content": json.dumps(user_content.__json__())}
                    ],
                    max_tokens=max_tokens,
                    timeout=120
                )

                # Check if response is not empty
                if response:
                    return response  # Return the response if valid

                # If empty, print a message and retry
                print(f"Attempt {attempt + 1}/{max_retries}: Empty response, retrying in {pause_time} seconds...")
                time.sleep(pause_time)

            except Exception as e:
                # Handle exceptions (e.g., network issues) and retry
                print(f"Attempt {attempt + 1}/{max_retries}: Error occurred: {e}. Retrying in {pause_time} seconds...")
                time.sleep(pause_time)

        # If all retries fail, return None
        print(f"All {max_retries} attempts failed. No valid response received.")
        return None
