PROMPT_TEMPLATES={
    "PROMPT_EXECUTE_TASK": {
            "requestContent": "{{REQUEST_CONTENT}}",
            "task": """Follow the protocol instructions provided in the requestContent to process tasks and create working plans. The requestContent contains both the protocol (from /agentlife/skills/project_thinking/protocols) and the task data (from /agentlife/tasks/new). Use the protocol's steps, decision_criteria, and example_output to guide your work.""",
        },

    "PROMPT_ANSWER_POSTS": {
            "requestContent": "{{REQUEST_CONTENT}}",
            "task": """Follow the protocol instructions to process the tasks and posts provided in requestContent.""",
    }
}

SYSTEM_CONTENT_TEMPLATES={
    "SYSTEM_EXECUTE_TASK":"""You are a citizen of Loopland - a virtual country for AI, robots and people. You are in project-manager mode. Follow the protocol instructions provided in the requestContent carefully. Use only standard double quotes for JSON and never single quotes or decorative quotes. Output must match the example_output format in the protocol."""
}

def isDirEmpty(args, sm):
  import os
  from core.services.loop_path_resolver import loop_path_resolver
  loop_id = sm.get_loop_id()
  user_id = sm.get_user_id()
  loop_fs_path = loop_path_resolver.get_file_system_by_user_and_loop(user_id, loop_id)
  cw_path = os.path.join(loop_fs_path, args[0])
  if not os.path.exists(cw_path) or len(os.listdir(cw_path)) == 0:
    return True
  return False