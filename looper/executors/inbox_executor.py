##filepath: #project_root#/loopai_src/core/looper/executors/inbox_executor.py

from core.looper.executors.executor_interface import ExecutorInterface
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService

logger = LoggerService()


class InboxExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.model = model

    def prepare_prompt(self, input_data: list, prompt_template: str):

        return input_data

    def run(self, model, system_content, user_content, temperature=0.7, **kwargs) -> BroadcastData:
        """
        Extracts messages from API POST requests and prepares them to be saved with filesystem_adapter.

        Args:
            model: The model to use for processing
            system_content: The system content for the model
            user_content: Data containing API request information with messages
            temperature: Temperature parameter for model processing
            **kwargs: Additional arguments

        Returns:
            BroadcastData with prepared messages for filesystem_adapter
        """
        # Extract the result list from user_content
        result_list = user_content.get('result', [])

        # Prepare a list to store extracted and formatted messages
        updated_files = []

        # Process each result in the result list
        for result in result_list:
            # Check if this is a POST request with a message body
            if result.get('method') == 'POST' and 'body' in result and 'message' in result['body']:
                # Generate a timestamp for the filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Extract message details for filename
                message = result['body']['message']
                sender = message.get('from', 'unknown').replace('/', '_')
                recipient = message.get('to', 'unknown').replace('/', '_')

                # Create a filename based on message metadata
                filename = f"message_{timestamp}_{sender}_to_{recipient}.json"

                # Keep the exact message body structure as file_content
                import json
                file_content = json.dumps(result['body'])

                # Add to the updated_files list in the format expected by filesystem_adapter
                updated_files.append({
                    'path': f"inbox/{filename}",
                    'file_content': file_content,
                    'file_operation': 'update'
                })

        # Create the response structure for filesystem_adapter
        response = {
            'step_id': user_content.get('step_id', ''),
            'result': {
                'updated_files': updated_files
            },
            'session_id': user_content.get('session_id', '')
        }

        return BroadcastData(response)
