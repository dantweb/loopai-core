# ./loopai_src/core/services/service_interface.py

import json
from openai import OpenAI
import os

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService

from dotenv import load_dotenv

load_dotenv()
FEATHERLESS_API_URL = os.getenv('FEATHERLESS_API_URL', 'featherless_url')
FEATHERLESS_API_KEY = os.getenv('FEATHERLESS_API_KEY', 'dummy_key')

class ServiceInterface:

    def __init__(self, model: str):
        self.logger = LoggerService()
        self.model = model
        pass

    def get_response(self, model, system_content, user_content: BroadcastData, max_tokens):
        pass



