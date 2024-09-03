import configparser
from dataclasses import dataclass
from typing import Optional


@dataclass
# src/models/action_config.py
class ActionConfig:
    def __init__(self, model: str, prompt: str, system_content: str, max_tokens: int, config: Optional[str] = None, executor: Optional[str] = None):
        self.model = model
        self.prompt = prompt
        self.system_content = system_content
        self.max_tokens = max_tokens
        self.config = config
        self.executor = executor
