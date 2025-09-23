from typing import Dict
from flask import request, Flask, has_request_context
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.adapters.file_adapter_interface import FileAdapterInterface

logger = LoggerService()


class RequestAdapter(FileAdapterInterface):
    """
    Adapter for handling HTTP requests (POST, GET, PUT) and converting them to BroadcastData objects.
    The read method processes incoming requests, while write method does nothing.
    """

    def __init__(self, app: Flask = None) -> None:
        """
        Initialize the HTTP Request Adapter.

        Args:
            app (Flask, optional): Flask application instance for context. Defaults to None.
        """
        self.app = app
        super().__init__()


    async def read(self, step_id: str, *args: str) -> BroadcastData:
        """
        Reads the HTTP request data from session and packs it into a BroadcastData object.
        Handles POST, GET, PUT and other HTTP methods.

        Args:
            step_id (str): Identifier for the processing step
            *args (str): Additional arguments

        Returns:
            BroadcastData: Object containing the request data
        """

        request_data = self.session_manager.get_request_data()

        if request_data:
            logger.info(f"[RequestAdapter::read] Found request data in session manager: {request_data}")
            return BroadcastData(request_data)

        # Fall back to trying direct Flask request access (for non-concurrent execution)
        if has_request_context() and request:
            logger.info("[RequestAdapter::read] Using direct Flask request context")
            method = request.method

            result = {
                'method': method,
                'path': request.path,
                'url': request.url,
                'args': dict(request.args),
                'remote_addr': request.remote_addr,
                'headers': dict(request.headers)
            }

            if method in ['POST', 'PUT', 'PATCH']:
                content_type = request.headers.get('Content-Type', '')

                if 'application/json' in content_type:
                    try:
                        result['body'] = request.get_json()
                    except Exception as e:
                        logger.error(f"Error parsing JSON body: {e}")
                        result['body'] = None
                        result['body_error'] = str(e)

                elif 'application/x-www-form-urlencoded' in content_type:
                    result['body'] = dict(request.form)

                elif 'multipart/form-data' in content_type:
                    # Handle form data
                    result['body'] = dict(request.form)
                    # Handle files
                    files = {}
                    for file_key in request.files:
                        file = request.files[file_key]
                        files[file_key] = {
                            'filename': file.filename,
                            'content_type': file.content_type,
                            'content_length': file.content_length,
                        }
                    result['files'] = files

                else:
                    try:
                        result['body'] = request.get_data(as_text=True)
                    except Exception as e:
                        logger.error(f"Error reading request body: {e}")
                        result['body'] = None
                        result['body_error'] = str(e)

            elif method == 'GET':
                result['query_params'] = dict(request.args)

            return BroadcastData(result)

        # No request context available
        logger.error("No request context available")
        return BroadcastData({"response": "No request context available"})

    async def write(self, step_id: str, data: BroadcastData) -> bool:

        try:
            self.add_broadcast_data(data)
            return True
        except Exception as e:
            logger.error(f"Error collecting broadcast: {e}")
            return False
