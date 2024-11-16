# ./src/adapters/wordpress_adapter.py
from core.adapters.file_adapter_interface import FileAdapterInterface
from core.models.broadcast_data import BroadcastData
from core.services.loopai_direct_wpapi_service import LoopAIDirectWPAPIService

class WordpressAdapter(FileAdapterInterface):

    def __init__(self, connector_id: str):
        self.connector_id = connector_id
        self.loopai_direct_wpapi_service = LoopAIDirectWPAPIService()
        super().__init__()

    def read(self, step_id) -> list:
        all_posts = self.loopai_direct_wpapi_service.get_all_posts()
        return all_posts

    def write(self, step_id: str, data: BroadcastData) -> bool:
        return_from_wp = self.loopai_direct_wpapi_service.create_post(data)
        self.logger.log(f"[Class WordpressAdapter::write] data type {type(return_from_wp)} ")
        self.logger.log(f"[Class WordpressAdapter::write] data {str(return_from_wp)} ")
        return True if return_from_wp.status_code == 200 else False
