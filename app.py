# src/app.py
import argparse
import os

from dotenv import load_dotenv

from core.adapters.file_adapter_interface import get_loop_config_base_path_by_user_and_loop
from core.controllers.loop_controller import LoopController
import app_global_config as config
from core.databus import global_vars
from core.services.logger_service import LoggerService


def main():
    parser = argparse.ArgumentParser(description='Run the application with the specified command.')
    parser.add_argument('--loop', type=str, help='Path to the loop file.')
    parser.add_argument('--user', type=str, help='Web User ID')
    parser.add_argument('--loopId', type=str, help='Web Loop ID')
    args = parser.parse_args()

    if args.user:
        config.GLOBAL_USER_ID = args.user

    if args.loopId:
        config.GLOBAL_LOOP_ID = args.loopId

    if args.loop:
        controller = LoopController(args.loop)
        controller.run()
    else:
        logger_service = LoggerService()
        logger_service.error("No loop file provided. Use --help for more information.")


if __name__ == "__main__":
    main()
