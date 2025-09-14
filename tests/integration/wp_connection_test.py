import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import json


# Load environment variables
load_dotenv('WPCreatePostTest.env')

WP_URL = os.getenv("WORDPRESS_URL") or "https://wp-mysql:8085"
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APPLICATION_PASSWORD = os.getenv("WORDPRESS_PASSWORD")

auth = HTTPBasicAuth(WP_USERNAME, WP_APPLICATION_PASSWORD)


class WPCreatePostTest:
    def __init__(self):
        print("WP_URL :")
        print(WP_URL)
        print(WP_USERNAME)
        print(WP_APPLICATION_PASSWORD)
        self.wp_site = WP_URL
        self.auth = auth

    def test_connection(self):
        url = f"{self.wp_site}/wp-json/"
        response = requests.get(url, auth=self.auth)
        assert response.status_code == 200, f"Connection failed: {response.status_code}"
        print("Connection successful")

    def test_create_post(self):
        url = f"{self.wp_site}/wp-json/loopai-direct-wpapi-plugin/v1/create-post"
        headers = {'Content-Type': 'application/json'}
        data = [
            {
                "title": "Equisetum Arvense: A Natural Herb for Health and Beauty",
                "summary": "Equisetum arvense, commonly known as horsetail, is a versatile herb that offers numerous health and beauty benefits. In this article, we will explore the uses and advantages of incorporating this herb into your daily routine.",
                "category": "Flowers",
                "tags": ["flowers", "poison plants", "traditional medicine"],
                "lead_paragraph": "Originating from the USA, Equisetum arvense has been used for centuries in traditional medicine and beauty practices. With its high content of silica and antioxidants, it has become a popular choice for those seeking natural remedies.",
                "subtitle1": "Health Benefits of Equisetum Arvense 1",
                "subtitle2": "Beauty Benefits of Equisetum Arvense 2",
                "subtitle3": "How to Incorporate Equisetum Arvense into Your Routine 3",
                "paragraph1": "Equisetum arvense offers a range of health benefits. Its anti-inflammatory properties can help alleviate symptoms of conditions such as arthritis and urinary tract infections. Additionally, its diuretic properties make it effective in relieving bloating and water retention.",
                "paragraph2": "In the realm of beauty, Equisetum arvense has gained recognition for its ability to promote healthy hair, skin, and nails. The silica content in this herb strengthens hair follicles, reducing hair loss and promoting hair growth. It also improves collagen production, resulting in firmer and more youthful-looking skin.",
                "paragraph3": "Incorporating Equisetum arvense into your routine is easy. You can consume it as a tea, take it in supplement form, or apply it topically in the form of creams or lotions. Remember to consult with a healthcare professional before adding any new herbs or supplements to your routine.",
                "category": "healthcare-and-beauty"
            },
            {
                "model_id": "dall-e-2",
                "step_id": "loop_step2",
                "prompt": "prompt1",
                "image_file": "/tests/_data/generated/img/step2.jpg",
                "image_base64": base64_images["image_1"]
            },
            {
                "model_id": "dall-e-2",
                "step_id": "loop_step3",
                "prompt": "prompt2",
                "image_file": "/tests/_data/generated/img/step3.jpg",
                "image_base64": base64_images["image_2"]
            },
            {
                "model_id": "dall-e-2",
                "step_id": "loop_step4",
                "prompt": "prompt3",
                "image_file": "/tests/_data/generated/img/step4.jpg",
                "image_base64": base64_images["image_3"]
            },
            {
                "model_id": "dall-e-2",
                "step_id": "loop_step5",
                "prompt": "prompt4",
                "image_file": "/tests/_data/generated/img/step5.jpg",
                "image_base64": base64_images["image_4"]
            }
        ]

        response = requests.post(url, auth=self.auth, headers=headers, data=json.dumps(data))
        assert response.status_code == 200, f"Create post failed: {response.status_code}, {response.text}"
        print("Create post successful")
        print(response.content)


# Create test instance
test_instance = WPCreatePostTest()

# Run the test
test_instance.test_connection()
test_instance.test_create_post()
