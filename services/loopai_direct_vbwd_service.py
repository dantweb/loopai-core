# ./loopai_src/core/services/loopai_direct_vbwd_service.py
import os
from typing import Optional

import requests
import json

from dotenv import load_dotenv
from requests import Response
from core.models.broadcast_data import BroadcastData
from core.services.service_interface import ServiceInterface

load_dotenv()

DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")

# vbwd instance + the User API Token (X-API-Key) that holds the
# ``loopai:posts:create`` scope. This is the vbwd-native counterpart of the
# WordPress service — same payloads, classic vbwd endpoints, token auth.
VBWD_SITE = os.getenv("VBWD_SITE", "https://loopai.local")
VBWD_API_KEY = os.getenv("VBWD_API_KEY", "")


class LoopAIDirectVbwdService(ServiceInterface):
    """Direct client for the vbwd ``loopai-adapter`` plugin.

    Backwards-compatible sibling of ``LoopAIDirectWPAPIService``: it sends the
    exact same ``BroadcastData`` body, but to the classic vbwd endpoints
    (``/api/v1/loopai-adapter/...``) and authenticates with the vbwd User API
    Token via the ``X-API-Key`` header instead of WordPress Basic-Auth.
    """

    DEFAULT_TIMEOUT = 10
    API_KEY_HEADER = "X-API-Key"

    def __init__(self,
                 vbwd_site=VBWD_SITE,
                 api_key=VBWD_API_KEY
         ):
        super().__init__('LoopAIDirectVbwdService')
        self.vbwd_site = vbwd_site
        self.api_key = api_key

    def _headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            self.API_KEY_HEADER: self.api_key,
        }

    def create_post(self, data: BroadcastData) -> Response:
        url = f"{self.vbwd_site}/api/v1/loopai-adapter/create-post"
        if DEBUG_LEVEL == "DEBUG":
            self.logger.info(f"[LoopAIDirectVbwdService::create_post] typeof='{type(data)}' : {str(data)}")

        # Send the data_to_send as JSON
        response = requests.post(url, headers=self._headers(), json=data.__json__())
        if response.ok:
            self.logger.info(f"Post created successfully: {response}")
        else:
            self.logger.error(f"Failed to create post: {response.status_code} - {response.text}")

        return response


    def get_all_posts(self) -> list:
        url = f"{self.vbwd_site}/api/v1/loopai-adapter/posts"
        response = requests.get(url, headers={self.API_KEY_HEADER: self.api_key})
        if response.ok:
            self.logger.info(f"Posts retrieved successfully: {response}")
            return response.json()
        else:
            self.logger.error(f"Failed to retrieve posts: {response.status_code} - {response.text}")
            return []

    def save_post_to_text_file(self, data):
        path = "/app/var/filesystem/loopai_direct_vbwd_service_output.txt"
        json_string = json.dumps(data.__json__(), ensure_ascii=True)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(json_string)
