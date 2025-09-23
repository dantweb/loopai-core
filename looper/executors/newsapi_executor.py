##filepath:: ./loopai_src/core/looper/executors/newsapi_executor.py
from core.looper.executors.executor_interface import ExecutorInterface
from core.services.newsapi_service import NewsApiService


class NewsapiExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.news_api_service = NewsApiService()
        self.parent_step = None

    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        input_data = input_data[0][0]
        return input_data

    async def run(self, model, system_content, user_content, max_tokens) -> list:
        newsapi_response = self.news_api_service.get_fresh_headlines_by_topic(user_content, system_content, '', max_tokens)

        return newsapi_response


    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
