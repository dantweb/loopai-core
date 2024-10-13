from core.services.social_media_publisher_interface import SocialMediaPublisherInterface
from core.services.logger_service import LoggerService
from core.services.socialnetworks.blogspot_publisher import BlogspotPublisher
from core.services.socialnetworks.tumblr_publisher import TumblrPublisher
from core.services.socialnetworks.twitter_publisher import TwitterPublisher

logger = LoggerService()

class SMMService:
    social_networks_available = ['tumblr', 'twitter', 'blogspot']

    def __init__(self):
        self._social_networks_active = []

    @property
    def social_networks_active(self):
        return self._social_networks_active

    @social_networks_active.setter
    def social_networks_active(self, networks_list):
        # Validate that the networks are available before activating them
        valid_networks = [network for network in networks_list if network in self.social_networks_available]
        self._social_networks_active = valid_networks

    def publishAll(self, content: dict) -> bool:
        publishers = {
            'tumblr': TumblrPublisher(api_key='your_tumblr_api_key', blog_identifier='your_blog_identifier'),
            'twitter': TwitterPublisher(api_key='your_twitter_api_key', api_secret='your_api_secret', access_token='your_access_token'),
            'blogspot': BlogspotPublisher(api_key='your_blogspot_api_key', blog_id='your_blog_id')
        }

        success = True

        for network in self.social_networks_active:
            publisher = publishers.get(network)
            if publisher:
                try:
                    logger.info(f"Publishing to {network}")
                    if not publisher.publish(content):
                        logger.error(f"Failed to publish content on {network}")
                        success = False
                except Exception as e:
                    logger.error(f"Error publishing on {network}: {str(e)}")
                    success = False

        return success
