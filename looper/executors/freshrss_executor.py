# ./loopai_src/looper/executors/freshrss_executor.py

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.freshrss_service import FreshRssService
from core.services.logger_service import LoggerService

logger = LoggerService()

class FreshrssExecutor(ExecutorInterface):
    def __init__(self, model: str):
        self.freshrss_service = FreshRssService()
        self.parent_step = None

    def prepare_prompt(self, input_data: list, prompt_template: str) -> str:
        ## Extract the first element from the list
        return prompt_template

    async def run(self, model, system_content, user_content, fine_tuning) -> BroadcastData:
        newsapi_response = {
            'response': self.freshrss_service.get_fresh_headlines(
                system_content, user_content, '', fine_tuning
            )
        }
        result = BroadcastData(newsapi_response)
        return result

