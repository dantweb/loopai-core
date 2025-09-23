import unittest
import threading
import time
from unittest.mock import patch, MagicMock
from web.services.async_loop_manager import AsyncLoopManager, ExecutionStatus, ExecutionInfo
import uuid

# Mock the socket to prevent NoneType errors
socket_mock = MagicMock()

class TestAsyncLoopManager(unittest.TestCase):
    def setUp(self):
        self.manager = AsyncLoopManager(max_workers=20)  # Increased to handle 10 simultaneous loops
        self.app = MagicMock()
        self.app.app_context = MagicMock()
        self.user_id = 1
        self.loop_id = 1
        self.agent_id = 1
        self.action_name = "test_action"
        self.request_data = {"key": "value"}

    def tearDown(self):
        self.manager.shutdown(wait=True)

    @patch('web.services.async_loop_manager.socket', socket_mock)
    def test_concurrent_executions(self):
        """Test multiple concurrent executions run in separate threads"""
        execution_ids = []
        thread_ids = set()

        def mock_run_loop(execution_id, app, user_id, loop_id, agent_id, action_name, request_data):
            thread_ids.add(threading.get_ident())
            time.sleep(0.1)  # Simulate some work
            self.manager._update_status(execution_id, ExecutionStatus.COMPLETED)

        with patch.object(self.manager, '_run_loop', side_effect=mock_run_loop):
            for _ in range(3):
                exec_id = self.manager.start_execution(
                    self.app, self.user_id, self.loop_id, self.agent_id, self.action_name, self.request_data
                )
                execution_ids.append(exec_id)

            timeout = time.time() + 2
            while any(self.manager.get_execution_status(eid)["status"] != "completed" for eid in execution_ids):
                if time.time() > timeout:
                    self.fail("Timeout waiting for executions to complete")
                time.sleep(0.01)

            self.assertGreater(len(thread_ids), 1, "Multiple threads should have been used")
            for exec_id in execution_ids:
                status = self.manager.get_execution_status(exec_id)
                self.assertEqual(status["status"], "completed")

    @patch('web.services.async_loop_manager.socket', socket_mock)
    def test_thread_safety_status_updates(self):
        """Test thread-safe status updates"""
        execution_id = str(uuid.uuid4())
        self.manager.executions[execution_id] = ExecutionInfo(
            execution_id=execution_id,
            user_id=self.user_id,
            loop_id=self.loop_id,
            agent_id=self.agent_id,
            action_name=self.action_name,
            status=ExecutionStatus.QUEUED,
            created_at=time.time(),
            progress_updates=[]
        )

        def update_status():
            for _ in range(100):
                self.manager._update_status(execution_id, ExecutionStatus.RUNNING)
                time.sleep(0.001)

        threads = [threading.Thread(target=update_status) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        status = self.manager.get_execution_status(execution_id)
        self.assertEqual(status["status"], "running")

    @patch('web.services.async_loop_manager.socket', socket_mock)
    def test_thread_safety_progress_updates(self):
        """Test thread-safe progress updates"""
        execution_id = str(uuid.uuid4())
        self.manager.executions[execution_id] = ExecutionInfo(
            execution_id=execution_id,
            user_id=self.user_id,
            loop_id=self.loop_id,
            agent_id=self.agent_id,
            action_name=self.action_name,
            status=ExecutionStatus.QUEUED,
            created_at=time.time(),
            progress_updates=[]
        )

        def add_progress_update():
            for i in range(100):
                self.manager._add_progress_update(execution_id, {
                    "timestamp": time.time(),
                    "message": f"Update {i}",
                    "type": "test"
                })
                time.sleep(0.001)

        threads = [threading.Thread(target=add_progress_update) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        updates = self.manager.get_progress_updates(execution_id)
        self.assertEqual(len(updates), 300)  # 3 threads * 100 updates each

    @patch('web.services.async_loop_manager.socket', socket_mock)
    @patch('core.services.session_manager.session_manager', MagicMock())
    def test_execution_isolation_ten_loops(self):
        """Test that 10 simultaneous loops run in isolated threads with distinct content"""
        execution_ids = []
        thread_ids = set()
        execution_data = {}  # Store expected data for each execution

        def mock_run_loop(execution_id, app, user_id, loop_id, agent_id, action_name, request_data):
            thread_ids.add(threading.get_ident())
            # Simulate unique progress updates and result for each execution
            self.manager._add_progress_update(execution_id, {
                "timestamp": time.time(),
                "message": f"Progress for user {user_id}, loop {loop_id}",
                "type": "progress",
                "user_id": user_id,
                "loop_id": loop_id
            })
            time.sleep(0.1)  # Simulate work
            self.manager._update_status(execution_id, ExecutionStatus.COMPLETED)
            self.manager.executions[execution_id].result = {
                "user_id": user_id,
                "loop_id": loop_id,
                "unique_data": f"Result_{user_id}_{loop_id}"
            }

        with patch.object(self.manager, '_run_loop', side_effect=mock_run_loop):
            # Start 10 executions with unique user IDs and loop IDs
            for i in range(10):
                user_id = i + 1
                loop_id = i + 100
                request_data = {"key": f"value_{i}"}
                exec_id = self.manager.start_execution(
                    self.app, user_id=user_id, loop_id=loop_id, agent_id=self.agent_id,
                    action_name=self.action_name, request_data=request_data
                )
                execution_ids.append(exec_id)
                execution_data[exec_id] = {
                    "user_id": user_id,
                    "loop_id": loop_id,
                    "request_data": request_data
                }

            # Wait for all executions to complete
            timeout = time.time() + 5
            while any(self.manager.get_execution_status(eid)["status"] != "completed" for eid in execution_ids):
                if time.time() > timeout:
                    self.fail("Timeout waiting for 10 executions to complete")
                time.sleep(0.01)

            # Verify thread isolation
            self.assertGreaterEqual(len(thread_ids), 2, "Multiple threads should be used for 10 executions")
            self.assertLessEqual(len(thread_ids), 10, "Should not exceed max_workers")

            # Verify content isolation
            for exec_id in execution_ids:
                status = self.manager.get_execution_status(exec_id)
                expected_data = execution_data[exec_id]

                # Check execution details
                self.assertEqual(status["user_id"], expected_data["user_id"], f"User ID mismatch for {exec_id}")
                self.assertEqual(status["loop_id"], expected_data["loop_id"], f"Loop ID mismatch for {exec_id}")
                self.assertEqual(status["status"], "completed", f"Execution {exec_id} should be completed")

                # Check progress updates
                updates = self.manager.get_progress_updates(exec_id)
                self.assertEqual(len(updates), 1, f"Expected one progress update for {exec_id}")
                self.assertEqual(updates[0]["user_id"], expected_data["user_id"], f"Progress user ID mismatch for {exec_id}")
                self.assertEqual(updates[0]["loop_id"], expected_data["loop_id"], f"Progress loop ID mismatch for {exec_id}")

                # Check result isolation
                result = status["result"]
                self.assertIsNotNone(result, f"Result missing for {exec_id}")
                self.assertEqual(result["user_id"], expected_data["user_id"], f"Result user ID mismatch for {exec_id}")
                self.assertEqual(result["loop_id"], expected_data["loop_id"], f"Result loop ID mismatch for {exec_id}")
                self.assertEqual(result["unique_data"], f"Result_{expected_data['user_id']}_{expected_data['loop_id']}",
                               f"Result unique data mismatch for {exec_id}")

            # Verify user executions are tracked separately
            for i in range(10):
                user_id = i + 1
                user_execs = self.manager.get_user_executions(user_id=user_id)
                self.assertEqual(len(user_execs), 1, f"Expected one execution for user {user_id}")
                self.assertEqual(user_execs[0]["execution_id"], execution_ids[i], f"Execution ID mismatch for user {user_id}")

if __name__ == '__main__':
    unittest.main()