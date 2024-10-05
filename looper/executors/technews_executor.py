# src/looper/executors/technews_executor.py
from core.looper.executors.executor_interface import ExecutorInterface
from core.services.newsapi_service import NewsApiService, extract_string_from_list
from core.services.technews_service import TechnewsService


class TechnewsExecutor(ExecutorInterface):
    def __init__(self, model: str):
        self.technews_service = TechnewsService()
        self.parent_step = None

    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        input_data = input_data[0][0]
        return input_data

    def run(self, model, system_content, user_content, max_tokens) -> list:
        newsapi_response = self.technews_service.get_fresh_headlines(user_content, system_content, '', max_tokens)

        return newsapi_response


    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
