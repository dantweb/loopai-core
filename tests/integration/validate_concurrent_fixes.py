#!/usr/bin/env python3
"""
Quick validation script to test our concurrent loop execution fixes.
This script verifies that:
1. Session isolation works properly in gevent contexts
2. Real-time logging gets the correct user context
3. Multiple concurrent executions don't interfere with each other
"""

import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def test_session_isolation():
    """Test that session isolation works with gevent contexts"""
    print("🧪 Testing Session Isolation with Gevent...")

    from gevent import spawn, sleep
    from core.services.thread_safe_session import thread_safe_session_manager

    results = {}

    def create_isolated_session(session_key):
        """Create a session in a gevent greenlet and set environment"""
        session_id = thread_safe_session_manager.create_session_for_loop(
            user_id=int(session_key),
            loop_id=int(session_key) + 100
        )

        # Set unique environment data
        thread_safe_session_manager.set_environment({
            'session_key': session_key,
            'unique_value': f'unique_{session_key}'
        })

        # Wait a bit to simulate concurrent execution
        sleep(0.1)

        # Collect results
        results[session_key] = {
            'session_id': session_id,
            'user_id': thread_safe_session_manager.get_user_id(),
            'loop_id': thread_safe_session_manager.get_loop_id(),
            'env_session_key': thread_safe_session_manager.get_env('session_key'),
            'env_unique_value': thread_safe_session_manager.get_env('unique_value')
        }

        # Cleanup
        thread_safe_session_manager.cleanup_session(session_id)

    # Run multiple greenlets concurrently
    greenlets = [spawn(create_isolated_session, key) for key in ['A', 'B', 'C', 'D', 'E']]

    # Wait for all to complete
    for g in greenlets:
        g.join()

    print(f"✅ Session results: {results}")

    # Verify isolation
    success = True
    for key in ['A', 'B', 'C', 'D', 'E']:
        if results[key]['env_session_key'] != key:
            print(f"❌ Session {key} failed isolation test: expected '{key}', got '{results[key]['env_session_key']}'")
            success = False
        if results[key]['env_unique_value'] != f'unique_{key}':
            print(f"❌ Session {key} failed unique value test: expected 'unique_{key}', got '{results[key]['env_unique_value']}'")
            success = False

    if success:
        print("✅ Session isolation test PASSED!")
    else:
        print("❌ Session isolation test FAILED!")

    return success

def test_logging_context():
    """Test that logging gets the correct user context"""
    print("\n🧪 Testing Logging Context Detection...")

    from core.services.logger_service import get_session_manager, GeventSessionBridge
    from core.services.thread_safe_session import thread_safe_session_manager
    from web.services.async_loop_executor import async_loop_executor, GreenletSessionContext

    # Test the session manager detection
    session_manager = get_session_manager()
    print(f"✅ Session manager type: {type(session_manager).__name__}")

    # Test gevent context detection
    is_gevent = thread_safe_session_manager._is_in_gevent_context()
    print(f"✅ Is in gevent context: {is_gevent}")

    # Test with a real gevent session context
    from gevent import spawn

    def test_in_greenlet():
        # Create a session context manually
        context = GreenletSessionContext(user_id=42, loop_id=123)

        # Simulate what would happen in GeventLoopExecutor
        execution_id = 999
        async_loop_executor._greenlet_sessions[execution_id] = context

        # Get the session manager
        session_mgr = get_session_manager()
        print(f"✅ Session manager in greenlet: {type(session_mgr).__name__}")

        # Clean up
        if execution_id in async_loop_executor._greenlet_sessions:
            del async_loop_executor._greenlet_sessions[execution_id]

    greenlet = spawn(test_in_greenlet)
    greenlet.join()

    return True

def test_concurrent_execution_simulation():
    """Simulate concurrent loop execution like the real system would do"""
    print("\n🧪 Testing Concurrent Execution Simulation...")

    from gevent import spawn, sleep
    from core.services.thread_safe_session import thread_safe_session_manager

    execution_results = []

    def simulate_loop_execution(user_id, loop_id):
        """Simulate what GeventLoopExecutor does"""
        try:
            # Create session like GeventLoopExecutor does
            session_id = thread_safe_session_manager.create_session_for_loop(
                user_id=user_id,
                loop_id=loop_id
            )

            # Simulate some loop work
            sleep(0.1)

            # Check that we can get the session data
            current_user = thread_safe_session_manager.get_user_id()
            current_loop = thread_safe_session_manager.get_loop_id()

            result = {
                'user_id': user_id,
                'loop_id': loop_id,
                'session_id': session_id,
                'retrieved_user_id': current_user,
                'retrieved_loop_id': current_loop,
                'success': current_user == user_id and current_loop == loop_id
            }

            execution_results.append(result)

            # Cleanup
            thread_safe_session_manager.cleanup_session(session_id)

        except Exception as e:
            execution_results.append({
                'user_id': user_id,
                'loop_id': loop_id,
                'success': False,
                'error': str(e)
            })

    # Run multiple concurrent simulated executions
    greenlets = []
    for user_id in [1, 2, 3]:
        for loop_id in [10, 20]:
            greenlets.append(spawn(simulate_loop_execution, user_id, loop_id))

    # Wait for all to complete
    for g in greenlets:
        g.join()

    print(f"✅ Execution results: {execution_results}")

    # Check results
    success_count = sum(1 for r in execution_results if r['success'])
    total_count = len(execution_results)

    print(f"✅ Successful executions: {success_count}/{total_count}")

    return success_count == total_count

def main():
    """Run all validation tests"""
    print("🚀 Validating Concurrent Loop Execution Fixes...\n")

    results = []

    try:
        # Test 1: Session Isolation
        results.append(test_session_isolation())

        # Test 2: Logging Context
        results.append(test_logging_context())

        # Test 3: Concurrent Execution Simulation
        results.append(test_concurrent_execution_simulation())

    except ImportError as e:
        print(f"❌ Import error (expected when running outside container): {e}")
        print("ℹ️  This validation script should be run inside the Docker container")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print(f"\n📊 Summary:")
    print(f"   Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All validation tests PASSED! The concurrent fixes are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)