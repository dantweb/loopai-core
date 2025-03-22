# src/app.py
import argparse
from core.controllers.loop_controller import LoopController
from core.services.logger_service import LoggerService


def main():
    parser = argparse.ArgumentParser(description='Run the application with the specified command.')
    parser.add_argument('--loop', type=str, help='Path to the loop file.')
    parser.add_argument('--user', type=str, help='Web User ID')
    parser.add_argument('--loopId', type=str, help='Web Loop ID')
    parser.add_argument('--projectId', type=str, help='Web Project ID')
    args = parser.parse_args()

    if args.loop:
        controller = LoopController(args.loop, args.user, args.projectId, args.loopId)
        controller.run()
    else:
        logger_service = LoggerService()
        logger_service.error("No loop file provided. Use --help for more information.")


if __name__ == "__main__":
    main()
