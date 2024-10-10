# .loopai_src/core/looper/executors/foreach_executor.py
import uuid
from collections.abc import Iterable
from typing import List

import pandas as pd
from dotenv import load_dotenv

from core.adapters.adapter_interface import AdapterInterface
from core.adapters.broadcast_adapter import BroadcastAdapter
from core.databus import global_vars
from core.looper.executors.executor_interface import ExecutorInterface
from core.looper.looper import Looper
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService

load_dotenv()

logger = LoggerService()

class ForeachExecutor(ExecutorInterface):
    def __init__(self, model: str):
        super().__init__(model)
        self.foreach_data = None
        self.input_data = None
        self.loop_data = None
        self.loop_data_foreach = None
        self.result = []
        self.output_adapters: List[AdapterInterface] = []

    def prepare_prompt(self, input_data, prompt_template: str) -> str:
        pass

    def set_foreach_data(self, foreach_data) -> str:
        self.foreach_data = foreach_data

    def run(self, model, system_content, user_content, max_tokens):
        logger.info(f"[ForeachExecutor::run] ..going to call Foreach")

        looper = Looper(self.loop_data, self.loop_data['session']['code_source'], self.parent_step)
        steps = looper.get_steps()

        if isinstance(self.foreach_data, Iterable):
            self.logger_service.log(f"[ForeachExecutor::run] data  type: {type(self.foreach_data)}")
            self.logger_service.log(f"[ForeachExecutor::run] data : {self.foreach_data}")

            if all(isinstance(df, pd.DataFrame) for df in self.foreach_data):
                rows_as_dicts = []
                for df in self.foreach_data:
                    rows_as_dicts.extend(df.to_dict(orient='records'))

                self.logger_service.log(f"[ForeachExecutor::run] data converted to list of dicts, length: {len(rows_as_dicts)}")

                for row in rows_as_dicts:
                    self.process_row_and_execute_steps(row, steps)
            # Handle if foreach_data is a plain list
            elif isinstance(self.foreach_data, list):
                self.logger_service.log(f"[ForeachExecutor::run] data is a list with length: {len(self.foreach_data)}")

                for item in self.foreach_data:
                    self.process_row_and_execute_steps(item, steps)
            else:
                raise ValueError("Foreach data must be either a list of pandas DataFrames or a list of other elements.")

    def set_output_adapters(self, adapters: List[AdapterInterface]):
        self.output_adapters: list[AdapterInterface] = adapters

    def send_data_to_output_adapters(self, step_id: str, data):
        for adapter in self.output_adapters:
            adapter.write(step_id, data)

    def set_loop(self, loop_data):
        self.loop_data = loop_data

    def cleanup_broadcast(self):
        broadcast_adapter = BroadcastAdapter()
        broadcast_adapter.delete_entries_by_session_id()

    def process_row_and_execute_steps(self, row, steps):
        logger.info(f"[ForeachExecutor::process_row_and_execute_steps] Processing row data: {row}")
        logger.info(f"[ForeachExecutor::process_row_and_execute_steps] Datatype is: {type(row)}")

        broadcast_data = BroadcastData(row)
        self.send_data_to_output_adapters(self.parent_step, broadcast_data)
        global_vars.global_loop_index = str(uuid.uuid4())
        for step in steps:
            global_vars.global_step_name = str(uuid.uuid4())
            step.execute(global_vars.global_step_name, global_vars.global_loop_index)
        self.cleanup_broadcast()
