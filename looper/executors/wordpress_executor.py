##filesystem: ./loopai_src/core/looper/executors/wordpress_executor.py
import base64
import os

from core.looper.executors.executor_interface import ExecutorInterface

## deprecated with new BroadcastData and BroadcastAdapter
class WordpressExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__()
        self.parent_step = None

    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        for item in input_data:
            if 'image_file' in item and 'image_base64' not in item:
                image_file_path = item['image_file']
                if os.path.exists(image_file_path):
                    with open(image_file_path, 'rb') as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        item['image_base64'] = encoded_string
                else:
                    raise FileNotFoundError(f"Image file not found: {image_file_path}")

        return input_data

    async def run(self, model, system_content, user_content, max_tokens) -> str:

        return ''

    def set_parent_step(self, parent_step):
        self.parent_step = parent_step
        pass
