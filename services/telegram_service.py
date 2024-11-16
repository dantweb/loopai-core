import os
from telegram import Bot
from dotenv import load_dotenv
from core.models.broadcast_data import BroadcastData
from core.services.service_interface import ServiceInterface

load_dotenv()

class LoopAIDirectTelegramService(ServiceInterface):


    def __init__(self, model: str, telegram_token=None, telegram_channel_id=None):
        super().__init__(model)
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_channel_id = telegram_channel_id or os.getenv('TELEGRAM_CHANNEL_ID')
        self.bot = Bot(token=self.telegram_token)

    ## data: Broadcast
    ## data.title: str
    ## data.content: str
    def create_post(self, data: BroadcastData):
        try:
            message = f"*{data.get('title')}*\n\n{data.get('content')}"
            self.bot.send_message(chat_id=self.telegram_channel_id, text=message, parse_mode='Markdown')
            self.logger.info(f"Message sent to Telegram channel: {self.telegram_channel_id}")
        except Exception as e:
            self.logger.error(f"Failed to send message to Telegram: {e}")
