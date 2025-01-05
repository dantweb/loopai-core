# ./src/services/loopai_direct_wpapi_service.py
import os
import requests
import json
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from core.databus import global_vars
from core.models.broadcast_data import BroadcastData
from core.services.service_interface import ServiceInterface

load_dotenv()

DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")


class LoopAIDirectWPAPIService(ServiceInterface):
    def __init__(self,
                 wp_site=None,
                 wp_username=None,
                 wp_password=None
         ):
        super().__init__('LoopAIDirectWPAPIService')
        self.wp_site = wp_site or global_vars.WORDPRESS_URL
        self.wp_username = wp_username or global_vars.WORDPRESS_USERNAME
        self.wp_application_password = wp_password or global_vars.WORDPRESS_PASSWORD
        self.auth = HTTPBasicAuth(self.wp_username, self.wp_application_password)

    def create_post(self, data: BroadcastData) -> requests.Response:
        url = f"{self.wp_site}/wp-json/loopai-adapter/v1/create-post"
        headers = {'Content-Type': 'application/json'}


        if DEBUG_LEVEL == "DEBUG":
            self.logger.info(f"[LoopAIDirectWPAPIService::create_post] typeof='{type(data)}' : {str(data)}")


        # flatten_data = BroadcastData(data.flatten_data()) #we do this to have then proper jsonification of the data

        ## for debug only ---
        # self.save_post_to_text_file(data)

        # Send the data_to_send as JSON
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