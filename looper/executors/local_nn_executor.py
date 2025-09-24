# src/looper/executors/local_nn_executor.py
from core.looper.executors.executor_interface import ExecutorInterface
from core.services.local_llm_service import LocalLLMService


class LocalNNExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model
        self.local_llm_service = LocalLLMService(model)

    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        return prompt_template.replace("{{input_data}}", str(input_data))

    def run(self, model: str, message: str, max_tokens: int) -> str:
        prompt = self.prepare_prompt(message, "{{input_data}}")
        response = self.local_llm_service.predict(prompt)
        return response
