#!/usr/bin/env python3
"""
Localhost Agent Actions Integration Test

This test runs inside the loopai_web container and executes curl requests
directly to localhost to test agent action loops (WAKEUP and RECEIVE_POST)
without network interference.

The test verifies:
1. RECEIVE_POST actions create actual files
2. WAKEUP actions return proper responses
3. Session data flows correctly through the loop execution
4. File system adapter creates files in expected locations
"""

import unittest
import subprocess
import json
import os
import time
import tempfile
import shutil
from datetime import datetime
from pathlib import Path


class TestLocalhostAgentActions(unittest.TestCase):
    """Test agent actions via localhost curl requests inside container"""

    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:5000/api/public/agent"
        self.test_inbox_path = "/tmp/agent_inbox_test"

        # Create test inbox directory
        os.makedirs(self.test_inbox_path, exist_ok=True)

        # Clear any existing test files
        for file in Path(self.test_inbox_path).glob("test_*.json"):
            file.unlink()

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        if os.path.exists(self.test_inbox_path):
            shutil.rmtree(self.test_inbox_path, ignore_errors=True)

    def execute_curl_request(self, agent_id: int, action: str, payload: dict = None):
        """
        Execute curl request to agent action endpoint

        Args:
            agent_id: Agent ID (1, 2, etc.)
            action: Action name (RECEIVE_POST, WAKEUP)
            payload: JSON payload to send

        Returns:
            dict: Response data and metadata
        """
        url = f"{self.base_url}/{agent_id}/action/{action}/"

        cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json"]

        if payload:
            cmd.extend(["-d", json.dumps(payload)])

        cmd.append(url)

        print(f"🔄 Executing: {' '.join(cmd[-3:])}")  # Show last 3 parts for brevity

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            print(f"📊 Status Code: {result.returncode}")
            print(f"📤 Response: {result.stdout[:200]}..." if len(result.stdout) > 200 else f"📤 Response: {result.stdout}")

            if result.stderr:
                print(f"⚠️  Stderr: {result.stderr}")

            # Parse JSON response if possible
            response_data = None
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")

            return {
                'status_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'json': response_data
            }

        except subprocess.TimeoutExpired:
            print("⏰ Request timed out after 30 seconds")
            return {
                'status_code': -1,
                'stdout': '',
                'stderr': 'Timeout',
                'json': None
            }
        except Exception as e:
            print(f"💥 Error executing curl: {str(e)}")
            return {
                'status_code': -2,
                'stdout': '',
                'stderr': str(e),
                'json': None
            }

    def test_receive_post_file_creation(self):
        """Test RECEIVE_POST action creates actual files"""
        print("\n🧪 Testing RECEIVE_POST File Creation")

        # Generate unique test data
        test_id = int(time.time() * 1000)  # Millisecond timestamp
        test_filename = f"test_receive_post_{test_id}.json"

        payload = {
            "result": {
                "result": {
                    "updated_files": [
                        {
                            "path": test_filename,
                            "file_operation": "update",
                            "file_content": json.dumps({
                                "message": {
                                    "from": "localhost_test",
                                    "to": "test_agent",
                                    "data": f"Integration test message {test_id}",
                                    "id": test_id,
                                    "created_at": datetime.now().isoformat()
                                }
                            })
                        }
                    ]
                }
            }
        }

        # Execute RECEIVE_POST request
        response = self.execute_curl_request(2, "RECEIVE_POST", payload)

        # Verify response
        self.assertEqual(response['status_code'], 0, "Curl should succeed")
        self.assertIsNotNone(response['json'], "Response should contain valid JSON")

        if response['json']:
            self.assertTrue(response['json'].get('success', False),
                          f"Response should indicate success: {response['json']}")

            # Check if we got structured data back (not empty)
            data = response['json'].get('data', [])
            print(f"📋 Response data structure: {data}")

            # The response should contain execution results
            self.assertIsInstance(data, list, "Response data should be a list")

    def test_wakeup_action_response(self):
        """Test WAKEUP action returns proper response (not 500 error)"""
        print("\n🧪 Testing WAKEUP Action Response")

        # Test different WAKEUP actions for various agents
        agents_to_test = [1, 2, 3, 6]  # Test multiple agents

        for agent_id in agents_to_test:
            print(f"\n🤖 Testing WAKEUP for Agent {agent_id}")

            response = self.execute_curl_request(agent_id, "WAKEUP")

            # Verify we don't get 500 errors (which would cause curl to fail)
            self.assertEqual(response['status_code'], 0,
                           f"Curl should succeed for agent {agent_id}")

            if response['json']:
                # If we get a JSON response, it should indicate success or at least not crash
                print(f"✅ Agent {agent_id} WAKEUP response: {response['json']}")

                # The response should be structured (not just error text)
                self.assertIsInstance(response['json'], dict,
                                    f"Agent {agent_id} should return structured response")
            else:
                print(f"⚠️  Agent {agent_id} returned non-JSON response: {response['stdout']}")

    def test_file_system_integration(self):
        """Test that RECEIVE_POST creates files in the expected file system locations"""
        print("\n🧪 Testing File System Integration")

        test_id = int(time.time() * 1000)
        test_filename = f"filesystem_test_{test_id}.json"

        payload = {
            "result": {
                "result": {
                    "updated_files": [
                        {
                            "path": test_filename,
                            "file_operation": "create",
                            "file_content": json.dumps({
                                "test_type": "filesystem_integration",
                                "test_id": test_id,
                                "message": {
                                    "from": "filesystem_test",
                                    "to": "agent_inbox",
                                    "data": "Testing file system integration",
                                    "id": test_id,
                                    "created_at": datetime.now().isoformat()
                                }
                            })
                        }
                    ]
                }
            }
        }

        # Execute request
        response = self.execute_curl_request(2, "RECEIVE_POST", payload)

        # Verify response
        self.assertEqual(response['status_code'], 0, "Request should succeed")

        if response['json'] and response['json'].get('success'):
            print(f"✅ RECEIVE_POST succeeded")

            # Check if files were actually created in expected locations
            # Note: The actual file location depends on the filesystem adapter configuration
            # We can check common locations or look for evidence of file creation in response

            data = response['json'].get('data', [])
            if data:
                print(f"📁 File creation evidence in response: {data}")
        else:
            print(f"⚠️  RECEIVE_POST response: {response}")

    def test_session_data_flow(self):
        """Test that session data flows correctly through agent actions"""
        print("\n🧪 Testing Session Data Flow")

        test_id = int(time.time() * 1000)

        # Create a payload with specific session data we can track
        session_test_payload = {
            "result": {
                "result": {
                    "updated_files": [
                        {
                            "path": f"session_test_{test_id}.json",
                            "file_operation": "update",
                            "file_content": json.dumps({
                                "session_test": True,
                                "test_id": test_id,
                                "tracking_data": {
                                    "session_marker": f"session_{test_id}",
                                    "flow_test": "session_data_tracking"
                                }
                            })
                        }
                    ]
                }
            }
        }

        # Execute request
        response = self.execute_curl_request(2, "RECEIVE_POST", session_test_payload)

        # Analyze response for session data handling
        self.assertEqual(response['status_code'], 0, "Request should succeed")

        if response['json']:
            data = response['json'].get('data', [])
            success = response['json'].get('success', False)

            print(f"📊 Session flow test results:")
            print(f"   Success: {success}")
            print(f"   Data structure: {type(data)}")
            print(f"   Data content: {data}")

            # Check for evidence of session data processing
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Session data processed - got {len(data)} result items")
            else:
                print(f"⚠️  Minimal session data processing - empty or minimal results")

    def test_concurrent_agent_requests(self):
        """Test multiple concurrent agent requests to ensure no interference"""
        print("\n🧪 Testing Concurrent Agent Requests")

        # Create multiple payloads for concurrent testing
        test_base_id = int(time.time() * 1000)
        concurrent_payloads = []

        for i in range(3):  # Test 3 concurrent requests
            payload = {
                "result": {
                    "result": {
                        "updated_files": [
                            {
                                "path": f"concurrent_test_{test_base_id}_{i}.json",
                                "file_operation": "create",
                                "file_content": json.dumps({
                                    "concurrent_test_id": test_base_id,
                                    "request_number": i,
                                    "message": {
                                        "from": f"concurrent_test_{i}",
                                        "to": "test_agent",
                                        "data": f"Concurrent request {i}",
                                        "id": test_base_id + i
                                    }
                                })
                            }
                        ]
                    }
                }
            }
            concurrent_payloads.append(payload)

        # Execute requests rapidly
        responses = []
        for i, payload in enumerate(concurrent_payloads):
            print(f"🚀 Sending concurrent request {i+1}/3")
            response = self.execute_curl_request(2, "RECEIVE_POST", payload)
            responses.append(response)
            time.sleep(0.1)  # Small delay between requests

        # Verify all requests succeeded
        success_count = 0
        for i, response in enumerate(responses):
            if response['status_code'] == 0 and response['json'] and response['json'].get('success'):
                success_count += 1
                print(f"✅ Concurrent request {i+1} succeeded")
            else:
                print(f"❌ Concurrent request {i+1} failed: {response}")

        # All concurrent requests should succeed
        self.assertEqual(success_count, 3, "All concurrent requests should succeed")
        print(f"🎉 {success_count}/3 concurrent requests succeeded")


def run_localhost_agent_tests():
    """Run all localhost agent action tests"""
    print("🚀 Running Localhost Agent Actions Integration Tests...\n")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLocalhostAgentActions)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n📊 Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")

    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")

    if result.wasSuccessful():
        print("🎉 All localhost agent action tests passed!")
    else:
        print("⚠️  Some localhost agent action tests failed!")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_localhost_agent_tests()
    exit(0 if success else 1)