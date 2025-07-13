import os
import re
import json
import xml.etree.ElementTree as ET
from typing import Optional, Dict

from bs4 import BeautifulSoup
import requests

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.adapters.file_adapter_interface import FileAdapterInterface

logger = LoggerService()

class HttpAdapter(FileAdapterInterface):
    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__()

    # Public Methods
    def read(self, step_id: str, *args: str) -> BroadcastData:
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

    def write(self, step_id: str, data: BroadcastData) -> bool:
        headers = {'Content-Type': 'application/json'}
        DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")
        if DEBUG_LEVEL == "DEBUG":
            self.logger.info(f"[LoopAIDirectWPAPIService::create_post] typeof='{type(data)}' : {str(data)}")

        response = requests.post(self.url,  headers=headers, json=data.to_json())
        if not response.ok:
            self.logger.error(f"Failed to create post: {response.status_code} - {response.text}")
            return False

        self.logger.info(f"Post created successfully: {response}")
        return True

    def _get_url_contents(self, url, timeout=300):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.text  # For text content
            # return response.content  # For binary content
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    from bs4 import BeautifulSoup

    def clean_html(self,
            html_content,
            remove_tags=None,
            keep_tags=None,
            min_text_length=1
    ):
        """
        Advanced HTML cleaning function.

        Args:
            html_content (str): HTML to clean
            remove_tags (list): Additional tags to remove
            keep_tags (list): Tags to preserve
            min_text_length (int): Minimum length of text to consider meaningful

        Returns:
            str: Cleaned HTML
        """
        if not html_content:
            return ''

        # Default tags to remove
        default_remove_tags = [
            'script', 'style', 'head', 'meta',
            'link', 'svg', 'nav', 'iframe',
            'comment', 'noscript'
        ]

        # Merge with user-provided tags to remove
        remove_tags = set(default_remove_tags + (remove_tags or []))

        # Tags to keep (if specified)
        keep_tags = set(keep_tags or [])

        try:
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove specified tags
            for tag in soup(list(remove_tags - keep_tags)):
                tag.decompose()

            # Remove comments
            for comment in soup.find_all(text=lambda text: isinstance(text, str) and '<!--' in text):
                comment.extract()

            # Function to check if tag has meaningful content
            def has_meaningful_text(tag, min_length=min_text_length):
                # Get text, stripping whitespace
                text = tag.get_text(strip=True)

                # Check if text meets minimum length requirement
                return len(text) >= min_length

            # Remove tags without meaningful text
            for tag in soup.find_all():
                # Skip tags in keep_tags
                if tag.name in keep_tags:
                    continue

                # Remove if no meaningful text
                if not has_meaningful_text(tag):
                    tag.decompose()

            # Return cleaned HTML
            return str(soup)

        except Exception as e:
            print(f"Error cleaning HTML: {e}")
            return html_content

    # Usage examples
    def clean_webpage_content(self, html_content):
        return self.clean_html(
            html_content,
            remove_tags=['ads', 'tracking'],  # Optional additional tags
            min_text_length=3  # Minimum meaningful text length
        )

    def detect_content_type(self, content):
        """
        Detect the content type of the input string.

        Args:
            content (str): Input content to analyze

        Returns:
            str: Content type - 'rss', 'html', or 'json'
        """
        if not content or not isinstance(content, str):
            return None

        # Trim whitespace
        content = content.strip()

        # Check for JSON
        try:
            json.loads(content)
            return 'json'
        except (json.JSONDecodeError, TypeError):
            pass

        # Check for RSS/XML
        try:
            # Quick XML check
            if content.startswith('<?xml') or '<rss' in content:
                # Attempt to parse the XML
                ET.fromstring(content)
                return 'rss'
        except ET.ParseError:
            pass

        # Check for HTML
        # Look for HTML-specific patterns
        html_patterns = [
            re.compile(r'<!DOCTYPE\s+html', re.IGNORECASE),
            re.compile(r'<html\b', re.IGNORECASE),
            re.compile(r'<head\b', re.IGNORECASE),
            re.compile(r'<body\b', re.IGNORECASE)
        ]

        for pattern in html_patterns:
            if pattern.search(content):
                return 'html'

        # If no clear type is found, return None or a default
        return None


    def rss_to_json(self, rss_content: str) -> Optional[Dict]:
        """
        Convert RSS XML content to a structured JSON dictionary.

        Args:
            rss_content (str): RSS XML content

        Returns:
            Optional[Dict]: Parsed RSS content as a dictionary, or None if parsing fails
        """
        if not rss_content or not isinstance(rss_content, str):
            return None

        try:
            # Parse the XML
            root = ET.fromstring(rss_content)

            # Initialize result dictionary
            result = {
                'channel': {
                    'title': '',
                    'description': '',
                    'link': '',
                    'items': []
                }
            }

            # Find channel element
            channel = root.find('channel')
            if channel is None:
                return None

            # Extract channel metadata
            for field in ['title', 'description', 'link']:
                elem = channel.find(field)
                result['channel'][field] = elem.text if elem is not None else ''

            # Extract items
            for item in channel.findall('item'):
                item_dict = {}

                # Extract common RSS item fields
                fields_to_extract = [
                    'title', 'link', 'description',
                    'pubDate', 'guid', 'author',
                    'category', 'comments'
                ]

                for field in fields_to_extract:
                    elem = item.find(field)
                    if elem is not None:
                        item_dict[field] = elem.text

                # Add any additional elements
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


    # Example usage with error handling
    def process_rss_content(self, content: str) -> Optional[Dict]:
        """
        Wrapper method to process RSS content

        Args:
            content (str): Input content

        Returns:
            Optional[Dict]: Processed JSON or None
        """
        # Check if content is RSS first
        if not content or 'rss' not in content.lower():
            return None

        # Convert RSS to JSON
        return self.rss_to_json(content)


    # Advanced example with more robust processing
    def advanced_rss_to_json(self, rss_content: str) -> Optional[Dict]:
        """
        Advanced RSS to JSON conversion with additional processing

        Args:
            rss_content (str): RSS XML content

        Returns:
            Optional[Dict]: Processed and cleaned RSS content
        """
        # Basic conversion
        json_data = self.rss_to_json(rss_content)

        if not json_data:
            return None

        # Optional post-processing
        try:
            # Example: Clean up description, truncate long texts
            for item in json_data.get('channel', {}).get('items', []):
                # Truncate description if too long
                if item.get('description'):
                    item['description'] = item['description'][:1000]

                # Convert pubDate to a more standard format if needed
                if item.get('pubDate'):
                    # Add your date parsing/formatting logic here
                    pass

            return json_data

        except Exception as e:
            print(f"Post-processing error: {e}")
            return json_data

