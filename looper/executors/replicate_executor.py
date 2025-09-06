import json
from io import BytesIO
from typing import Any

import requests
from PIL import Image
import replicate

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.session import session_manager


class ReplicateExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model
        self.logger_service = LoggerService()

    def prepare_prompt(self, input_data: BroadcastData, prompt_template):
        self.logger_service.info(f"[ReplicateExecutor::prepare_prompt] preparing prompt for GPT...")
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
        self.logger_service.info(f"[ReplicateExecutor::prepare_prompt] generated prompt_template : {prompt_template}")
        return prompt_template

    def run(self, model: str, system_content: dict, user_content: Any, max_tokens: int = 4096, **kwargs):
        """
        Run the executor: generate an image from replicate and return the PIL Image.
        """
        result = self.generate_image_from_replicate(model, user_content)

        return result

    def generate_image_from_replicate(self, model: str, user_content: Any, width: int = 1024, height: int = 1024):
        """
        Calls Replicate API to generate an image and returns a PIL.Image on success,
        otherwise returns None. Handles multiple possible response formats from
        replicate.Client.run (list of urls, list of FileOutput objects, dicts, etc).
        """
        REPLICATE_API_TOKEN = session_manager.get_env('REPLICATE_API_TOKEN')

        client = replicate.Client(api_token=REPLICATE_API_TOKEN)

        try:
            # Log the input parameters
            self.logger_service.info(f"[ReplicateExecutor] Generating image with model: {model}")
            self.logger_service.info(f"[ReplicateExecutor] User content type: {type(user_content)}")

            # Ensure prompt is a plain string. If user_content is a BroadcastData or dict, serialize safely and truncate.
            prompt_text = user_content.to_json() if isinstance(user_content, BroadcastData) else str(user_content)

            self.logger_service.info(f"[ReplicateExecutor] Final prompt (truncated): {str(prompt_text)[:500]}...")
            self.logger_service.info(f"[ReplicateExecutor] Width: {width}, Height: {height}")

            # Call the Replicate API
            output = client.run(
                model,
                input={
                    "prompt": prompt_text,
                    "width": width,
                    "height": height,
                }
            )

            self.logger_service.info(f"[ReplicateExecutor] Raw API response: {str(output)}")
            # Normalize output to a single URL string if possible
            image_url = None

            # If output is a list, prefer first non-empty element
            if isinstance(output, list):
                first = output[0] if len(output) > 0 else None
                candidate = first
            else:
                candidate = output

            # Candidate may be a replicate FileOutput object, dict, or a string (URL)
            # 1) If it has 'url' attribute (FileOutput), use it
            if candidate is not None and hasattr(candidate, "url"):
                image_url = candidate.url
            # 2) If candidate is a dict, try common paths
            elif isinstance(candidate, dict):
                # common shapes: {'url': '...'} or nested snippet/thumbnails or {'output': ['...']}
                if "url" in candidate and isinstance(candidate["url"], str):
                    image_url = candidate["url"]
                elif "output" in candidate and isinstance(candidate["output"], list) and candidate["output"]:
                    # assume list of urls
                    maybe = candidate["output"][0]
                    if isinstance(maybe, str):
                        image_url = maybe
                    elif hasattr(maybe, "url"):
                        image_url = maybe.url
                else:
                    # try snippet -> thumbnails -> maxres -> url (legacy shape)
                    try:
                        image_url = candidate.get("snippet", {}).get("thumbnails", {}).get("maxres", {}).get("url")
                    except Exception:
                        image_url = None
            # 3) If candidate is a plain string, assume it's a URL
            elif isinstance(candidate, str):
                image_url = candidate
            # 4) As a last resort, try converting candidate to str (some FileOutput print as url)
            else:
                try:
                    candidate_str = str(candidate)
                    if candidate_str.startswith("http"):
                        image_url = candidate_str
                except Exception:
                    image_url = None

            if not image_url:
                raise ValueError(f"Could not extract image URL from Replicate response: {repr(output)}")

            self.logger_service.info(f"[ReplicateExecutor] Resolved image URL: {image_url}")

            # Download the image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            requests.session().close()

            img = Image.open(BytesIO(response.content))
            img.load()

            self.logger_service.info(f"[ReplicateExecutor] Image successfully downloaded and opened: {img}")

            return img

        except Exception as e:
            # Log error with safe representation of user_content
            safe_content = None
            try:
                if isinstance(user_content, BroadcastData):
                    safe_content = user_content.to_json()[:1000]
                else:
                    safe_content = str(user_content)[:1000]
            except Exception:
                safe_content = "<unserializable content>"

            self.logger_service.error(
                f"Error during image generation: {str(e)} \n\n Prompt was type {type(user_content)} : {safe_content}"
            )
            return None