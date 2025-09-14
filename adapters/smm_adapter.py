from core.adapters.adapter_interface import AdapterInterface  # Assuming this is the interface from your intro
from core.models.broadcast_data import BroadcastData
from core.services.socialnetworks_service import SMMService  # Import the SMMService we created earlier
from core.services.logger_service import LoggerService

logger = LoggerService()

class SMMAdapter(AdapterInterface):
    def __init__(self, source: str):
        super().__init__(source)
        self.smm_service = SMMService()  # Initialize the SMM service

    def get_input(self) -> str:
        # Method to retrieve input, if necessary. For now, return the source as the input.
        return self.source

    async def read(self, session_id: str, step_id: str) -> BroadcastData:
        # For now, this method is not necessary for the SMMAdapter
        # In a real-world scenario, it could read from a database or external source
        logger.info(f'[SMMAdapter::read] Reading data for session {session_id}, step {step_id}')
        return BroadcastData(result={})  # Placeholder

    async def write(self, step_id: str, data: BroadcastData) -> bool:
        """
        The write method should use the SMM service to publish the given broadcast data to the
        active social networks.
        """
        try:
            # Extracting relevant content from BroadcastData
            result = data.get('result', {})
            response = result.get('response', {})
            title = response.get('title', '')
            text = response.get('text', '')
            url = response.get('url', '')
            tags = response.get('tags', '')

            logger.info(f"[SMMAdapter::write] Preparing to publish content for step {step_id}")

            if not all([title, text, url, tags]):
                raise ValueError("One or more required fields are empty: title, text, url, tags")

            # Prepare the content dictionary in the format SMMService expects
            content = {
                'title': title,
                'text': text,
                'url': url,
                'tags': tags
            }

            # Call the SMMService to publish the content
            logger.info("[SMMAdapter::write] Sending content to SMMService")
            self.smm_service.publishAll(content)

            logger.info("[SMMAdapter::write] Successfully published content to social networks")
            return True

        except Exception as e:
            logger.error(f"[SMMAdapter::write] Failed to publish content: {e}")
            return False
