# python
import os
import io
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import json
from contextlib import contextmanager

# ensure project package imports work from tests directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the classes under test
from core.adapters.broadcast_adapter import BroadcastAdapter
from core.looper.executors.replicate_executor import ReplicateExecutor
from core.models.broadcast_data import BroadcastData

class TestBroadcastReplicate(unittest.TestCase):
    def setUp(self):
        # Prepare a temporary output directory for generated images
        self.output_dir = os.path.join('tests', '_data', 'generated', 'integration')
        os.makedirs(self.output_dir, exist_ok=True)

        # Create adapter instance
        self.adapter = BroadcastAdapter()
        self.adapter.logger = MagicMock()

        # Create a ReplicateExecutor instance (model name doesn't matter since we mock)
        self.replicate_model = "mock/model"
        self.executor = ReplicateExecutor(self.replicate_model)

    def tearDown(self):
        # Clean up generated files (if any)
        for fname in os.listdir(self.output_dir):
            try:
                os.remove(os.path.join(self.output_dir, fname))
            except Exception:
                pass

    def _make_test_image(self, size=(512, 512), color=(155, 0, 0)):
        """Create an in-memory PIL Image for testing."""
        img = Image.new("RGB", size, color=color)
        img.format = "PNG"
        return img

    @patch.object(ReplicateExecutor, "generate_image_from_replicate")
    def test_replicate_produces_image_and_broadcast_adapter_handles_payload(self, mock_generate):
        """
        Integration test:
         - mock ReplicateExecutor.generate_image_from_replicate to return a PIL Image
         - simulate storing that image to disk (as the real executor might do)
         - build a broadcast payload referencing the saved image path
         - call BroadcastAdapter.prepare_result and verify it returns expected metadata
        """

        # Arrange: mock generate_image_from_replicate to return an image
        test_img = self._make_test_image(size=(256, 256))
        mock_generate.return_value = test_img

        # Act: call the (mocked) executor to "generate" an image
        generated_image = self.executor.generate_image_from_replicate(
            model=self.replicate_model,
            user_content="test prompt",
            width=256,
            height=256
        )

        # Save the returned image to disk as the executor would do
        saved_filename = os.path.join(self.output_dir, "integration_generated.png")
        generated_image.save(saved_filename, format="PNG")
        self.assertTrue(os.path.exists(saved_filename), "Generated image file should be saved for the adapter input.")

        # Build a broadcast-like payload that the BroadcastAdapter would process.
        # Many adapters expect nested structures; use a simple example matching other tests.
        broadcast_payload = {
            "result": {
                "model_id": "mock/model",
                "step_id": "replicate_step",
                "result": {
                    # put the path or url where adapter expects image reference (adjust if your adapter expects different key)
                    "image_path": saved_filename,
                    "caption": "A mock generated image"
                }
            }
        }

        # Here we set it to read the caption we put under result/result/caption
        self.adapter.field = "result/result/caption"
        result_caption = self.adapter.prepare_result(broadcast_payload)
        self.assertEqual(result_caption, "A mock generated image")

        self.adapter.field = "result/result"
        result_dict = self.adapter.prepare_result(broadcast_payload)

        if not isinstance(result_dict, dict):

            if hasattr(result_dict, "to_dict"):
                result_dict = result_dict.to_dict()
                self.assertIsInstance(result_dict, dict)
            elif hasattr(result_dict, "to_json"):
                result_dict = json.loads(result_dict.to_json())
                self.assertIsInstance(result_dict, dict)
            elif hasattr(result_dict, "__json__"):
                result_dict = result_dict.__json__()
                self.assertIsInstance(result_dict, dict)

        self.assertIn("image_path", result_dict)
        self.assertEqual(result_dict["image_path"], saved_filename)

        mock_generate.assert_called_once()


    @patch.object(ReplicateExecutor, "generate_image_from_replicate")
    def test_replicate_run_saved_and_read_via_broadcast_adapter(self, mock_generate):
        """
        End-to-end test using the real database connection (no fake cursor).
         - mock ReplicateExecutor.generate_image_from_replicate to return a PIL Image
         - call ReplicateExecutor.run() to get an image
         - create a BroadcastData containing the image under 'result'
         - write it using BroadcastAdapter.write() (real DB)
         - read it back using BroadcastAdapter.read() and verify the image placeholder or image properties
        """

        # --- Arrange: mock image generation ---
        test_img = self._make_test_image(size=(128, 128))
        mock_generate.return_value = test_img

        # Ensure session id used for write/read is consistent
        from core.services import session as session_module
        original_get_session_id = session_module.session_manager.get_session_id
        session_module.session_manager.get_session_id = MagicMock(return_value="test-session")

        # Clean up any previous rows for this session to have a predictable state
        try:
            # delete any previous rows for 'test-session'
            self.adapter.delete_entries_by_session_id()
        except Exception:
            # best-effort cleanup, ignore errors
            pass

        try:
            # Act: call executor.run() which under the hood will call generate_image_from_replicate (mocked)
            generated = self.executor.run(self.replicate_model, {}, "test prompt", None)
            self.assertIsNotNone(generated)
            self.assertIsInstance(generated, Image.Image)

            # Prepare BroadcastData object that matches how executor results are expected to be saved.
            bd = BroadcastData({"model_id": self.replicate_model, "step_id": "replicate_step", "result": generated})

            # Write to DB via BroadcastAdapter (real DB)
            write_success = self.adapter.write("replicate_step", bd)
            self.assertTrue(write_success, "BroadcastAdapter.write should return True")

            # Now read it back using BroadcastAdapter.read() (real DB)
            self.adapter.field = "result"
            read_result = self.adapter.read(self_step_id="replicate_step", ref_step_id="replicate_step",
                                            ignore_read_status=True)

            # The adapter.prepare_result may return BroadcastData or dict — normalize
            self.assertIsNotNone(read_result, "BroadcastAdapter.read returned None, expected saved data.")

            if hasattr(read_result, "to_dict"):
                read_dict = read_result.to_dict()
            elif hasattr(read_result, "__json__"):
                read_dict = read_result.__json__()
            else:
                read_dict = dict(read_result) if isinstance(read_result, dict) else {"result": read_result}

            # Verify that stored data contains the 'result' key (either image placeholder or other representation)
            result_value = read_dict.get("result")
            if result_value == "<Image Object>" or result_value is None:
                # Accept placeholder; also verify DB actually contains JSON with model_id and result
                # Query DB directly to fetch raw stored JSON for this session/step
                from core.services.postgres_db_connect import get_db_cursor
                with get_db_cursor() as cur:
                    cur.execute(
                        "SELECT data FROM loopai_broadcast WHERE sessionid = %s AND stepid = %s ORDER BY id DESC LIMIT 1",
                        ("test-session", "replicate_step"))
                    row = cur.fetchone()
                    self.assertIsNotNone(row, "Expected a row in DB but got none")
                    raw = row.get("data") if isinstance(row, dict) else row[0]
                    stored_json = json.loads(raw)
                    self.assertIn("model_id", stored_json)
                    self.assertIn("result", stored_json)
            else:
                # If result_value is a dict or Image, verify contents or image size
                if isinstance(result_value, dict):
                    self.assertIn("model_id", result_value)
                elif isinstance(result_value, Image.Image):
                    self.assertEqual(result_value.size, (128, 128))
                else:
                    self.assertTrue(result_value)

        finally:
            # cleanup: remove entries we created and restore session manager
            try:
                self.adapter.delete_entries_by_session_id()
            except Exception:
                pass
            session_module.session_manager.get_session_id = original_get_session_id

        mock_generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()