##filepath: #project_root#/loopai_src/core/looper/executors/lambda_executor.py
import json
import re
from app_global_config import is_valid_json
from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.services.featherless_service import FeatherlessService

logger = LoggerService(component='core')


class LambdaExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):

        return input_data

    async def run(self, model, system_content, user_content, temperature=0.7, **kwargs) -> BroadcastData:

        return user_content
