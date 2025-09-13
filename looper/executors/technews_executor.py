# ./loopai_src/looper/executors/technews_executor.py

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.technews_service import TechnewsService
from core.services.logger_service import LoggerService

logger = LoggerService()

##TODO: Implement the TechnewsExecutor class - use USER_PROMPT and SYSTEM_PROMPT

class TechnewsExecutor(ExecutorInterface):
    def __init__(self, model: str):
        self.technews_service = TechnewsService()
        self.parent_step = None

    def prepare_prompt(self, input_data: list, prompt_template: str) -> str:
        ## Extract the first element from the list
        return prompt_template

    async def run(self, model, system_content, user_content, max_tokens) -> BroadcastData:
        newsapi_response = {
            'response': self.technews_service.get_fresh_headlines(
                system_content, user_content, '', max_tokens
            )
        }
        result = BroadcastData(newsapi_response)
        return result


    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
