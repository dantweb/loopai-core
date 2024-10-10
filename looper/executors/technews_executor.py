# src/looper/executors/technews_executor.py
import json

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.newsapi_service import NewsApiService, extract_string_from_list
from core.services.technews_service import TechnewsService
from core.services.logger_service import LoggerService

logger = LoggerService()


class TechnewsExecutor(ExecutorInterface):
    def __init__(self, model: str):
        self.technews_service = TechnewsService()
        self.parent_step = None

    def prepare_prompt(self, input_data: list, prompt_template: str) -> str:
        ## Extract the first element from the list
        return input_data

    def run(self, model, system_content, user_content, max_tokens) -> BroadcastData:
        newsapi_response = {
            'response': self.technews_service.get_fresh_headlines(
                user_content, system_content, '', max_tokens
            )
        }
        result = BroadcastData(newsapi_response)
        return result


    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
