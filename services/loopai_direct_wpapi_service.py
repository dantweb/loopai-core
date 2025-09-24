# ./loopai_src/core/services/loopai_direct_wpapi_service.py
import os
from traceback import print_tb
from typing import Any, Optional, Coroutine

import aiohttp
import requests
import json

from aiohttp import ClientResponse
from dotenv import load_dotenv
from requests import Response
from requests.auth import HTTPBasicAuth
from core.models.broadcast_data import BroadcastData
from core.services.service_interface import ServiceInterface

load_dotenv()

DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")

WP_SITE = os.getenv("WP_SITE", "https://loopai.local")
WP_USERNAME = os.getenv("WP_USERNAME", "username")
WP_APPLICATION_PASSWORD = os.getenv("WP_APPLICATION_PASSWORD", "password")

class LoopAIDirectWPAPIService(ServiceInterface):
    DEFAULT_TIMEOUT = 10

    def __init__(self,
                 wp_site=WP_SITE,
                 wp_username=WP_USERNAME,
                 wp_password=WP_APPLICATION_PASSWORD
         ):
        super().__init__('LoopAIDirectWPAPIService')
        self.wp_site = wp_site
        self.wp_username = wp_username
        self.wp_application_password = wp_password
        self.auth = HTTPBasicAuth(self.wp_username, self.wp_application_password)

    def create_post(self, data: BroadcastData) -> Response:
        url = f"{self.wp_site}/wp-json/loopai-adapter/v1/create-post"
        headers = {'Content-Type': 'application/json'}
        if DEBUG_LEVEL == "DEBUG":
            self.logger.info(f"[LoopAIDirectWPAPIService::create_post] typeof='{type(data)}' : {str(data)}")

        # Send the data_to_send as JSON
        response = requests.post(url, auth=self.auth, headers=headers, json=data.__json__())
        if response.ok:
            self.logger.info(f"Post created successfully: {response}")
        else:
            self.logger.error(f"Failed to create post: {response.status_code} - {response.text}")

        return response


    def get_all_posts(self) -> list:
        url = f"{self.wp_site}/wp-json/wp/v2/posts"
        response = requests.get(url, auth=HTTPBasicAuth(self.wp_username, self.wp_application_password))
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