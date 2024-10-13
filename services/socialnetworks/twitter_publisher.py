import requests
from core.services.logger_service import LoggerService
from core.services.socialnetworks.social_media_publisher_interface import SocialMediaPublisherInterface

logger = LoggerService()

class TwitterPublisher(SocialMediaPublisherInterface):
    def __init__(self, api_key: str, api_secret: str, access_token: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token

    def publish(self, content: dict) -> bool:
        url = "https://api.twitter.com/2/tweets"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'text': f"{content['title']}\n{content['text']}\n{content['url']}\n# {content['tags']}"
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            logger.info("Post successfully published on Twitter.")
            return True
        else:
            logger.error(f"Failed to publish post on Twitter. Status code: {response.status_code}")
            return False
