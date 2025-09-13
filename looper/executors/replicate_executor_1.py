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
        # ... existing code ...
        final_prompt = BroadcastData(prompt_template)

        return final_prompt.to_json()

    async def run(self, model, system_content, user_content, max_tokens):
        img = self.generate_image_from_replicate(model, user_content)

        self.logger_service.info(f"[ReplicateExecutor::run] ReplicateExecutor response type: {type(result)}")

        result = BroadcastData({"image": img, "type": "image"})

        return result

    # ... existing code ...

    def _build_prompt(self, user_content: BroadcastData) -> str:
        """
        Build a safe, compact prompt string from user_content.
        """
        if isinstance(user_content, BroadcastData):
            try:
                return user_content.to_json()
            except Exception:
                try:
                    keys = list(user_content.data.keys()) if isinstance(user_content.data, dict) else []
                    return f"<BroadcastData keys={keys}>"
                except Exception:
                    return "<BroadcastData>"
        else:
            try:
                s = str(user_content)
                return s if len(s) <= 1000 else s[:1000]
            except Exception:
                return "<unrepresentable input>"

    def _call_replicate(self, client, model: str, prompt: str, width: int, height: int):
        """
        Calls replicate.Client.run and returns the raw output.
        Kept isolated for easier testing and single responsibility.
        """
        return client.run(
            model,
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
            }
        )

    def _extract_image_url(self, api_output):
        """
        Extract a usable image URL (string) from Replicate API output.

        Strategy:
        - If api_output is a list/tuple, try the first item and also search the whole structure.
        - Wrap output into BroadcastData and use its recursive finder to look for common keys
          like 'url', 'image', 'output', 'result' etc.
        - As a final fallback, inspect any top-level strings that look like an HTTP(S) URL.
        - Returns a single URL string or None.
        """
        # Quick guard
        if api_output is None:
            return None

        # If it's a simple string, check if it's an URL
        if isinstance(api_output, str):
            if api_output.startswith("http://") or api_output.startswith("https://"):
                return api_output
            return None

        # If it's a list/tuple, try the first element as a candidate
        first_candidate = None
        if isinstance(api_output, (list, tuple)) and len(api_output) > 0:
            first_candidate = api_output[0]

            # If the first candidate is a string URL, return it
            if isinstance(first_candidate, str) and (first_candidate.startswith("http://") or first_candidate.startswith("https://")):
                return first_candidate

        # Use BroadcastData to search recursively for likely URL fields
        try:
            bd = BroadcastData(api_output)
        except Exception:
            bd = None

        if bd is not None:
            # Common keys that may contain an URL
            candidate_keys = [
                "url", "image", "image_url", "output", "result", "file", "files", "artifact"
            ]

            # Search each key; bd.find_value_recursive_by_key returns list (possibly empty)
            for key in candidate_keys:
                matches = bd.find_value_recursive_by_key(key)
                if matches:
                    # matches is a list - iterate and pick first HTTP(S) looking string
                    for m in matches:
                        if isinstance(m, str) and (m.startswith("http://") or m.startswith("https://")):
                            return m
                        # if m is dict or BroadcastData, try to find url inside it
                        if isinstance(m, (dict, BroadcastData, list)):
                            nested = BroadcastData(m) if not isinstance(m, BroadcastData) else m
                            nested_matches = nested.find_value_recursive_by_key("url") or []
                            for nm in nested_matches:
                                if isinstance(nm, str) and (nm.startswith("http://") or nm.startswith("https://")):
                                    return nm

        # If first_candidate was an object with an attribute .url or .get('url'), try to extract
        if first_candidate is not None:
            # attribute access
            try:
                if hasattr(first_candidate, "url"):
                    url_val = getattr(first_candidate, "url")
                    if isinstance(url_val, str) and (url_val.startswith("http://") or url_val.startswith("https://")):
                        return url_val
            except Exception:
                pass
            # mapping-like access
            try:
                if isinstance(first_candidate, dict) and "url" in first_candidate:
                    url_val = first_candidate["url"]
                    if isinstance(url_val, str) and (url_val.startswith("http://") or url_val.startswith("https://")):
                        return url_val
            except Exception:
                pass
            # stringification fallback
            try:
                s = str(first_candidate)
                if s.startswith("http://") or s.startswith("https://"):
                    return s
            except Exception:
                pass

        # Last resort: perform a shallow scan of any strings inside api_output to find an http(s) substring
        def _scan_for_url(obj):
            if isinstance(obj, str):
                if "http://" in obj or "https://" in obj:
                    # return the first full substring starting at http[s]:// up to whitespace or quote
                    import re
                    m = re.search(r"https?://[^\s'\"\\]+", obj)
                    if m:
                        return m.group(0)
                    return None
                return None
            if isinstance(obj, dict):
                for v in obj.values():
                    r = _scan_for_url(v)
                    if r:
                        return r
            if isinstance(obj, (list, tuple)):
                for item in obj:
                    r = _scan_for_url(item)
                    if r:
                        return r
            # other types: ignore
            return None

        url = _scan_for_url(api_output)
        return url

    def _download_image(self, url: str, timeout: int = 30) -> Image.Image:
        """
        Download image bytes from URL and return a PIL Image. Ensures response is closed.
        """
        resp = requests.get(url, timeout=timeout)
        try:
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            img.load()  # force load to catch errors early
            return img
        finally:
            try:
                resp.close()
            except Exception:
                pass

    def generate_image_from_replicate(self, model, user_content, width: int = 1024, height: int = 1024):
        """
        Generate an image via Replicate and return a PIL.Image object.
        This method delegates small tasks to single-responsibility helpers:
          - _build_prompt
          - _call_replicate
          - _extract_image_url
          - _download_image

        It logs compact prompt previews and closes network responses to avoid resource warnings.
        """
        REPLICATE_API_TOKEN = session_manager.get_env('REPLICATE_API_TOKEN')
        client = replicate.Client(api_token=REPLICATE_API_TOKEN)

        prompt = self._build_prompt(user_content)
        self.logger_service.info(f"[ReplicateExecutor] Generating image with model: {model}")
        self.logger_service.info(f"[ReplicateExecutor] Prompt preview: {prompt[:200]}")
        self.logger_service.info(f"[ReplicateExecutor] Width: {width}, Height: {height}")

        try:
            output = self._call_replicate(client, model, prompt, width, height)
            self.logger_service.info(f"[ReplicateExecutor] API response: {output}")

            image_url = self._extract_image_url(output)
            if not image_url:
                raise ValueError("Invalid API response: No image URL or file output found in response.")

            self.logger_service.info(f"[ReplicateExecutor] Generated image URL: {image_url}")

            img = self._download_image(image_url, timeout=30)
            self.logger_service.info(f"[ReplicateExecutor] Image successfully downloaded and opened: {img}")

            return img

        except Exception as e:
            # Compact prompt preview for logging
            try:
                prompt_preview = prompt if isinstance(prompt, str) else "<prompt>"
                if len(prompt_preview) > 1000:
                    prompt_preview = prompt_preview[:1000] + "..."
            except Exception:
                prompt_preview = "<unrepresentable prompt>"

            self.logger_service.error(
                f"[ReplicateExecutor] Error during image generation: {e}. Prompt preview: {prompt_preview}"
            )
            raise
