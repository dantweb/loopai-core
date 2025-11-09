# src/controllers/loop_controller.py
import uuid
import yaml
from core.looper.looper import Looper
from core.services.logger_service import LoggerService
from core.services.session_dependent import SessionDependent


class LoopController(SessionDependent):
    # var loop_file_path should be only absolute path. Use
    # get_file_system_by_user_and_loop(user_id, loop_id) to get the absolute path

    def __init__(self, loop_file_path, user_id, project_id, loop_id, request_data=None):
        SessionDependent.__init__(self)
        self.logger_service = LoggerService()

        # Note: In the new AsyncLoopManager architecture, session is already
        # set up by the thread context. This controller should just validate
        # that the session data matches the expected parameters.
        if self.has_session():
            # Verify session data matches expected parameters
            session_user_id = self.get_user_id()
            session_loop_id = self.get_loop_id()
            if session_user_id != user_id or session_loop_id != loop_id:
                self.logger_service.warning(
                    f"Session data mismatch: session({session_user_id}, {session_loop_id}) "
                    f"vs expected({user_id}, {loop_id})"
                )

        self.loop_file_path = loop_file_path
        self.request_data = request_data  # Store request_data for use in loops

    def run(self):
        self.logger_service.info(f"[LoopController::run] Running loop from file: {self.loop_file_path}")
        with open(self.loop_file_path, 'r', encoding='utf-8') as file:
            loop_data = yaml.safe_load(file)

        code_source = loop_data['session']['code_source']
        looper = Looper(loop_data, code_source)
        steps = looper.get_steps()

        # Precompute index lookup for efficient jumps
        step_index_map = {step.name: i for i, step in enumerate(steps)}

        execution_result_packed_blob = {}
        # Optional: If you need to accumulate all results:
        results = {}
        current_index = 0

        while current_index < len(steps):
            step = steps[current_index]
            index_uuid = str(uuid.uuid4())

            execution_result_packed_blob = step.execute(step.name, index_uuid)
            # Optional: Accumulate if needed, e.g.:
            results[step.name] = execution_result_packed_blob.copy()

            if 'next' in execution_result_packed_blob:
                next_step_name = execution_result_packed_blob['next']
                current_index = step_index_map.get(next_step_name)

                if current_index is None:
                    self.logger_service.warning(f"[LoopController::run] Next step '{next_step_name}' not found in steps")
                    break
            else:
                # No 'next': proceed to the sequential next step
                current_index += 1

            #Prevent cycles (uncomment if workflows might loop back)
            visited = set()  # Initialize outside loop
            if current_index in visited:
                self.logger_service.warning(f"[LoopController::run] Cycle detected at step '{step.name}'")
                break
            visited.add(current_index)

        return execution_result_packed_blob