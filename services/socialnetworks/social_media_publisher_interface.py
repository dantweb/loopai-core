from abc import ABC, abstractmethod


class SocialMediaPublisherInterface(ABC):
    @abstractmethod
    def publish(self, content: dict) -> bool:
        """
        Publish content to the respective social media platform.

        Args:
            content (dict): A dictionary containing title, text, URL, and tags.

        Returns:
            bool: True if the publishing is successful, otherwise False.
        """
        pass
