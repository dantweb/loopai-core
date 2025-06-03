import base64
import json
import requests
from core.looper.executors.gpt2code_executor import Gpt2codeExecutor
from core.services.session import session_manager


class Gpt2code_chunkExecutor(Gpt2codeExecutor):
    def prepare_prompt(self, input_data: list, prompt_template: str):
        # Compress and encode the input data
        # request_content = self.compress_and_encode(input_data)
        # Prepare the prompt based on input_data and the prompt_template
        prompt_template['requestContent'] = input_data
        return prompt_template

    def compress_and_encode(self, data: list) -> str:
        import gzip
        import io

        compressed_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed_buffer, mode='wb') as f:
            f.write(json.dumps(data).encode('utf-8'))

        compressed_data = compressed_buffer.getvalue()
        encoded_data = base64.b64encode(compressed_data).decode('utf-8')
        return encoded_data

    def run(self, model, system_content, user_content, fine_tuning):
        # Compress and encode user content
        # Define the API endpoint and key
        api_endpoint = "https://api.openai.com/v1/chat/completions"
        api_key = session_manager.get_env('USER_GPT_API_KEY')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": json.dumps(system_content)},
                {"role": "user", "content": json.dumps(user_content)}
            ],
            "max_tokens": fine_tuning
        }

        response = requests.post(api_endpoint, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

        result = response.json()
        return json.loads(result['choices'][0]['message']['content'])

    def process_responses(self, responses: list) -> dict:
        combined_result = {}
        for response in responses:
            # Combine responses as needed
            combined_result.update(response)
        return combined_result
