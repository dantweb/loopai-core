# ./loopai_src/core/services/loopai_direct_wpapi_service.py
import os
from typing import Any, Optional, Coroutine

import aiohttp
import requests
import json

from aiohttp import ClientResponse
from dotenv import load_dotenv
from gevent import sleep
from requests.auth import HTTPBasicAuth
from core.models.broadcast_data import BroadcastData
from core.services.service_interface import ServiceInterface

load_dotenv()

DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")

class LoopAIDirectWPAPIService(ServiceInterface):
    DEFAULT_TIMEOUT = 10

    def __init__(self,
                 wp_site=None,
                 wp_username=None,
                 wp_password=None
         ):
        super().__init__('LoopAIDirectWPAPIService')
        self.wp_site = wp_site
        self.wp_username = wp_username
        self.wp_application_password = wp_password
        self.auth = HTTPBasicAuth(self.wp_username, self.wp_application_password)



    async def create_post(self, data: BroadcastData) -> Optional[ClientResponse]:
        url = f"{self.wp_site}/wp-json/loopai-adapter/v1/create-post"
        headers = {'Content-Type': 'application/json'}

        if DEBUG_LEVEL == "DEBUG":
            self.logger.info(f"[LoopAIDirectWPAPIService::create_post] typeof='{type(data)}' : {str(data)}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT)) as response:
                    if response.status != 200:
                        text = await response.text()
                        self.logger.error(
                            f"[HttpAdapter::_get_url_contents] HTTP error {response.status}: {text[:200]}..."
                        )
                        raise Exception(f"HTTP error: {response.status} - {text[:200]}...")
                    text = await response.text()
                    self.logger.info(f"[HttpAdapter::_get_url_contents] Success: {text[:100]}...")
                    return response
        except Exception as e:
            self.logger.error(f"Failed to create post: {response.status} - {response.text}")

        return None

        response = requests.post(url, auth=self.auth, headers=headers, json=data.__json__())
        if response.ok:
            self.logger.info(f"Post created successfully: {response}")
        else:
            self.logger.error(f"Failed to create post: {response.status_code} - {response.text}")

        return response


    def get_all_posts(self) -> list:
        url = f"{self.wp_site}/wp-json/wp/v2/posts"
        response = requests.get(url, auth=self.auth)
        if response.ok:
            self.logger.info(f"Posts retrieved successfully: {response}")
            return response.json()
        else:
            self.logger.error(f"Failed to retrieve posts: {response.status_code} - {response.text}")
            return []


    def save_post_to_text_file(self, data):
        path = "/app/var/filesystem/loopai_direct_wpapi_service_output.txt"
        json_string = json.dumps(data.__json__(), ensure_ascii=True)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(json_string)