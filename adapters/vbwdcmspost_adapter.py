# ./src/adapters/vbwdcmspost_adapter.py
from core.adapters.file_adapter_interface import FileAdapterInterface
from core.models.broadcast_data import BroadcastData
from core.services.loopai_direct_vbwd_service import LoopAIDirectVbwdService

class VbwdcmspostAdapter(FileAdapterInterface):
    """vbwd CMS counterpart of ``WordpressAdapter``.

    Writes posts to a vbwd instance through the ``loopai-adapter`` plugin
    (classic ``/api/v1/loopai-adapter`` endpoints, ``X-API-Key`` auth) while
    keeping the WordPress adapter intact for backward compatibility.
    """

    def __init__(self,
                 connector_id: str,
                 vbwd_site: str = None,
                 vbwd_api_key: str = None
             ):

        self.connector_id = connector_id
        self.loopai_direct_vbwd_service = LoopAIDirectVbwdService(vbwd_site, vbwd_api_key)
        super().__init__()

    def read(self, step_id) -> list:
        all_posts = self.loopai_direct_vbwd_service.get_all_posts()
        return all_posts

    def write(self, step_id: str, data: BroadcastData) -> bool:
        return_from_vbwd = self.loopai_direct_vbwd_service.create_post(data)
        self.logger.log(f"[Class VbwdcmspostAdapter::write] data {str(return_from_vbwd)} ")
        print(f"[Class VbwdcmspostAdapter::write] data {str(return_from_vbwd)} ")

        # Handle None response (when service fails)
        if return_from_vbwd is None:
            self.logger.error("vbwd CMS API call failed - received None response")
            return False

        return True
