# ./src/adapters/wordpress_adapter.py
from core.adapters.file_adapter_interface import FileAdapterInterface
from core.services.loopai_direct_wpapi_service import LoopAIDirectWPAPIService
from core.services.wordpress_service import WordPressService


class WordpressAdapter(FileAdapterInterface):

    def __init__(self, connector_id: str):
        self.connector_id = connector_id
        self.loopai_direct_wpapi_service = LoopAIDirectWPAPIService()
        # self.wordpress_service = WordPressService()
        super().__init__()

    def read(self, step_id) -> list:
        # all_posts = self.wordpress_service.get_all_posts()
        # return all_posts
        return []

    def write(self, step_id: str, data: list) -> bool:
        return_from_wp = self.loopai_direct_wpapi_service.create_post(data)
        self.logger_service.log(return_from_wp.text)
        return True if return_from_wp.status_code == 200 else False
