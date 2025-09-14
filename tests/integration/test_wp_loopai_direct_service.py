import json
import unittest
from unittest.mock import patch, AsyncMock
import aiohttp
import requests

from core.models.broadcast_data import BroadcastData
from core.services.loopai_direct_wpapi_service import LoopAIDirectWPAPIService


class MockResponse:
    def __init__(self, status=200, text='{"status": "success"}'):
        self.status = status
        self._text = text

    async def text(self):
        return self._text

class TestLoopAIDirectWPAPIServiceIntegration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.service = LoopAIDirectWPAPIService(
            wp_site='https://wp-mysql:8085',
            wp_username='admin',
            wp_password='admin'
        )
        self.sample_data = BroadcastData({
            "data":
                {
                    "result":{
                        'title': 'Test Title',
                        'lead_paragraph': 'Test Lead',
                        'summary': 'Test Summary',
                        'category': 'Test Category',
                        'article_body': 'Test Body',
                        'tags': 'tag1,tag2',
                        'image_base64': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg==',
                        # Tiny base64 image
                        'image_file': 'test.jpg'
                    }
                }
        })

    @patch('aiohttp.ClientSession.post')
    async def test_create_post_success(self, mock_post):
        mock_response = MockResponse(status=200, text='{"status": "success", "post_id": 123}')
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_post.return_value = mock_context

        result = await self.service.create_post(self.sample_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, 200)
        text = await result.text()
        self.assertIn("success", text)

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], 'https://wp-mysql:8085/wp-json/loopai-adapter/v1/create-post')
        self.assertEqual(called_kwargs['headers']['Content-Type'], 'application/json')
        json_data = called_kwargs['json']

        self.assertIn('title', json_data['data']['result'])
        self.assertEqual(json_data['data']['result']['title'], 'Test Title')
        self.assertIn('image_base64', json_data['data']['result'])
        self.assertIsInstance(called_kwargs['timeout'], aiohttp.ClientTimeout)

    @patch('aiohttp.ClientSession.post')
    async def test_create_post_failure(self, mock_post):
        mock_response = MockResponse(status=400, text='{"error": "Bad Request"}')
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_post.return_value = mock_context

        with self.assertRaises(Exception) as context:
            await self.service.create_post(self.sample_data)
            self.assertIn("HTTP error: 400", str(context.exception))

    @patch('requests.get')
    def test_get_all_posts_success(self, mock_get):
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b'[{"id": 1, "title": "Post 1"}, {"id": 2, "title": "Post 2"}]'
        mock_get.return_value = mock_response

        result = self.service.get_all_posts()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        mock_get.assert_called_once_with('https://wp-mysql:8085/wp-json/wp/v2/posts', auth=self.service.auth)

    @patch('requests.get')
    def test_get_all_posts_failure(self, mock_get):
        mock_response = requests.Response()
        mock_response.status_code = 500
        mock_response._content = b'{"error": "Server Error"}'
        mock_get.return_value = mock_response

        result = self.service.get_all_posts()

        self.assertEqual(result, [])

    def test_save_post_to_text_file(self):
        test_data = BroadcastData({'key': 'value'})
        self.service.save_post_to_text_file(test_data)

        path = "/app/var/filesystem/loopai_direct_wpapi_service_output.txt"
        with open(path, 'r') as f:
            content = f.read()
        loaded = json.loads(content)
        self.assertEqual(loaded['key'], 'value')

if __name__ == "__main__":
    unittest.main()