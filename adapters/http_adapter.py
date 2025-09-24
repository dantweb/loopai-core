# core/adapters/http_adapter.py
import os
import re
import json
import xml.etree.ElementTree as ET
from typing import Optional, Dict

import aiohttp
import requests
from bs4 import BeautifulSoup

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.adapters.file_adapter_interface import FileAdapterInterface

logger = LoggerService()

class HttpAdapter(FileAdapterInterface):
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 2
    DEFAULT_TIMEOUT = 10

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__()

    def read(self, step_id: str, *args: str) -> BroadcastData:
        try:
            content = self._get_url_contents(self.url)
            content_type = self.detect_content_type(content)
            if content_type == 'rss':
                result = self.process_rss_content(content)
            elif content_type == 'html':
                result = self.clean_webpage_content(content)
            elif content_type == 'json':
                result = json.loads(content)
            else:
                result = content
            return BroadcastData({'result': result})
        except Exception as e:
            logger.error(f"[HttpAdapter::read] Failed: {str(e)}")
            raise

    def write(self, step_id: str, data: BroadcastData) -> bool:
        headers = {'Content-Type': 'application/json'}
        DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")
        if DEBUG_LEVEL == "DEBUG":
            logger.info(f"[HttpAdapter::write] typeof='{type(data)}' : {str(data)}")
        try:
            response = requests.post(self.url, headers=headers, json=data.to_json())
            request_status_code = response.status_code
            if request_status_code == 200:
                logger.info(f"[HttpAdapter::write] Successfully posted to {self.url}")
                return True
            else:
                logger.error(f"[HttpAdapter::write] Failed to post to {self.url}. Status code: {request_status_code}")

        except Exception as e:
            logger.error(f"[HttpAdapter::write] Failed: {str(e)}")
            return False

    def _get_url_contents(self, url, timeout=None):
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
        self.logger.info(f"[HttpAdapter::_get_url_contents] Attempting to fetch: {url} (timeout={timeout})")
        for attempt in range(self.RETRY_ATTEMPTS):
            try:

                response = requests.get(url)
                if response.status_code == 200:
                    return response.text
                else:
                    self.logger.error(f"[HttpAdapter::_get_url_contents] Attempt {attempt + 1} failed: {response.status_code}")

            except Exception as e:
                self.logger.error(f"[HttpAdapter::_get_url_contents] Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.RETRY_ATTEMPTS - 1:
                    from time import sleep
                    sleep(self.RETRY_DELAY)
                else:
                    raise Exception(f"Failed to fetch {url} after {self.RETRY_ATTEMPTS} attempts: {str(e)}")
        return None

    def clean_html(self, html_content, remove_tags=None, keep_tags=None, min_text_length=1):
        """Advanced HTML cleaning function."""
        if not html_content:
            return ''
        default_remove_tags = ['script', 'style', 'head', 'meta', 'link', 'svg', 'nav', 'iframe', 'comment', 'noscript']
        remove_tags = set(default_remove_tags + (remove_tags or []))
        keep_tags = set(keep_tags or [])
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for tag in soup(list(remove_tags - keep_tags)):
                tag.decompose()
            for comment in soup.find_all(text=lambda text: isinstance(text, str) and '<!--' in text):
                comment.extract()
            def has_meaningful_text(tag, min_length=min_text_length):
                text = tag.get_text(strip=True)
                return len(text) >= min_length
            for tag in soup.find_all():
                if tag.name in keep_tags:
                    continue
                if not has_meaningful_text(tag):
                    tag.decompose()
            return str(soup)
        except Exception as e:
            print(f"Error cleaning HTML: {e}")
            return html_content

    def clean_webpage_content(self, html_content):
        return self.clean_html(html_content, remove_tags=['ads', 'tracking'], min_text_length=3)

    def detect_content_type(self, content):
        """Detect the content type of the input string."""
        if not content or not isinstance(content, str):
            return None
        content = content.strip()
        try:
            json.loads(content)
            return 'json'
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            if content.startswith('<?xml') or '<rss' in content:
                ET.fromstring(content)
                return 'rss'
        except ET.ParseError:
            pass
        html_patterns = [
            re.compile(r'<!DOCTYPE\s+html', re.IGNORECASE),
            re.compile(r'<html\b', re.IGNORECASE),
            re.compile(r'<head\b', re.IGNORECASE),
            re.compile(r'<body\b', re.IGNORECASE)
        ]
        for pattern in html_patterns:
            if pattern.search(content):
                return 'html'
        return None

    def rss_to_json(self, rss_content: str) -> Optional[Dict]:
        """Convert RSS XML content to a structured JSON dictionary."""
        if not rss_content or not isinstance(rss_content, str):
            return None
        try:
            root = ET.fromstring(rss_content)
            result = {'channel': {'title': '', 'description': '', 'link': '', 'items': []}}
            channel = root.find('channel')
            if channel is None:
                return None
            for field in ['title', 'description', 'link']:
                elem = channel.find(field)
                result['channel'][field] = elem.text if elem is not None else ''
            for item in channel.findall('item'):
                item_dict = {}
                fields_to_extract = ['title', 'link', 'description', 'pubDate', 'guid', 'author', 'category']
                for field in fields_to_extract:
                    elem = item.find(field)
                    if elem is not None:
                        item_dict[field] = elem.text
                for elem in item:
                    if elem.tag not in fields_to_extract:
                        item_dict[elem.tag] = elem.text
                result['channel']['items'].append(item_dict)
            return result
        except ET.ParseError as e:
            print(f"XML Parsing error: {e}")
            return None
        except Exception as e:
            print(f"Error converting RSS to JSON: {e}")
            return None

    def process_rss_content(self, content: str) -> Optional[Dict]:
        """Wrapper method to process RSS content."""
        if not content or 'rss' not in content.lower():
            return None
        return self.rss_to_json(content)

    def advanced_rss_to_json(self, rss_content: str) -> Optional[Dict]:
        """Advanced RSS to JSON conversion with additional processing."""
        json_data = self.rss_to_json(rss_content)
        if not json_data:
            return None
        try:
            for item in json_data.get('channel', {}).get('items', []):
                if item.get('description'):
                    item['description'] = item['description'][:1000]
                if item.get('pubDate'):
                    pass  # Add date parsing if needed
            return json_data
        except Exception as e:
            print(f"Post-processing error: {e}")
            return json_data