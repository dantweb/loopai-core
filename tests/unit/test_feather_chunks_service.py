import pytest
import string
import random

from unittest.mock import MagicMock

from core.services.featherchunks_service import FeatherchunkService


@pytest.fixture
def mock_featherless_service(monkeypatch):
    """
    A fixture that creates a mock version of FeatherlessService
    so we don't call the real API during tests.
    """
    service = FeatherchunkService(model="featherless-70B")
    mock_client = MagicMock()
    service.client = mock_client
    return service

def generate_large_test_text(num_chunks=10, chunk_size=500):
    """
    Generate a large text of `num_chunks` sections, each ~`chunk_size` words,
    with unique chunk markers for easy detection.
    """
    large_text = []
    for i in range(num_chunks):
        # Create random words
        random_words = " ".join(
            ''.join(random.choices(string.ascii_lowercase, k=5))
            for _ in range(chunk_size)
        )
        # Add a unique label
        chunk_label = f"CHUNK_{i}_MARKER"
        large_text.append(f"{chunk_label} {random_words}")

    return "\n\n".join(large_text)

def mock_chat_completion_create(model, messages, max_tokens):
    """
    A mock function that simulates the LLM response.
    We embed references to the user prompt so we can test
    that chunk markers are recognized.
    """
    # Let's just echo back the user content to demonstrate
    user_message = [m for m in messages if m["role"] == "user"]
    if not user_message:
        return MagicMock(model_dump=lambda: {"choices": [{"message": {"content": "No user message."}}]})

    content = user_message[-1]["content"]

    # Fake a summary that includes any CHUNK references from the prompt
    # We simulate the model having read them by simply "detecting" chunk markers
    # and listing them in a summary-like style.
    detected_chunks = []
    for line in content.split("\n"):
        if "CHUNK_" in line:
            # naive detection of chunk id
            for token in line.split():
                if "CHUNK_" in token:
                    detected_chunks.append(token)

    summary_text = " ".join(set(detected_chunks))  # deduplicate

    # Provide a "model_dump" return in the same shape as the real response
    return MagicMock(
        model_dump=lambda: {
            "choices": [
                {"message": {"content": f"Summary: Found {len(detected_chunks)} chunk markers: {summary_text}"}}
            ]
        }
    )

def test_get_response_chunked(mock_featherless_service):
    """
    Test that get_response_chunked can process large text in 10 chunks
    and the final output references all chunk markers (proof that all are read).
    """

    # 1. Generate large text with 10 chunk markers
    test_text = generate_large_test_text(num_chunks=10, chunk_size=200)

    # 2. Mock the model call so we don't hit the real API
    mock_featherless_service.client.chat.completions.create.side_effect = mock_chat_completion_create

    # 3. System instructions
    system_content = {
        "instructions": "You are a helpful assistant. Summarize input chunks."
    }

    # 4. Call the chunked method
    final_response = mock_featherless_service.get_response_chunked(
        model="featherless-70B",
        system_content=system_content,
        large_text=test_text,
        max_tokens=1000,
        chunk_size=300  # smaller chunk size to force multiple chunks
    )

    print(f"Final response: {str(final_response)}")

    # 5. Assert final_response includes references to all chunk markers
    for i in range(10):
        assert f"CHUNK_{i}_MARKER" in final_response, \
            f"Final summary should reference CHUNK_{i}_MARKER."

    print("\nTest passed: All chunk markers were found in the final summary.\n")
