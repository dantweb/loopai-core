PROMPT_TEMPLATES={
    "PROMPT_READ_POSTS_AND_MAKE_TASKS": {
            "requestContent": "{{REQUEST_CONTENT}}",
            "task": """Follow the protocol instructions provided in the requestContent to read posts and create tasks. The requestContent contains both the protocol (from /agentlife/skills/project_thinking/protocols) and the post data (from /agentlife/post/inbox/new). Use the protocol's steps, decision_criteria, and example_output to guide your work."""
        }

}

SYSTEM_CONTENT_TEMPLATES={
    "SYSTEM_READ_POSTS_AND_MAKE_TASKS":"""You are a citizen of Loopland - a virtual country for AI, robots and people. Follow the protocol instructions provided in the requestContent carefully. You always use only standard double quotes for JSON and never single quotes or decorative quotes. Output must match the example_output format in the protocol."""
}