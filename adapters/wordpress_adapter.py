# ./src/adapters/wordpress_adapter.py
from core.adapters.file_adapter_interface import FileAdapterInterface
from core.models.broadcast_data import BroadcastData
from core.services.loopai_direct_wpapi_service import LoopAIDirectWPAPIService

class WordpressAdapter(FileAdapterInterface):

    def __init__(self,
                 connector_id: str,
                 wp_site: str = None,
                 wp_username: str = None,
                 wp_application_password: str = None
             ):

        self.connector_id = connector_id
        self.loopai_direct_wpapi_service = LoopAIDirectWPAPIService(wp_site, wp_username, wp_application_password)
        super().__init__()

    async def read(self, step_id) -> list:
        all_posts = self.loopai_direct_wpapi_service.get_all_posts()
        return all_posts

    async def write(self, step_id: str, data: BroadcastData) -> bool:
        return_from_wp = await self.loopai_direct_wpapi_service.create_post(data)
        self.logger.log(f"[Class WordpressAdapter::write] data {str(return_from_wp)} ")
        print(f"[Class WordpressAdapter::write] data {str(return_from_wp)} ")
        return True if return_from_wp.status == 200 else False
