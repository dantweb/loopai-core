##filepath: ./loopai_src/core/services/loop_path_resolver.py
import os

from gevent import sleep

from core.services.logger_service import LoggerService
from core.services.session_manager import SessionManager
from web.admin_models import Loop
import app_global_config as config

class LoopPathResolver:

    def get_loop_config_path(self, loop: Loop):
        filesystem_path = self.get_file_system_by_user_and_loop(str(loop.user_id), str(loop.id))
        config_path = filesystem_path.replace('filesystem', 'config')
        sleep(0)
        return config_path

    def get_loop_filesystem_path(self, loop: Loop):
        filesystem_path = self.get_file_system_by_user_and_loop(str(loop.user_id), str(loop.id))
        sleep(0)
        return filesystem_path

    def get_file_system_by_user_and_loop(self, user_id: str, loop_id: str):

        if config.WEB_OR_CLI == 'cli':
            path_root = config.LOOPAI_SINGLE_FILESYSTEM_PATH
        else:
            path_root = config.LOOPAI_WEB_USERS_FILESYSTEM_PATH

        path = os.path.join(
            path_root,
            str(user_id),
            'loops',
            str(loop_id),
            'filesystem'
        )
        return path

    def get_loop_config_base_path_by_user_and_loop(self, user_id: str, loop_id: str):

        if config.WEB_OR_CLI == 'cli':
            path_root = config.LOOPAI_SINGLE_FILESYSTEM_PATH
        else:
            path_root = config.LOOPAI_WEB_USERS_FILESYSTEM_PATH

        path = os.path.join(
            path_root,
            str(user_id),
            'loops',
            str(loop_id),
            'config'
        )

        return path

    def get_full_path(self, session_manager: SessionManager, file_path_template: str) -> str:
        # Use the appropriate session manager

        loop_index = session_manager.get_loop_index()
        step = session_manager.get_global_step_name()
        path = f"loop.{step}.{loop_index}"
        user_id = session_manager.get_user_id()
        loop_id = session_manager.get_loop_id()

        # Add debug logging
        logger = LoggerService(component="core")
        logger.info(f"[get_full_path] Using session manager: {type(session_manager).__name__}")
        logger.info(f"[get_full_path] User ID: {user_id}, Loop ID: {loop_id}")

        session_id = session_manager.get_session_id()
        session_id_short = session_id[:8] if session_id else 'no-session'

        last_part_of_the_path: str = file_path_template.replace(
            '{{SESSION_ID}}', session_id_short
        ).replace(
            '{{FOREACH_STEP_UUID}}', str(loop_index)
        ).replace('{{PATH}}', path)

        base_path = self.get_file_system_by_user_and_loop(user_id, loop_id)

        full_path = f'{base_path}/{last_part_of_the_path}'
        logger.info(f"[get_full_path] Resolved path: {full_path}")

        return full_path

loop_path_resolver = LoopPathResolver()