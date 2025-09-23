#!/usr/bin/env python3
"""
Sample WAKEUP.py implementation for RECEIVE_POST action.

This is what should be in the agent's WAKEUP.py file to properly handle
the RECEIVE_POST action that agent_post tests expect.

This implementation:
1. Gets request data from the HTTP adapter
2. Extracts message information from the nested structure
3. Creates files in the agent's inbox directory
4. Broadcasts the result for the filesystem adapter
"""

import json
import os
from datetime import datetime


def process_receive_post(request_data):
    """
    Process RECEIVE_POST action from agent_post service.

    Expected request_data structure (from agent_post):
    {
        'method': 'POST',
        'body': {
            'result': {
                'result': {
                    'updated_files': [
                        {
                            'path': 'dir_save_123456.json',
                            'file_operation': 'update',
                            'file_content': '{"message": {...}}'
                        }
                    ]
                }
            }
        }
    }
    """
    print(f"🔄 Processing RECEIVE_POST action...")

    try:
        # Extract the request body
        body = request_data.get('body', {})
        print(f"📥 Request body keys: {list(body.keys())}")

        # Navigate the nested structure that agent_post sends
        result_data = body.get('result', {})
        if not result_data:
            print("⚠️  No 'result' key in body")
            return {'error': 'No result data found in request'}

        inner_result = result_data.get('result', {})
        if not inner_result:
            print("⚠️  No inner 'result' key found")
            return {'error': 'No inner result data found'}

        updated_files = inner_result.get('updated_files', [])
        if not updated_files:
            print("⚠️  No 'updated_files' found")
            return {'error': 'No updated_files in request'}

        print(f"📂 Found {len(updated_files)} files to process")

        # Process each file for the filesystem adapter
        processed_files = []

        for file_data in updated_files:
            if not isinstance(file_data, dict):
                continue

            path = file_data.get('path')
            file_content = file_data.get('file_content')
            file_operation = file_data.get('file_operation', 'create')

            if not path or not file_content:
                print(f"⚠️  Skipping incomplete file data: {file_data}")
                continue

            # Validate that file_content contains a message
            try:
                if isinstance(file_content, str):
                    content_data = json.loads(file_content)
                else:
                    content_data = file_content

                message = content_data.get('message', {})
                if not message:
                    print(f"⚠️  No message found in file content")
                    continue

                message_id = message.get('id')
                from_addr = message.get('from')
                to_addr = message.get('to')

                print(f"📧 Processing message: ID={message_id}, From={from_addr}, To={to_addr}")

            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️  Error parsing file content: {e}")
                continue

            # Add to processed files list
            processed_files.append({
                'path': path,
                'file_operation': file_operation,
                'file_content': file_content
            })

        print(f"✅ Processed {len(processed_files)} files successfully")

        # Return the result that filesystem adapter expects
        return {
            'updated_files': processed_files
        }

    except Exception as e:
        error_msg = f"Error processing RECEIVE_POST: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}


def main():
    """
    Main execution function for lambda executor.

    This is called when the RECEIVE_POST.yaml loop is executed.
    """
    print("🚀 RECEIVE_POST lambda executor starting...")

    try:
        # Import session manager to get request data
        from core.services.session_manager import session_manager

        # Get the request data from HTTP adapter
        request_data = session_manager.get_request_data()

        if not request_data:
            print("❌ No request data found in session")
            result = {'error': 'No request data available'}
        else:
            print(f"📨 Request method: {request_data.get('method')}")
            print(f"📍 Request path: {request_data.get('path')}")

            # Process the RECEIVE_POST request
            result = process_receive_post(request_data)

        # Broadcast the result for filesystem adapter
        session_manager.collect_broadcast({'result': result})

        print("✅ RECEIVE_POST processing completed")

    except Exception as e:
        error_msg = f"Fatal error in RECEIVE_POST lambda: {str(e)}"
        print(f"💥 {error_msg}")

        # Still try to broadcast the error
        try:
            from core.services.session_manager import session_manager
            session_manager.collect_broadcast({'result': {'error': error_msg}})
        except:
            pass


# Template variables (can be used by other parts of the system)
PROMPT_TEMPLATES = {
    'receive_post': 'Processing incoming agent message: {message_content}',
    'file_created': 'Created inbox file: {filename}'
}

SYSTEM_CONTENT_TEMPLATES = {
    'agent_inbox': 'Agent inbox directory: {inbox_path}',
    'message_format': 'Expected message format: {format_spec}'
}


# Main execution when called as lambda
if __name__ == "__main__":
    main()