import requests
from core.services.logger_service import LoggerService
from core.services.socialnetworks.social_media_publisher_interface import SocialMediaPublisherInterface

logger = LoggerService()

class TumblrPublisher(SocialMediaPublisherInterface):
    def __init__(self, api_key: str, blog_identifier: str):
        self.api_key = api_key
        self.blog_identifier = blog_identifier

    def publish(self, content: dict) -> bool:
        url = f"https://api.tumblr.com/v2/blog/{self.blog_identifier}/post"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        data = {
            'type': 'text',
            'title': content['title'],
            'body': content['text'],
            'tags': content['tags'],
            'source_url': content['url']
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            logger.info("Post successfully published on Tumblr.")
            return True
        else:
            logger.error(f"Failed to publish post on Tumblr. Status code: {response.status_code}")
            return False
