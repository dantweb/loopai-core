# ./loopai_src/core/services/featherchunks_service.py

import json
import os

from openai import OpenAI
from dotenv import load_dotenv
from core.models.broadcast_data import BroadcastData
from core.services.service_interface import ServiceInterface

load_dotenv()
FEATHERLESS_API_URL = os.getenv('FEATHERLESS_API_URL', 'featherless_url')
FEATHERLESS_API_KEY = os.getenv('FEATHERLESS_API_KEY', 'dummy_key')


class FeatherchunkService(ServiceInterface):
    """
    Service that communicates with a Featherless-hosted Llama model
    using an OpenAI-like Python SDK, with support for chunking
    large BroadcastData objects.
    """

    def __init__(self, model: str):
        super().__init__(model)
        self.client = OpenAI(
            base_url=FEATHERLESS_API_URL,
            api_key=FEATHERLESS_API_KEY
        )

    def get_response(self, model, system_content, user_content: BroadcastData, max_tokens):
        """
        Makes a single request to the LLM. Direct usage if input is small enough.
        """
        self.logger.info("[FeatherchunkService::get_response] Requesting response from Featherless API...")
        self.logger.info(f"[FeatherchunkService::get_response] typeof user_content: {type(user_content)}")
        self.logger.info(f"[FeatherchunkService::get_response] user_content: {str(user_content)}")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": json.dumps(system_content)},
                    # We directly JSON-serialize the broadcast data here, which works fine for smaller data
                    {"role": "user", "content": json.dumps(user_content.__json__())}
                ],
                max_tokens=max_tokens
            )
            result_content = response.model_dump()['choices'][0]['message']['content']

            self.logger.info(f"[FeatherchunkService::get_response] Response received successfully: \n{result_content}\n")
            return result_content

        except Exception as e:
            self.logger.error(f"[FeatherchunkService::get_response] Error: {str(e)}")
            raise e

    def get_response_chunked(
        self,
        model,
        system_content,
        user_content: BroadcastData,
        max_tokens=2048,
        max_words_per_chunk=1500
    ):
        """
        Handle large BroadcastData by:
          1) Extracting text from the data structure (e.g., articles).
          2) Splitting into multiple chunks (by word count).
          3) Summarizing each chunk separately.
          4) Combining partial summaries into a final cohesive summary.

        :param model: Model name (e.g., "featherless-70B").
        :param system_content: Instructions/context for the system prompt.
        :param user_content: A BroadcastData object with potentially large amounts of textual data.
        :param max_tokens: The maximum tokens for each call's response.
        :param max_words_per_chunk: Word-chunk size threshold for splitting large text.
        :return: A final combined summary referencing all chunks.
        """
        self.logger.info("[FeatherchunkService::get_response_chunked] Starting chunked processing...")

        # 1. Extract textual data from BroadcastData
        #    Example: gather all article text into one big list of "articles"
        all_text_snippets = self._extract_text_from_broadcast_data(user_content)

        # 2. Create word-based chunks from these snippets
        chunks = self._build_chunks_from_snippets(all_text_snippets, max_words_per_chunk)
        self.logger.info(f"[FeatherchunkService::get_response_chunked] Created {len(chunks)} chunk(s).")

        # 3. Summarize each chunk
        partial_summaries = []
        for idx, chunk_text in enumerate(chunks):
            user_prompt = {
                "role": "user",
                "content": (
                    f"CHUNK_{idx}_MARKER\n\n"
                    f"{chunk_text}\n\n"
                    "Please summarize the key points from this chunk in 2-3 sentences. "
                    "Include the chunk marker in your summary."
                )
            }

            self.logger.info(f"[FeatherchunkService::get_response_chunked] Summarizing chunk {idx} ...")
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": json.dumps(system_content)},
                        user_prompt
                    ],
                    max_tokens=max_tokens
                )
                summary = response.model_dump()['choices'][0]['message']['content']
                self.logger.info(f"[FeatherchunkService::get_response_chunked] Chunk {idx} summary:\n{summary}\n")
                partial_summaries.append(f"CHUNK_{idx}_SUMMARY: {summary.strip()}")

            except Exception as e:
                self.logger.error(
                    f"[FeatherchunkService::get_response_chunked] Error summarizing chunk {idx}: {str(e)}"
                )
                raise e

        # 4. Combine partial summaries into a final prompt
        combined_summaries = "\n\n".join(partial_summaries)
        final_prompt = {
            "role": "user",
            "content": (
                "We have multiple chunk summaries below. Each summary references a CHUNK_x_MARKER.\n\n"
                f"{combined_summaries}\n\n"
                "Please combine these into a final cohesive summary that covers all key points. "
                "Retain references to chunk markers to confirm coverage."
            )
        }

        self.logger.info("[FeatherchunkService::get_response_chunked] Generating final combined summary ...")
        try:
            final_response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": json.dumps(system_content)},
                    final_prompt
                ],
                max_tokens=max_tokens
            )
            final_content = final_response.model_dump()['choices'][0]['message']['content']
            self.logger.info("[FeatherchunkService::get_response_chunked] Final combined summary received.")
            return final_content

        except Exception as e:
            self.logger.error(f"[FeatherchunkService::get_response_chunked] Error in final combination step: {str(e)}")
            raise e

    def _extract_text_from_broadcast_data(self, data: BroadcastData):
        """
        Extract text fields from the BroadcastData object in a structured way.
        Return a list of text snippets. You can adapt this method
        to your broadcast data schema.

        Example assumption:
        data.__json__() -> {
            "articles": [
                {"title": "...", "body": "..."},
                ...
            ]
        }
        """
        json_data = data.__json__()
        articles = json_data.get("articles", [])  # adapt if your schema differs

        text_snippets = []
        for article in articles:
            title = article.get("title", "")
            body = article.get("body", "")
            # Concatenate or store separately:
            snippet = f"Title: {title}\nBody: {body}"
            text_snippets.append(snippet)

        return text_snippets

    def _build_chunks_from_snippets(self, snippets, max_words_per_chunk=1500):
        """
        Take a list of text snippets (each snippet may be an article),
        and build word-based chunks that do not exceed max_words_per_chunk.
        """
        chunks = []

        for snippet in snippets:
            words = snippet.split()
            current_chunk = []

            for w in words:
                current_chunk.append(w)
                if len(current_chunk) >= max_words_per_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []

            if current_chunk:
                chunks.append(" ".join(current_chunk))

        return chunks
