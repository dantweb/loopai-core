#Filepath relative the core root[.]: ./loopai_src/core/services/technews_service.py
import ast

from dotenv import load_dotenv
from eventregistry import *
import feedparser

from core.databus import global_vars
from core.services.logger_service import LoggerService

from web.routes.filesystem import logger_service

load_dotenv()

class TechnewsService:

    def __init__(self):
        self.key = global_vars.NEWSAPI_API_KEY
        self.logger = LoggerService()


    def fetch_news_for_topic(self, first_parameter, topic, max_items=10) -> list:
        logger_service.info(f"[TechnewsService::fetch_news_for_topic]Fetching news for topic: {topic}")
        feeds = first_parameter.get(topic, [])
        logger_service.info(f"[TechnewsService::fetch_news_for_topic] Feeds: {str(feeds)}")
        news_items = []
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            logger_service.info(f"[TechnewsService::fetch_news_for_topic] parsing url: {feed_url}")
            for entry in feed.entries:
                new_entry = {'title': entry.title + '--- body --' + entry.summary if hasattr(entry, 'summary') else ''}
                news_items.append(new_entry)
                logger_service.info(f"News item: {entry.title}")
                if len(news_items) >= max_items:
                    break
            if len(news_items) >= max_items:
                break
        return news_items


    # Function to fetch latest news for all topics
    def fetch_news_for_all_topics(self, first_parameter, topics, max_items_per_topic=10) -> dict:
        self.logger.info(f"[TechnewsService::fetch_news_for_all_topics] first_parameter {str(first_parameter)}")
        self.logger.info(f"[TechnewsService::fetch_news_for_all_topics] Fetching news for all topics {str(topics)}")
        all_news = {}
        for topic in topics:
            all_news[topic] = self.fetch_news_for_topic(first_parameter, topic, max_items_per_topic)
        return all_news


    # first_parameter = ['ai', 'e_commerce', 'ai_medicine', 'ai_applications', 'e_payments']
    def get_fresh_headlines(self, first_parameter, second_parameter, connector_id, max_results):
        self.logger.info(f"[TechnewsService::get_fresh_headlines] first_parameter type {type(first_parameter)}: {first_parameter}")
        self.logger.info(f"[TechnewsService::get_fresh_headlines] second_parameter type{type(second_parameter)}: {second_parameter}")
        first_topic = self.fetch_news_for_all_topics(first_parameter, second_parameter, max_results)
        return first_topic

