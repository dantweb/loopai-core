PROMPT_TEMPLATES={
    "PROMPT_EXECUTE_TASK": {
            "requestContent": "{{REQUEST_CONTENT}}",
            "task": """
                """,
            "example_output": {
              "updated_files": [
                { "path": "status/status.json", "file_content": "...", "file_operation": "create" },
                { "path": "current_operation/filename.json", "file_content": "...", "file_operation": "create" },
              ]
            },
        }
}

SYSTEM_CONTENT_TEMPLATES={
    "SYSTEM_EXECUTE_TASK":"""You are a citizen of Loopland - a virtual country for 
    AI, robots and people. """
}