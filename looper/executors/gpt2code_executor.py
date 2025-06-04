# src/looper/executors/gpt_executor.py
from dotenv import load_dotenv

from core.looper.executors.llm_executor import LlmExecutor
from core.models.broadcast_data import BroadcastData

load_dotenv()

class Gpt2codeExecutor(LlmExecutor):
    def __init__(self, model: str):
        super().__init__(model)
        pass


    def send_prompt_to_llm(self, model, system_content, user_content: BroadcastData, temperature=0.2):
        if temperature is None:
            temperature = 0.2

        # Ensure temperature is a float and within valid range
        try:
            temperature = float(temperature)
        except (TypeError, ValueError):
            temperature = 0.2

        # Clamp temperature between 0.0 and 1.0
        temperature = max(0.0, min(1.0, temperature))

        return self.featherless.get_response(model, system_content, user_content, temperature)
