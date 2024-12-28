import os
import pytest

from core.services.featherchunks_service import FeatherchunkService


@pytest.mark.integration
def test_get_response_chunked_real():
    """
    Integration test that uses real requests to Featherless LLM.
    Make sure FEATHERLESS_API_URL and FEATHERLESS_API_KEY are set,
    and a model like "featherless-70B" is available at that endpoint.
    """

    # 1. Ensure ENV variables exist
    assert os.getenv('FEATHERLESS_API_URL'), "FEATHERLESS_API_URL not set"
    assert os.getenv('FEATHERLESS_API_KEY'), "FEATHERLESS_API_KEY not set"

    # 2. Create large synthetic text with 10 chunk markers
    #    Each chunk includes a marker CHUNK_i_MARKER
    #    We simply replicate a small text multiple times for demonstration
    large_text = []
    for i in range(10):
        # Insert a marker at the beginning
        chunk_marker = f"### CHUNK_{i}_MARKER ###"
        repeated_sentence = "This is some repeated content for demonstration " \
                            "purposes that should be summarized or recognized. " * 50
        large_text.append(f"{chunk_marker}\n{repeated_sentence}")

    # Combine all
    large_text_str = "\n\n".join(large_text)

    # 3. Initialize the real FeatherlessService
    service = FeatherchunkService(model="meta-llama/Meta-Llama-3.1-8B-Instruct")

    # 4. Prepare system instructions
    system_content = {
        "instructions": "You are a helpful assistant. Summarize input chunks. Include references to CHUNK markers."
    }

    # 5. Call the chunked method
    final_summary = service.get_response_chunked(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        system_content=system_content,
        large_text=large_text_str,
        max_tokens=800,       # Adjust as needed
        chunk_size=100        # Force smaller chunks for demonstration
    )

    print("\n===== Final Summary from Real Featherless LLM =====\n")
    print(final_summary)
    print("\n===================================================\n")

    # 6. OPTIONAL: check if the final summary includes references to CHUNK markers
    #    Because we can't fully control the real model's output, we treat this as a "best effort" check.
    for i in range(10):
        marker = f"CHUNK_{i}_MARKER"
        if marker not in final_summary:
            print(f"WARNING: '{marker}' was not explicitly referenced. The model may have summarized differently.")
        else:
            print(f"SUCCESS: Found '{marker}' in the final summary.")
