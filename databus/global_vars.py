# global_vars.py
import os
from dotenv import load_dotenv

load_dotenv()
WORDPRESS_URL = os.getenv('WORDPRESS_URL', 'dummyurl')
WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME', 'dummyusername')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD', 'dummypassword')
TUMBLR_API_KEY = os.getenv('TUMBLR_API_KEY', 'abcdefg_allahu_akbar')
TWITTER_API_KEY = os.getenv('TUMBLR_API_KEY', 'abcdefg_allahu_akbar')
BLOGSPOT_API_KEY = os.getenv('TUMBLR_API_KEY', 'abcdefg_allahu_akbar')
BLOGSPOT_API_KEY = os.getenv('TUMBLR_API_KEY', 'abcdefg_allahu_akbar')

global_loop_index = None
global_step_name = None
NEWSAPI_API_KEY = None
USER_GPT_API_KEY = os.getenv('USER_GPT_API_KEY', 'dummy-gpt-key-123')
