#Filepath relative to the core root[.]: ./loopai_src/core/services/freshrss_service.py
import ast
import os

import requests
from dotenv import load_dotenv
import feedparser

from core.services.logger_service import LoggerService
from web.routes.filesystem import logger_service

load_dotenv()

class FreshRssService:

    def __init__(self):
        self.logger = LoggerService()
        # Replace with your actual FreshRSS API endpoint and auth token
        self.freshrss_api_endpoint = os.getenv("FRESHRSS_API_ENDPOINT")
        self.freshrss_auth_token = os.getenv("FRESHRSS_AUTH_TOKEN")


    def fetch_news_for_topic(self, first_parameter, topic, max_items=10) -> list:
        logger_service.info(f"[FreshRssService::fetch_news_for_topic] Fetching news for topic: {topic}")
        feeds = first_parameter.get(topic, [])
        logger_service.info(f"[FreshRssService::fetch_news_for_topic] Feeds: {str(feeds)}")
        news_items = []

        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            logger_service.info(f"[FreshRssService::fetch_news_for_topic] parsing url: {feed_url}")
            logger_service.info(f"[FreshRssService::fetch_news_for_topic] feed.entries: {str(feed.entries)}")
            count = 0
            for entry in feed.entries:
                # Construct the news entry object
                new_entry = {
                    'title': entry.title + '--- body --' + entry.summary if hasattr(entry, 'summary') else entry.title
                }
                news_items.append(new_entry)

                # Mark the item as read in FreshRSS
                item_id = self._get_item_id(entry)
                if item_id:
                    self._mark_item_as_read(item_id)

                count += 1
                if count >= max_items:
                    break
            if len(news_items) >= max_items:
                break
        return news_items


    def fetch_news_for_all_topics(self, first_parameter, topics, max_items_per_topic=10) -> dict:
        self.logger.info(f"[FreshRssService::fetch_news_for_all_topics] first_parameter {str(first_parameter)}")
        self.logger.info(f"[FreshRssService::fetch_news_for_all_topics] Fetching news for all topics {str(topics)}")
        all_news = {}
        for topic in topics:
            all_news[topic] = self.fetch_news_for_topic(first_parameter, topic, max_items_per_topic)
        return all_news


    def get_fresh_headlines(self, first_parameter, second_parameter, connector_id, max_results):
        self.logger.info(f"[FreshRssService::get_fresh_headlines] first_parameter type {type(first_parameter)}: {first_parameter}")
        self.logger.info(f"[FreshRssService::get_fresh_headlines] second_parameter type{type(second_parameter)}: {second_parameter}")
        first_topic = self.fetch_news_for_all_topics(first_parameter, second_parameter, max_results)
        return first_topic


    def _get_item_id(self, entry):
        # Attempt to identify a unique item ID. Commonly, feed entries have 'id' or 'link'.
        # Adjust this logic as needed based on your specific feed structure.
        if hasattr(entry, 'id'):
            return entry.id
        elif hasattr(entry, 'link'):
            return entry.link
        return None


    def _mark_item_as_read(self, item_id):
        # Send a request to FreshRSS to mark the item as read.
        # Consult the FreshRSS API documentation for the correct endpoint and parameters.
        endpoint = f"{self.freshrss_api_endpoint}/api/markAsRead"
        headers = {
            'Authorization': f"Bearer {self.freshrss_auth_token}",
            'Content-Type': 'application/json'
        }
        payload = {
            "item_id": item_id,
            "status": "read"
        }

        response = requests.post(endpoint, headers=headers, json=payload)

        if response.status_code == 200:
            logger_service.info(f"[FreshRssService::_mark_item_as_read] Successfully marked item {item_id} as read.")
        else:
            logger_service.error(
                f"[FreshRssService::_mark_item_as_read] Failed to mark item {item_id} as read. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
