import json
import os
import tempfile
import unittest
from core.adapters.filesystem_adapter import FilesystemAdapter
from core.models.broadcast_data import BroadcastData
from unittest.mock import patch


class TestFilesystemAdapterWithBroadcast(unittest.TestCase):
    def setUp(self):
        self.source = "/test_source"
        self.global_user_id = "test_user"
        self.global_loop_id = "test_loop"

        # Mock the config and utility functions
        with patch("core.adapters.filesystem_adapter.config") as mock_config, \
                patch("core.adapters.filesystem_adapter.loop_path_resolver.get_file_system_by_user_and_loop") as mock_get_user_loop:
            mock_config.LOOPAI_SINGLE_FILESYSTEM_PATH = "/mock/base_path"
            mock_config.WEB_OR_CLI = "cli"
            mock_config.LOOPAI_ROOT = "/mock/root"
            mock_get_user_loop.return_value = "/mock/user_loop_path"

            self.adapter = FilesystemAdapter(
                source=self.source
            )

    def write_and_collect(self, broadcast_data):
        """Run write() into a temp dir; return {relative_path: decoded content} of the files written."""
        with tempfile.TemporaryDirectory() as tmp, \
                patch("core.adapters.filesystem_adapter.write_to_fs_log"):
            self.adapter.absolute_path = tmp
            self.adapter.write('step1', broadcast_data)
            written = {}
            for root, _, names in os.walk(tmp):
                for name in names:
                    full_path = os.path.join(root, name)
                    with open(full_path) as f:
                        written[os.path.relpath(full_path, tmp)] = json.loads(f.read())
            return written

    def test_extract_files_from_nested_broadcast(self):
        data = {
            "result": {
                "result": {
                    "result": {
                        "updated_files": [
                            {
                                "path": "post/inbox/new/message1756287702.json",
                                "file_operation": "update",
                                "file_content": "{\"message\": {\"from\": \"FRBG/cityhall\", \"to\": \"FRBG/Agent_hwp2bg\", \"data\": \"Test message eb3b740d sent at 2025-08-27T09:41:42.822348\", \"id\": 1756287702, \"created_at\": \"2025-08-27T09:41:42.822348\"}}"
                            }
                        ]
                    }
                }
            }
        }
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        # file_content arrives as a JSON string; BroadcastData decodes it to the message dict
        expected_message = {
            "message": {
                "from": "FRBG/cityhall",
                "to": "FRBG/Agent_hwp2bg",
                "data": "Test message eb3b740d sent at 2025-08-27T09:41:42.822348",
                "id": 1756287702,
                "created_at": "2025-08-27T09:41:42.822348"
            }
        }
        self.assertEqual(files, {"post/inbox/new/message1756287702.json": expected_message})

    def test_extract_files_from_valid_broadcast(self):
        data = {
            "result": {
                "updated_files": [
                    {"path": "file1.txt", "file_content": "content1"},
                    {"path": "file2.doc", "file_content": "content2"},
                    {"path": "file3.png", "file_content": "content3"}
                ]
            }
        }
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        self.assertEqual(files, {
            "file1.txt": "content1",
            "file2.doc": "content2",
            "file3.png": "content3",
        })

    def test_extract_files_with_irregular_broadcast(self):
        data = {
            "result": {
                "updated_files": [
                    {"path": "valid_file.txt", "extra_field": "ignore_me"},
                    {"no_path": "missing_path"},
                    {"path": "another_valid_file.doc"}
                ]
            }
        }
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        # entries without file_content abort the write: nothing is written
        self.assertEqual(files, {})

    def test_extract_files_with_empty_broadcast(self):
        data = {"result": {}}
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)
        self.assertEqual(files, {})

    def test_extract_files_with_suspicious_paths(self):
        data = {
            "result": {
                "updated_files": [
                    {"path": "/absolute_file.txt"},
                    {"path": "../relative_traversal.txt"},
                    {"path": "safe_path/valid_file.txt"}
                ]
            }
        }
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        self.assertEqual(files, {})
        self.assertFalse(os.path.exists("/absolute_file.txt"))

    def test_extract_files_no_filtering(self):
        data = {
            "result": {
                "updated_files": [
                    {"path": "file1.txt", "file_content":"file content1"},
                    {"path": "file2.jpg", "file_content":"file content2"},
                    {"path": "file3.doc", "file_content":"file content3"}
                ]
            }
        }
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        self.assertEqual(files, {
            "file1.txt": "file content1",
            "file2.jpg": "file content2",
            "file3.doc": "file content3",
        })

    def test_extract_files_life_example(self):
        data = {
            "step_id": "create_tasks",
            "result": [
                {
                    "method": "POST",
                    "path": "/api/public/agent/3/action/RECEIVE_POST/",
                    "url": "http://loopai_web:5000/api/public/agent/3/action/RECEIVE_POST/",
                    "args": {},
                    "remote_addr": "172.22.0.5",
                    "body": {
                        "result": {"response": {
                            "updated_files": [
                                {
                                    "path": "post/inbox/new/message1756287548.json",
                                    "file_content": "{\"message\": {\"from\": \"FRBG/cityhall\", \"to\": \"FRBG/Agent_hwp2bg\", \"data\": \"Test message 3f0e89cb sent at 2025-08-27T09:39:08.442998\", \"id\": 1756287548, \"created_at\": \"2025-08-27T09:39:08.442998\"}}"
                                }
                            ]
                        }}}
                }
            ],
            "session_id": "c78d3c7a-81df-4355-a63a-5bddc81e6039"
        }
        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        # file_content arrives as a JSON string; BroadcastData decodes it to the message dict
        expected_message = {
            "message": {
                "from": "FRBG/cityhall",
                "to": "FRBG/Agent_hwp2bg",
                "data": "Test message 3f0e89cb sent at 2025-08-27T09:39:08.442998",
                "id": 1756287548,
                "created_at": "2025-08-27T09:39:08.442998"
            }
        }
        self.assertEqual(files, {"post/inbox/new/message1756287548.json": expected_message})

    def test_extract_files_life_example2(self):
        data = {
            "data": {
                "result": {
                    "data": [
                        {
                            "data": {
                                "args": {},
                                "body": {
                                    "model_id": False,
                                    "result": {
                                        "response": {
                                            "updated_files": [
                                                {
                                                    "file_content":
                                                        {"message":
                                                             {
                                                                 "from": "FRBG/cityhall",
                                                                 "to": "FRBG/Agent_hwp2bg",
                                                                 "data": "Test message 3f0e89cb sent at 2025-08-27T09:39:08.442998",
                                                                 "id": 1756287548,
                                                                 "created_at": "2025-08-27T09:39:08.442998"
                                                             }
                                                         },
                                                    "path": "post/inbox/new/message1756287548.json"
                                                }
                                            ]
                                        }
                                    }
                                },
                                "method": "POST",
                                "path": "/api/public/agent/2/action/RECEIVE_POST/",
                                "remote_addr": "172.22.0.5",
                                "url": "http://loopai_web:5000/api/public/agent/2/action/RECEIVE_POST/"
                            },
                            "image": "",
                            "properties": [
                                "str",
                                "str",
                                "str",
                                "dict",
                                "str",
                                "dict"
                            ]
                        }
                    ],
                    "properties": [
                        "BroadcastData"
                    ]
                },
                "step_id": "create_tasks"
            }
        }

        broadcast_data = BroadcastData(data)
        files = self.write_and_collect(broadcast_data)

        expected_message = {
            "message": {
                "from": "FRBG/cityhall",
                "to": "FRBG/Agent_hwp2bg",
                "data": "Test message 3f0e89cb sent at 2025-08-27T09:39:08.442998",
                "id": 1756287548,
                "created_at": "2025-08-27T09:39:08.442998"
            }
        }
        self.assertEqual(files, {"post/inbox/new/message1756287548.json": expected_message})

    def test_write_files_to_desired_location_with_broadcast_data(self):
        # Mocked BroadcastData object containing file data
        data = {
            "result": {
                "updated_files": [
                    {"path": "test_folder/test_file1.txt", "file_content": "This is a test file."},
                    {"path": "test_folder/test_file2.json", "file_content": {"key": "value"}}
                ]
            }
        }
        broadcast_data = BroadcastData(data)

        expected_full_dir_path = '/mock/base_path/test_source/test_folder'

        # Mock filesystem operations
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
                patch("os.makedirs") as mock_makedirs:
            # Call the write method on the adapter
            self.adapter.write('step1', broadcast_data)

            mock_makedirs.assert_any_call(expected_full_dir_path, exist_ok=True)

            # file contents are stored JSON-encoded
            mock_file().write.assert_any_call(json.dumps("This is a test file."))


if __name__ == "__main__":
    unittest.main()
