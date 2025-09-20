#!/usr/bin/env python3
"""
Test Runner for Agent RECEIVE_POST Flow Validation

This script runs comprehensive tests to validate that the
HTTP -> Lambda -> Filesystem flow works correctly for agent messaging.

Usage:
    python run_agent_flow_tests.py

This will help diagnose why agent_post tests are failing and
validate that the loop execution infrastructure can handle
the agent messaging scenarios correctly.
"""

import sys
import os
import subprocess
import json

def run_tests():
    """Run the agent flow tests and report results"""

    print("🚀 Running Agent RECEIVE_POST Flow Tests")
    print("=" * 60)
    print()

    try:
        # Run the integration test
        from test_agent_receive_post_flow import run_agent_receive_post_tests

        success = run_agent_receive_post_tests()

        if success:
            print()
            print("🎉 SUCCESS: All agent flow tests passed!")
            print()
            print("✅ Key validations completed:")
            print("   - HTTP adapter captures POST requests correctly")
            print("   - Lambda executor processes message data")
            print("   - Filesystem adapter creates files in agent inbox")
            print("   - End-to-end flow matches agent_post expectations")
            print("   - File creation and search works like agent_post tests")
            print()
            print("💡 The loop execution infrastructure is working correctly.")
            print("   The agent_post test failures are likely due to:")
            print("   1. Empty or incorrect WAKEUP.py lambda implementation")
            print("   2. Incorrect RECEIVE_POST.yaml configuration")
            print("   3. Filesystem adapter not processing the correct directory paths")
            print()
            return True
        else:
            print()
            print("❌ FAILURE: Some agent flow tests failed")
            print("   Check the test output above for details")
            print()
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the correct directory")
        print(f"   Current directory: {os.getcwd()}")
        return False

    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_sample_lambda_implementation():
    """Show the sample lambda implementation"""
    print()
    print("📝 Sample WAKEUP.py Implementation")
    print("=" * 60)
    print()
    print("To fix the agent_post tests, copy this to your agent's WAKEUP.py file:")
    print()

    try:
        with open('sample_receive_post_lambda.py', 'r') as f:
            content = f.read()

        print("```python")
        print(content)
        print("```")
        print()

    except FileNotFoundError:
        print("❌ sample_receive_post_lambda.py not found in current directory")
        print("   Make sure both files are in the same directory")

def main():
    """Main execution"""
    print("Agent RECEIVE_POST Flow Test Runner")
    print()

    # Run the tests
    success = run_tests()

    if not success:
        print()
        print("🔧 Troubleshooting Guide:")
        print("1. Check that the RECEIVE_POST.yaml loop configuration is correct")
        print("2. Ensure WAKEUP.py has proper lambda implementation")
        print("3. Verify filesystem adapter processes /agentlife/post/inbox/new correctly")
        print("4. Check that the HTTP adapter captures request data properly")
        print()
        show_sample_lambda_implementation()

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())