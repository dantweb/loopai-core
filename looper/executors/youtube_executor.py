#filesystem ./loopai_src/core/looper/executors/gpt_executor.py
import requests
from dotenv import load_dotenv

from core.looper.executors.executor_interface import ExecutorInterface
from core.services.session_manager import session_manager

load_dotenv()

YOUTUBE_API_KEY = session_manager.get_env('YOUTUBE_API_KEY') or 'no-youtoube-api-key'

class YoutubeExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template=''):
        return input_data[0]

    def run(self, model, system_content, user_content, max_tokens):
        result = {'embed_code': self.get_youtube_embed_code(user_content)}
        return result

    def get_youtube_embed_code(self, formulated_prompt: object) -> object:
        search_url = 'https://www.googleapis.com/youtube/v3/search'
        search_params = {
            'part': 'snippet',
            'q': formulated_prompt + ' in english language',
            'type': 'video',
            'key': YOUTUBE_API_KEY,
            'maxResults': 2  # Number of results to return
        }

        search_response = requests.get(search_url, params=search_params)
        search_results = search_response.json()

        # Extract video details
        videos = []
        for item in search_results['items']:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            url = f"https://www.youtube.com/watch?v={video_id}"
            embed_code = f'<iframe width="100%" height="350px" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
            videos.append({
                'title': title,
                'url': url,
                'embed_code': embed_code
            })

        return videos[1]
