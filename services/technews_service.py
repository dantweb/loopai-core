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
        logger_service.info(f"[TechnewsService::fetch_news_for_topic] Fetching news for topic: {topic}")
        feeds = first_parameter.get(topic, [])
        logger_service.info(f"[TechnewsService::fetch_news_for_topic] Feeds: {str(feeds)}")
        news_items = []

        for feed_url in feeds:
            logger_service.info(f"[TechnewsService::fetch_news_for_topic] Parsing URL: {feed_url}")
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:

                # Extract fields with a priority: content:encoded > description > summary
                content_encoded = entry.get('content', [{}])[0].get('value') if 'content' in entry else None
                description = entry.description if hasattr(entry, 'description') else None
                summary = entry.summary if hasattr(entry, 'summary') else None

                # Use content:encoded if available, fall back to description or summary
                # disabled for now becouse to much content for llm in dec.2024
                # content_body = content_encoded or description or summary or ''
                content_body =  description or summary or ''
                content = f"{entry.title}<content_body>{content_body}</content_body>"

                # Add to news items
                new_entry = {'title': entry.title, 'content': content}
                news_items.append(new_entry)
                # Break if max items are reached
                if len(news_items) >= max_items:
                    logger_service.info("[TechnewsService::fetch_news_for_topic] Reached max items limit.")
                    break

            if len(news_items) >= max_items:
                break

        logger_service.info(f"[TechnewsService::fetch_news_for_topic] Total news items fetched: {len(news_items)}")
        return news_items

    # Function to fetch latest news for all topics
    def fetch_news_for_all_topics(self, first_parameter, topics, max_items_per_topic=10) -> dict:
        all_news = {}
        for topic in topics:
            all_news[topic] = self.fetch_news_for_topic(first_parameter, topic, max_items_per_topic)
        return all_news


    # first_parameter = ['ai', 'e_commerce', 'ai_medicine', 'ai_applications', 'e_payments']
    def get_fresh_headlines(self, first_parameter, second_parameter, connector_id, max_results):
        first_topic = self.fetch_news_for_all_topics(first_parameter, second_parameter, max_results)
        return first_topic

