# src/controllers/loop_controller.py
import uuid, yaml, os
from core.looper.looper import Looper


class LoopController:

    # var loop_file_path should be only absolute path. Use
    # get_file_system_by_user_and_loop(user_id, loop_id) to get the absolute path
    def __init__(self, loop_file_path):
        self.loop_file_path = loop_file_path

    def run(self):
        with open(self.loop_file_path, 'r', encoding='utf-8') as file:
            loop_data = yaml.safe_load(file)

        code_source = loop_data['session']['code_source']
        looper = Looper(loop_data, code_source)
        steps = looper.get_steps()

        for index, step in enumerate(steps):
            index_uuid = str(uuid.uuid4())
            step.execute(step.name, index_uuid)
