# src/looper/executors/gpt_executor.py
from dotenv import load_dotenv

from core.looper.executors.llm_executor import LlmExecutor

load_dotenv()

class Gpt2codeExecutor(LlmExecutor):
    def __init__(self, model: str):
        super().__init__(model)
        pass