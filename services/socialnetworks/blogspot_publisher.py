import requests
from core.services.logger_service import LoggerService

logger = LoggerService()

class BlogspotPublisher(SocialMediaPublisherInterface):
    def __init__(self, api_key: str, blog_id: str):
        self.api_key = api_key
        self.blog_id = blog_id

    def publish(self, content: dict) -> bool:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts/"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        data = {
            'title': content['title'],
            'content': content['text'],
            'labels': content['tags'].split(','),
            'url': content['url']
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info("Post successfully published on Blogspot.")
            return True
        else:
            logger.error(f"Failed to publish post on Blogspot. Status code: {response.status_code}")
            return False
