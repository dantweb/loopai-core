# src/models/step_model.py
import importlib.util
import os
from typing import List, Dict

from PIL.Image import Image
from dotenv import load_dotenv
from sqlalchemy import nulls_last

from core.adapters.broadcast_adapter import BroadcastAdapter
from core.adapters.file_adapter_interface import FileAdapterInterface, get_loop_config_base_path_by_user_and_loop, \
    get_file_system_by_user_and_loop
from core.adapters.filesystem_adapter import FilesystemAdapter
from core.databus import global_vars
import config
from core.looper.executors.bash_executor import BashExecutor
from core.looper.executors.gpt2code_executor import Gpt2codeExecutor
from core.looper.executors.gpt_executor import GptExecutor
from core.looper.executors.wordpress_executor import WordpressExecutor
from core.models.action_config import ActionConfig
from core.models.broadcast_data import BroadcastData
from core.models.input_config import InputConfig
from core.models.output_config import OutputConfig
from core.services.logger_service import LoggerService

logger = LoggerService()

class StepModel:
    def __init__(self,
                 name: str,
                 description: str,
                 step_type: str,
                 step_input: List[InputConfig],
                 output: List[OutputConfig],
                 action: ActionConfig,
                 loop_data: str,
                 code_source: str
                ):
        self.logger_service = LoggerService()
        self.loop_python_src = None
        self.packed_blob = {}
        self.name = name
        self.env_filename = '.env'
        self.description = description
        self.type = step_type
        self.input = step_input
        self.output = output
        self.action = action
        self.max_tokens = action.max_tokens

        self.executor = None
        self.output_adapters = []
        self.input_adapters = []

        global_vars.global_step_name = name
        global_vars.global_loop_index = 'start'

        # Parse the loop YAML file to get the code source path
        self.loop_data = loop_data
        self.code_source = code_source
        self.code_module = self.load_code_module(self.code_source)

        for output_config in self.output:
            if output_config.csv:
                if output_config.csv['fields']:
                    fields = self.get_variable_from_py_template(output_config.csv['fields'])
                    logger.info(f"[StepModel::__init__] CSV step {self.name} has defined Fields: {str(fields)}")
                else:
                    fields = []

                if output_config.csv['mapping']:
                    mapping = self.get_variable_from_py_template(output_config.csv['mapping'])
                    logger.info(f"[StepModel::__init__] CSV step {self.name} has defined mapping: {str(mapping)}")
                else:
                    mapping = {}

                output_adapter_class = self.load_adapter('csv')
                self.output_adapters.append(
                    output_adapter_class(
                        output_config.csv['name'],
                        fields,
                        mapping
                    )
                )

            if output_config.text:
                output_adapter_class = self.load_adapter('text')
                self.output_adapters.append(output_adapter_class(output_config.text['name']))
            if output_config.image:
                output_adapter_class = self.load_adapter('image')
                self.output_adapters.append(output_adapter_class(output_config.image['name']))
            if output_config.wordpress:
                output_adapter_class = self.load_adapter('wordpress')
                wp_site = os.getenv(output_config.wordpress['wp_site'])
                wp_username = os.getenv(output_config.wordpress['wp_username'])
                wp_password = os.getenv(output_config.wordpress['wp_password'])
                self.output_adapters.append(
                    output_adapter_class(
                        connector_id = output_config.wordpress['connector'],
                        wp_site = wp_site,
                        wp_username = wp_username,
                        wp_application_password = wp_password,
                    )
                )

            if output_config.filesystem:
                output_adapter_class = self.load_adapter('filesystem')
                self.output_adapters.append(
                    output_adapter_class(
                        output_config.filesystem['code_dir'],
                        config.GLOBAL_USER_ID,
                        config.GLOBAL_LOOP_ID
                    )
                )
            if output_config.broadcast:
                output_adapter_class = self.load_adapter('broadcast')
                if isinstance(output_config.broadcast, dict) and 'image_file' in output_config.broadcast:
                    self.broadcast_image_file = output_config.broadcast['image_file']
                self.output_adapters.append(output_adapter_class())

        for input_config in self.input:
            if input_config.csv:
                if input_config.csv['fields']:
                    fields = self.get_variable_from_py_template(input_config.csv['fields'])
                    logger.info(f"[StepModel::__init__] CSV step {self.name} has defined Fields: {str(fields)}")
                else:
                    fields = []

                if input_config.csv['mapping']:
                    mapping = self.get_variable_from_py_template(input_config.csv['mapping'])
                    logger.info(f"[StepModel::__init__] CSV step {self.name} has defined mapping: {str(mapping)}")
                else:
                    mapping = {}

                input_adapter_class = self.load_adapter('csv')
                self.input_adapters.append(
                    input_adapter_class(
                        input_config.csv['name'],
                        fields,
                        mapping
                    )
                )

            if input_config.text:
                input_adapter_class = self.load_adapter('text')
                self.input_adapters.append(input_adapter_class(input_config.text['name']))
            if input_config.image:
                input_adapter_class = self.load_adapter('image')
                self.input_adapters.append(input_adapter_class(input_config.image['name']))
            if input_config.broadcast:
                input_adapter_class = self.load_adapter('broadcast')
                self.input_adapters.append(input_adapter_class())
            if input_config.filesystem:
                input_adapter_class = self.load_adapter('filesystem')
                self.input_adapters.append(
                    input_adapter_class(
                        input_config.filesystem['code_dir'],
                        config.GLOBAL_USER_ID,
                        config.GLOBAL_LOOP_ID
                    )
                )


    def get_system_content(self, variable_name: str) -> str:
        spec = importlib.util.spec_from_file_location(
            "module.name", os.getcwd() + '/../..' + self.loop_python_src
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, variable_name)


    def load_adapter(self, adapter_type: str):
        module_name = f"core.adapters.{adapter_type}_adapter"
        class_name = f"{adapter_type.capitalize()}Adapter"
        module = importlib.import_module(module_name)
        adapter_class = getattr(module, class_name)
        return adapter_class


    def load_executor(self, executor_type: str):
        module_name = f"core.looper.executors.{executor_type}_executor"
        class_name = f"{executor_type.capitalize()}Executor"
        module = importlib.import_module(module_name)
        executor_class = getattr(module, class_name)
        return executor_class


    def execute(self, step_name: str, loop_index: str):
        global_vars.global_step_name = step_name
        global_vars.global_loop_index = loop_index
        step_input_data = []
        # Load executor
        executor_class = self.load_executor(self.action.executor)
        self.executor = executor_class(self.action.model)
        logger.info(f"[StepModel::execute] step name '{step_name}'...")
        logger.info(f"[StepModel::execute] executor of this step is '{self.action.executor}'...")
        logger.info(f"[StepModel::execute] input adapters (total={len(self.input_adapters)}) {self.input_adapters}...")
        logger.info(f"[StepModel::execute] input variable has {self.input}...")
        logger.info(f"\n\n[StepModel::execute] enumerate input adapters  {enumerate(self.input_adapters)}... \n\n")
        adapters_count = 0
        for index, input_adapter in enumerate(self.input_adapters):
            adapters_count += 1
            logger.info(f"input_adapter counter: {adapters_count} / {len(self.input_adapters)}")
            logger.info(f"[StepModel::execute] step {step_name}; input length={len(self.input)} index={index} adapter={input_adapter.__class__}")

            if index < len(self.input):
                input_item = self.input[index]
                if input_item.broadcast and input_item.broadcast.get('source'):
                    logger.info(f"[StepModel::execute] !!!! input_item.broadcast['source'] = {input_item.broadcast['source']}")
                    first_parameter = self.name
                    second_parameter = input_item.broadcast['source']
                else:
                    logger.info(f"[StepModel::execute] input_item.broadcast['source'] is not defined")
                    first_parameter = self.name
                    second_parameter = None

                if input_item.field and input_item.output_format:
                    input_adapter.setAdditionalParams(
                        input_item.output_format,
                        input_item.field,
                    )
            else:
                logger.info(f"[StepModel::execute] self.input contains: \n {str(self.input)} \n")
                # Since index is out of bounds, handle accordingly
                first_parameter = self.name
                second_parameter = 'not_defined'

            logger.info(f"[StepModel::execute] args for adapter a1={first_parameter} a2={second_parameter}")

            if isinstance(self.executor, WordpressExecutor) or isinstance(input_adapter, BroadcastAdapter):
                fresh_data_from_input = input_adapter.read(first_parameter, second_parameter, ignore_read_status=True)
            elif isinstance(self.executor, Gpt2codeExecutor) and isinstance(input_adapter, FilesystemAdapter):
                fresh_data_from_input = input_adapter.read(first_parameter)
            else:
                fresh_data_from_input = input_adapter.read(first_parameter, second_parameter)

            logger.info(f"[StepModel::execute] Read data from adapter {input_adapter.__class__}")
            logger.info(f"[StepModel::execute] Data we have read: {fresh_data_from_input}")
            logger.info(f"[StepModel::execute] Type of data read: {type(fresh_data_from_input)}")

            if fresh_data_from_input is None or fresh_data_from_input == 'None':
                err = f"Data is empty for {input_adapter.__class__} step {self.name} parent {first_parameter}"
                logger.info(err)
                raise Exception(err)

            logger.info(f"[StepModel::execute] step_input_data: {step_input_data}")

            if self.type == 'foreach' or self.type == 'generate_image':
                step_input_data = fresh_data_from_input
                break

            step_input_data.append(fresh_data_from_input)

        logger.info(f"[StepModel::execute] This is all data we have collected for the executor '{self.type}' data type of {type(step_input_data)}: {step_input_data}")

        step_id = self.name
        if step_input_data is None:
            msg = f"step_input_data is None at step  {step_id}"
            logger.info(msg)
            raise RuntimeError(msg)

        if self.type == 'foreach':
            self.run_foreach(step_input_data)
            return 'foreach_end'

        prompt_template = self.get_prompt_templates().get(self.action.prompt)

        if prompt_template is None and self.action.prompt:
            prompt_template = self.get_variable_from_py_template(self.action.prompt)

        logger.info(f"[StepModel::execute] prompt name : {self.action.prompt}")
        logger.info(f"[StepModel::execute] prompt template : {prompt_template}")
        logger.info(f"[StepModel::execute] system content template typeOf ({type(prompt_template)}) : {prompt_template}")

        logger.info(f"[StepModel::execute:get_system_content_templates] typeof ({type(self.get_system_content_templates())}): {str(self.get_system_content_templates())}")
        system_content = self.get_system_content_templates().get(self.action.system_content)

        if system_content is None and self.action.system_content:
            system_content = self.get_variable_from_py_template(self.action.system_content)

        logger.info(f"[StepModel::execute] system content name : {self.action.system_content}")
        logger.info(f"[StepModel::execute] system content template typeOf ({type(system_content)}) : {system_content}")


        # Create prompt - reading context only from first input source
        prompt = self.executor.prepare_prompt(
            step_input_data,
            prompt_template
        )

        logger.info(f"[StepModel::execute] Prompt: {prompt}")
        logger.info(f"[StepModel::execute] Prompt type: {type(prompt)}")

        prompt = BroadcastData(prompt)

        if isinstance(self.executor, WordpressExecutor):
            result = step_input_data
        elif isinstance(self.executor, BashExecutor):
            config = self.action.config if hasattr(self.action, 'config') else {}
            result = self.executor.run(
                self.action.model,
                system_content,
                prompt,
                self.action.max_tokens,
                config
            )
        else:
            result = self.executor.run(
                self.action.model,
                system_content,
                prompt,
                self.action.max_tokens
            )

        # Write output
        step_id = self.name  # or another appropriate identifier

        self.packed_blob['model_id'] = self.action.model
        self.packed_blob['step_id'] = step_id
        self.packed_blob['result'] = result

        self.write(step_id)
        self.cleanup(step_id)

        return self.packed_blob

    def write(self, step_id: str):

        self.logger_service.log(f"Step {self.name} tries to save data typeof({type(self.packed_blob['result'])}) {self.packed_blob['result']} ")

        for output_adapter in self.output_adapters:

            if isinstance(output_adapter, BroadcastAdapter) and isinstance(self.packed_blob['result'], Image):
                self.packed_blob['image_file'] = FileAdapterInterface.get_full_path(self, self.broadcast_image_file)

            broadcast_data = BroadcastData(self.packed_blob)

            self.logger_service.log(f"Trying so save {self.name} adapter {output_adapter.__class__} BroadcastData {str(broadcast_data)}")

            try:
                a = output_adapter.write(step_id, broadcast_data)
                if a is True:
                    self.logger_service.log(f"Step \"{self.name}\" is saved by the adapter {output_adapter.__class__} ")
                else:
                    self.logger_service.error(f"Cannot save the step data\"{self.name}\" by the adapter {output_adapter.__class__}")
            except Exception as e:
                self.logger_service.error(e)
                raise

    def run_foreach(self, input_data):
        msg = f"[StepModel::run_foreach] for the step '{self.name}'"
        self.logger_service.info(msg)
        self.executor.set_loop(self.loop_data)
        self.executor.set_parent_step(self.name)
        self.executor.set_foreach_data(input_data)
        self.executor.set_output_adapters(self.output_adapters)
        self.executor.run(self.action.model, '', '', '')

    def cleanup(self, step_id):

        pass

    def get_prompt_templates(self):
        return self.get_variable_from_py_template('PROMPT_TEMPLATES')

    def get_system_content_templates(self):
        return self.get_variable_from_py_template('SYSTEM_CONTENT_TEMPLATES')

    def get_variable_from_py_template(self, variable_name: str):
        logger.info(f"[StepModel::get_variable_from_py_template] Getting variable: {variable_name}")
        return getattr(self.code_module, variable_name)

    def load_code_module(self, module_path: str):
        module_absolute_path = os.path.join(
            get_loop_config_base_path_by_user_and_loop(config.GLOBAL_USER_ID, config.GLOBAL_LOOP_ID),
            module_path
        )

        logger.info(f"[StepModel::load_code_module] Loading module from path: {module_absolute_path}")

        module_name = os.path.basename(module_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, module_absolute_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        logger.info(f"[StepModel::load_code_module] Module loaded: {module}")

        return module
