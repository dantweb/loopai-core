# src/controllers/loop_controller.py
import uuid, yaml, os

from core.adapters.broadcast_adapter import cleanup_session
from core.looper.looper import Looper
from core.services.session import session_manager

def get_session_manager():
    """Get the appropriate session manager based on execution context"""
    try:
        # First try the enhanced session manager (works in both thread and gevent contexts)
        if session_manager.has_current_session():
            return session_manager

        # If thread-safe session manager has active session, use it (backward compatibility)
        from core.services.thread_safe_session import thread_safe_session_manager
        if thread_safe_session_manager.has_current_session():
            return thread_safe_session_manager
    except:
        pass
    # Fall back to global session manager
    return session_manager


class LoopController:

    # var loop_file_path should be only absolute path. Use
    # get_file_system_by_user_and_loop(user_id, loop_id) to get the absolute path
    def __init__(self, loop_file_path, user_id, project_id, loop_id):
        current_session = get_session_manager()

        # Only create new session if one doesn't exist (backward compatibility)
        if not current_session.has_current_session():
            current_session.regenerate_session_id()
            current_session.set_user_id(user_id)
            current_session.set_project_id(project_id)
            current_session.set_loop_id(loop_id)
        else:
            # If session exists, just update project_id as it might be None initially
            if project_id:
                current_session.set_project_id(project_id)

        self.loop_file_path = loop_file_path

    async def run(self):
        with open(self.loop_file_path, 'r', encoding='utf-8') as file:
            loop_data = yaml.safe_load(file)

        code_source = loop_data['session']['code_source']

        looper = Looper(loop_data, code_source)
        steps = looper.get_steps()

        for index, step in enumerate(steps):
            index_uuid = str(uuid.uuid4())
            await step.execute(step.name, index_uuid)

        cleanup_session()