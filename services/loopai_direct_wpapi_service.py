# ./src/services/loopai_direct_wpapi_service.py
import os
import requests
import json
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from core.databus import global_vars
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

    def create_post(self, data):
        url = f"{self.wp_site}/wp-json/loopai-direct-wpapi-plugin/v1/create-post"
        headers = {'Content-Type': 'application/json'}
        data_to_send = data['result']
        logger.info(f"[LoopAIDirectWPAPIService::create_post] data: {str(data_to_send[0])}")
        logger.info(f"[LoopAIDirectWPAPIService::create_post] data to send type: {type(data_to_send[0])}")
        response = requests.post(url, auth=self.auth, headers=headers, data=data_to_send[0].to_json())
        logger.info(f"[LoopAIDirectWPAPIService::create_post] response: {response}")
        if response.status_code == 200:
            return response
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
