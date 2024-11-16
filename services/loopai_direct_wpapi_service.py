# ./src/services/loopai_direct_wpapi_service.py
import os
import requests
import json
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from core.adapters.file_adapter_interface import FileAdapterInterface
from core.adapters.text_adapter import TextAdapter
from core.databus import global_vars
from core.models.broadcast_data import BroadcastData
from core.services.wordpress_service import WordPressService
from core.services.logger_service import LoggerService

logger = LoggerService()

load_dotenv()


class LoopAIDirectWPAPIService:
    def __init__(self, wp_site=None, wp_username=None, wp_application_password=None):
        self.wp_site = wp_site or global_vars.WORDPRESS_URL
        self.wp_username = wp_username or global_vars.WORDPRESS_USERNAME
        self.wp_application_password = wp_application_password or global_vars.WORDPRESS_PASSWORD
        self.auth = HTTPBasicAuth(self.wp_username, self.wp_application_password)

    def create_post(self, data: BroadcastData):
        url = f"{self.wp_site}/wp-json/loopai-direct-wpapi-plugin/v1/create-post"
        headers = {'Content-Type': 'application/json'}

        logger.info(f"[LoopAIDirectWPAPIService::create_post] typeof='{type(data)}' : {str(data)}")

        text_adapter = TextAdapter('')

        data_to_send = text_adapter.extract_data_to_write(
            data.to_dict(), ['title', 'content', 'status', 'author', 'categories', 'tags']
        )

        # Send the data_to_send as JSON
        response = requests.post(url, auth=self.auth, headers=headers, json=data_to_send)
        if response.ok:
            logger.info(f"Post created successfully: {response.json()}")
        else:
            logger.error(f"Failed to create post: {response.status_code} - {response.text}")