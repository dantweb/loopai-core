# src/controllers/loop_controller.py
import uuid, yaml, os

from core.adapters.broadcast_adapter import cleanup_session
from core.looper.looper import Looper
from core.services.logger_service import LoggerService
from core.services.session_dependent import SessionDependent


class LoopController(SessionDependent):

    # var loop_file_path should be only absolute path. Use
    # get_file_system_by_user_and_loop(user_id, loop_id) to get the absolute path
    def __init__(self, loop_file_path, user_id, project_id, loop_id, request_data=None):
        SessionDependent.__init__(self)

        # Note: In the new AsyncLoopManager architecture, session is already
        # set up by the thread context. This controller should just validate
        # that the session data matches the expected parameters.
        if self.has_session():
            # Verify session data matches expected parameters
            session_user_id = self.get_user_id()
            session_loop_id = self.get_loop_id()
            if (session_user_id != user_id or session_loop_id != loop_id):
                self.logger_service.warning(
                    f"Session data mismatch: session({session_user_id}, {session_loop_id}) "
                    f"vs expected({user_id}, {loop_id})"
                )

        self.loop_file_path = loop_file_path
        self.request_data = request_data  # Store request_data for use in loops
        self.logger_service = LoggerService()

    async def run(self):
        self.logger_service.info(f"[LoopController::run] Running loop from file: {self.loop_file_path}")
        with open(self.loop_file_path, 'r', encoding='utf-8') as file:
            loop_data = yaml.safe_load(file)

        code_source = loop_data['session']['code_source']

        looper = Looper(loop_data, code_source)
        steps = looper.get_steps()

        for index, step in enumerate(steps):
            index_uuid = str(uuid.uuid4())
            await step.execute(step.name, index_uuid)

