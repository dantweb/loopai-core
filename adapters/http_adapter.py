import os
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
        html = self._get_url_contents(self.url)
        result = self.clean_webpage_content(html)
        return BroadcastData({'result': result})

    def write(self, step_id: str, data: BroadcastData) -> bool:
        headers = {'Content-Type': 'application/json'}
        DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO")
        if DEBUG_LEVEL == "DEBUG":
            self.logger.info(f"[LoopAIDirectWPAPIService::create_post] typeof='{type(data)}' : {str(data)}")

        response = requests.post(self.url,  headers=headers, json=data.__json__())
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
