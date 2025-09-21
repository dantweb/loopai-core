import json
import logging
import os
from typing import Dict, Any
from flask import request, Flask, Response, session, has_request_context, g
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.adapters.file_adapter_interface import FileAdapterInterface, get_file_system_by_user_and_loop
from core.services.session import session_manager
from core.services.thread_safe_session import thread_safe_session_manager

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
        # Try to get request data from appropriate session manager first
        def get_current_session_manager():
            """Get the appropriate session manager based on execution context"""
            try:
                from core.services.session import session_manager
                # First try the enhanced session manager (works in both thread and gevent contexts)
                if session_manager.has_current_session():
                    return session_manager

                # If thread-safe session manager has active session, use it (backward compatibility)
                if thread_safe_session_manager.has_current_session():
                    return thread_safe_session_manager
            except:
                pass
            # Fall back to global session manager
            from core.services.session import session_manager
            return session_manager

        current_session = get_current_session_manager()
        request_data = current_session.get_request_data()

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
            session_manager.collect_broadcast(data)
            return True
        except Exception as e:
            logger.error(f"Error collecting broadcast: {e}")
            return False


    def _extract_content_type(self, headers: Dict[str, str]) -> str:
        """
        Helper method to extract content type from headers.

        Args:
            headers (Dict[str, str]): Request headers

        Returns:
            str: Content type string
        """
        content_type = headers.get('Content-Type', '')
        if ';' in content_type:
            # Split and get the main content type
            content_type = content_type.split(';')[0].strip()
        return content_type
