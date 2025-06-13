from typing import List

from core.looper.executors.llm_executor import LlmExecutor
from core.models.broadcast_data import BroadcastData

MAX_TOKEN_LENGTH = 8192  # Approx GPT-4 token limit (adjust if model-specific)


class Gpt2code_chunkExecutor(LlmExecutor):
    def __init__(self, model: str):
        super().__init__(model)

    def chunk_input(self, input_text: str, max_token_length: int = MAX_TOKEN_LENGTH) -> List[str]:
        """Chunk input text into smaller segments that fit within the token limits."""
        input_length = len(input_text)
        if input_length <= max_token_length:
            return [input_text]

        # Divide input into segments that fit within the limit
        chunks = []
        for i in range(0, input_length, max_token_length - 500):  # Leave space for response/system tokens
            chunks.append(input_text[i:i + (max_token_length - 500)])
        return chunks

    def send_prompt_to_llm(self, model, system_content, user_content: BroadcastData, temperature=0.2):
        if temperature is None:
            temperature = 0.2

        # Ensure temperature is a float and within valid range
        try:
            temperature = float(temperature)
        except (TypeError, ValueError):
            temperature = 0.2

        # Clamp temperature between 0.0 and 1.0
        temperature = max(0.0, min(1.0, temperature))

        # Handle chunking for large inputs (requestContent could be very large)
        input_chunks = self.chunk_input(user_content)  # Assuming `request` contains raw input text
        responses = []

        # Process each chunk iteratively
        for chunk in input_chunks:
            user_content_chunk = BroadcastData(chunk)  # Create individual BroadcastData for each chunk
            response = self.featherless.get_response(model, system_content, user_content_chunk, temperature)
            responses.append(response)

        # Combine all responses (adjust logic based on format/requirements)
        return "\n".join(responses)
