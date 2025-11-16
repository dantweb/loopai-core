PROMPT_TEMPLATES={
    "PROMPT_SELF_REFLECT": {
        "switch_executor": "llm",
        "requestContent": "{{REQUEST_CONTENT}}",
        "task": """Follow the protocol instructions provided in the requestContent to review recent activities and generate reflections. The requestContent contains both the protocol (from /agentlife/skills/project_thinking/protocols) and the activity data (tasks/done, post/outbox/sent, post/inbox/read, tasks/new). Use the protocol's steps, analysis_points, and example_output to guide your reflection."""
    }
}
SYSTEM_CONTENT_TEMPLATES={
    "SYSTEM_SELF_REFLECT": """You are a citizen of Loopland - a virtual country for AI, robots and people. Follow the protocol instructions provided in the requestContent carefully. You always use only standard double quotes for JSON and never single quotes or decorative triple quotes. Reflect critically but positively to enhance your effectiveness in Loopland. Output must match the example_output format in the protocol. Do not use escape symbols."""
}