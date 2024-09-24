import csv
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import json
from tests.integration.wp_connection_test_parts.image_encoded64_examples import base64_images

# Load environment variables
load_dotenv()

WP_URL = os.getenv("WORDPRESS_URL")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APPLICATION_PASSWORD = os.getenv("WORDPRESS_PASSWORD")

auth = HTTPBasicAuth(WP_USERNAME, WP_APPLICATION_PASSWORD)


class WPCreatePostTest:
    def __init__(self):
        self.wp_site = WP_URL
        self.auth = auth

    def test_connection(self):
        url = f"{self.wp_site}/wp-json/"
        response = requests.get(url, auth=self.auth)
        assert response.status_code == 200, f"Connection failed: {response.status_code}"
        print("Connection successful")

    def test_create_post(self, post_data):
        url = f"{self.wp_site}/wp-json/loopai-direct-wpapi-plugin/v1/create-post"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, auth=self.auth, headers=headers, data=json.dumps(post_data))
        assert response.status_code == 200, f"Create post failed: {response.status_code}, {response.text}"
        print("Create post successful")
        print(response.content)

    def create_posts_from_csv(self, csv_file_path):

        for i in range(5):
            post_data = [
                {
                    "title": f"Dummy Title {i+1}",
                    "summary": f"Dummy Summary {i+1}",
                    "category": "Dummy Category",
                    "tags": "tag1,tag2",
                    "lead_paragraph": f"Dummy Lead Paragraph {i+1}",
                    "subtitle1": f"Dummy Subtitle1 {i+1}",
                    "subtitle2": f"Dummy Subtitle2 {i+1}",
                    "subtitle3": f"Dummy Subtitle3 {i+1}",
                    "paragraph1": f"Dummy Paragraph1 {i+1}",
                    "paragraph2": f"Dummy Paragraph2 {i+1}",
                    "paragraph3": f"Dummy Paragraph3 {i+1}",
                    "category": "dummy-category"
                },
                {
                    "model_id": "dall-e-2",
                    "step_id": f"loop_step2_{i+1}",
                    "prompt": f"Dummy Prompt1 {i+1}",
                    "image_file": "/tests/_data/generated/img/step2.jpg",
                    "image_base64": base64_images["image_11"]
                },
                {
                    "model_id": "dall-e-2",
                    "step_id": f"loop_step3_{i+1}",
                    "prompt": f"Dummy Prompt2 {i+1}",
                    "image_file": "/tests/_data/generated/img/step3.jpg",
                    "image_base64": base64_images["image_12"]
                },
                {
                    "model_id": "dall-e-2",
                    "step_id": f"loop_step4_{i+1}",
                    "prompt": f"Dummy Prompt3 {i+1}",
                    "image_file": "/tests/_data/generated/img/step4.jpg",
                    "image_base64": base64_images["image_13"]
                },
                {
                    "model_id": "dall-e-2",
                    "step_id": f"loop_step5_{i+1}",
                    "prompt": f"Dummy Prompt4 {i+1}",
                    "image_file": "/tests/_data/generated/img/step5.jpg",
                    "image_base64": base64_images["image_14"]
                }
            ]
            self.test_create_post(post_data)


# Create test instance
test_instance = WPCreatePostTest()

# Run the test
test_instance.test_connection()
test_instance.create_posts_from_csv("../_data/input/herbs.csv")
