#!/usr/bin/env python3
"""
Production test to verify session bridge works in real environment.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from core.services.session import session_manager
from core.services.thread_safe_session import thread_safe_session_manager

def test_session_bridge():
    """Test the session bridge in production environment"""
    print("🧪 Testing Session Bridge in Production Environment")

    try:
        # Test 1: Check if bridge method exists
        has_method = hasattr(session_manager, 'get_request_data')
        print(f"✅ session_manager.get_request_data() method exists: {has_method}")

        if not has_method:
            print("❌ CRITICAL: Bridge method not found!")
            return False

        # Test 2: Create session and store data
        session_id = thread_safe_session_manager.create_session_for_loop(
            user_id=1, loop_id=999, project_id=1
        )

        test_data = {
            'method': 'POST',
            'path': '/test/bridge',
            'body': {'test': 'bridge_verification'}
        }

        thread_safe_session_manager.set_request_data(test_data)
        print(f"✅ Stored test data in thread_safe_session_manager")

        # Test 3: Access via bridge
        bridge_data = session_manager.get_request_data()
        bridge_success = bridge_data is not None and bridge_data.get('method') == 'POST'

        print(f"✅ Bridge access successful: {bridge_success}")

        if bridge_success:
            print(f"📋 Bridge retrieved data: {bridge_data.get('method')} {bridge_data.get('path')}")
        else:
            print(f"❌ Bridge failed - got: {bridge_data}")

        # Cleanup
        thread_safe_session_manager.cleanup_session(session_id)

        return bridge_success

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_session_bridge()
    exit(0 if success else 1)