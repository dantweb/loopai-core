# src/looper/looper.py
import os
from typing import List
import app_global_config as config
from dotenv import load_dotenv

from core.adapters.file_adapter_interface import get_loop_config_base_path_by_user_and_loop
from core.databus import global_vars
from core.models.action_config import ActionConfig
from core.models.input_config import InputConfig
from core.models.output_config import OutputConfig
from core.models.step_model import StepModel
from core.services.logger_service import LoggerService
from web.services.socket_io_service import socket

class Looper:
    def __init__(self, loop_data: str, code_source: str, parent_step: str = None):
        self.iterable_steps = None
        self.loop_data = loop_data
        self.code_source = code_source
        if parent_step is None:
            self.iteratable_steps = self.loop_data['session']['loop']
        else:
            self.iteratable_steps = self.loop_data['session']['loop'][parent_step]['action']['loop']

    def get_steps(self) -> List[StepModel]:
        logger = LoggerService()
        logger.info('Reading stepps...')
        steps = []
        for step_name, step_details in self.iteratable_steps.items():
            logger.info(f"now into step configuration: {step_name}")
            input_config = [
                InputConfig(
                    text=step_input_config.get('text') if 'text' in step_input_config else None,
                    image=step_input_config.get('image') if 'image' in step_input_config else None,
                    csv=step_input_config.get('csv') if 'csv' in step_input_config else None,
                    broadcast=step_input_config.get('broadcast') if 'broadcast' in step_input_config else None,
                    source=step_input_config.get('broadcast').get('source') if 'broadcast' in step_input_config and 'source' in step_input_config['broadcast'] else None,
                    output_format=step_input_config.get('broadcast').get('output_format') if 'broadcast' in step_input_config and 'output_format' in step_input_config['broadcast'] else None,
                    field=step_input_config.get('broadcast').get('field') if 'broadcast' in step_input_config and 'field' in step_input_config['broadcast'] else None,
                    filesystem=step_input_config.get('filesystem') if 'filesystem' in step_input_config else None
                ) for step_input_config in step_details['input']
            ]
            output_config = [
                OutputConfig(
                    text=output.get('text'),
                    csv=output.get('csv'),
                    broadcast=output.get('broadcast', False),
                    image=output.get('image'),
                    wordpress=output.get('wordpress'),
                    filesystem=output.get('filesystem') if 'filesystem' in output else None
                ) for output in step_details['output']
            ]
            action_config = ActionConfig(
                model=step_details['action']['model'] if 'model' in step_details['action'] else None,
                prompt=step_details['action']['prompt'] if 'prompt' in step_details['action'] else None,
                system_content=step_details['action']['system_content'] if 'system_content' in step_details['action'] else None,
                max_tokens=step_details['action']['max_tokens'] if 'max_tokens' in step_details['action'] else None,
                config=step_details['action']['config'] if 'config' in step_details['action'] else None,
                executor=step_details['action'].get('executor')  # Optional argument
            )
            step = StepModel(
                name=step_name,
                description=step_details['description'],
                step_type=step_details['type'],
                step_input=input_config,
                output=output_config,
                action=action_config,
                loop_data=self.loop_data,
                code_source=self.code_source
            )
            steps.append(step)
            logger.info(f"Step {step_name} added to steps")
        return steps

    def set_iterable_steps(self, iterable_steps: List[StepModel]):
        self.iterable_steps = iterable_steps
