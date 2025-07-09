import json
from typing import Dict, Any
from flask import request, Flask, Response
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService
from core.adapters.file_adapter_interface import FileAdapterInterface
from core.services.session import session_manager

logger = LoggerService()


class HttpRequestAdapter(FileAdapterInterface):
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


    def read(self, step_id: str, *args: str) -> BroadcastData:
        """
        Reads the current HTTP request and packs it into a BroadcastData object.
        Handles POST, GET, PUT and other HTTP methods.

        Args:
            step_id (str): Identifier for the processing step
            *args (str): Additional arguments

        Returns:
            BroadcastData: Object containing the request data
        """
        if not request:
            logger.error("No request context available")
            return BroadcastData({})

        # Extract request method
        method = request.method

        # Initialize result dictionary
        result = {
            'method': method,
            'path': request.path,
            'url': request.url,
            'headers': dict(request.headers),
            'args': dict(request.args),
            'remote_addr': request.remote_addr
        }

        # Process body based on content type and method
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
                # Get raw data for other content types
                try:
                    result['body'] = request.get_data(as_text=True)
                except Exception as e:
                    logger.error(f"Error reading request body: {e}")
                    result['body'] = None
                    result['body_error'] = str(e)

        # For GET requests, just use the query parameters
        elif method == 'GET':
            result['query_params'] = dict(request.args)

        # Add cookies if present
        if request.cookies:
            result['cookies'] = dict(request.cookies)

        logger.info(f"Processed {method} request for path: {request.path}")

        return BroadcastData(result)


    def write(self, step_id: str, data: BroadcastData) -> bool:
        """
        Write method to send data as an HTTP response back to the client.

        Args:
            step_id (str): Identifier for the processing step.
            data (BroadcastData): Data to be written into the response.

        Returns:
            Response: Flask Response object containing the serialized data.
        """
        try:
            # Serialize the BroadcastData object to JSON
            response_body = data.to_json()  # Assuming BroadcastData has a `to_json` method
            bc = BroadcastData(response_body)
            session_manager.collect_broadcast(bc)
            logger.info(f"HttpRequest::write: Data for written to session_manager for step_id: {step_id}")
            return True
        except Exception as e:
            # Handle any exceptions and generate an error response
            logger.error(f"Error writing response for step_id: {step_id}, error: {e}")

            error_response = Response(
                response=json.dumps({"error": str(e)}),
                status=500,
                mimetype="application/json"
            )

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
