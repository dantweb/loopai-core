import os
import requests
import json
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from core.services.wordpress_service import WordPressService

load_dotenv()


class LoopAITableWPAPIService:
    def __init__(self, wp_site=None, wp_username=None, wp_application_password=None):
        self.wordpress_service = WordPressService(wp_site, wp_username, wp_application_password)
        self.wp_site = wp_site or os.getenv("WP_URL_BASIC")
        self.wp_username = wp_username or os.getenv("WP_USER_2")
        self.wp_application_password = wp_application_password or os.getenv("WP_PASSWORD_2")
        self.auth = HTTPBasicAuth(self.wp_username, self.wp_application_password)

    def get_all_rows(self):
        url = f"{self.wp_site}/wp-json/loopai-wp-api-plugin/v1/rows"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def get_row_by_icd10code(self, icd10code):
        url = f"{self.wp_site}/wp-json/loopai-wp-api-plugin/v1/row/icd10/{icd10code}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def update_row(self, data):
        url = f"{self.wp_site}/wp-json/loopai-wp-api-plugin/v1/row"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, auth=self.auth, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def get_rows_unpublished(self):
        unpublished = []
        rows = self.get_all_rows()
        for row in rows:
            post_id = self.wordpress_service.get_post_id_by_meta('icd10code', row['icd10code'])
            if post_id is None:
                unpublished.append(row)

        return unpublished

    def delete_row(self, icd10code):
        url = f"{self.wp_site}/wp-json/loopai-wp-api-plugin/v1/row/delete/{icd10code}"
        response = requests.delete(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
