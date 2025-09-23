# python
import os
import io
import unittest
import uuid
from unittest.mock import patch, MagicMock
from PIL import Image
import json
import base64
from contextlib import contextmanager

# Ensure project package imports work from tests directory
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

        # Clean up any existing DB entries for the test session
        from core.services import session_manager as session_module
        self.original_get_session_id = session_module.session_manager.get_session_id
        session_module.session_manager.get_session_id = MagicMock(return_value="test-session")
        try:
            self.adapter.delete_entries_by_session_id()
        except Exception:
            pass

    def tearDown(self):
        # Clean up generated files
        for fname in os.listdir(self.output_dir):
            try:
                os.remove(os.path.join(self.output_dir, fname))
            except Exception:
                pass

        # Clean up DB entries
        try:
            self.adapter.delete_entries_by_session_id()
        except Exception:
            pass

        # Restore session manager
        from core.services import session_manager as session_module
        session_module.session_manager.get_session_id = self.original_get_session_id

    def _make_test_image(self, size=(512, 512), color=(155, 0, 0)):
        """Create an in-memory PIL Image for testing."""
        img = Image.new("RGB", size, color=color)
        img.format = "PNG"
        return img

    def _encode_image_to_base64(self, image):
        """Convert a PIL Image to base64-encoded string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def _decode_base64_to_image(self, base64_str):
        """Decode a base64 string to a PIL Image."""
        img_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(img_data))

    def _encode_dict_to_base64(self, data):
        """Convert a dictionary to base64-encoded JSON string."""
        json_str = json.dumps(data)
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    def _decode_base64_to_dict(self, base64_str):
        """Decode a base64 string to a dictionary."""
        json_str = base64.b64decode(base64_str).decode('utf-8')
        return json.loads(json_str)

    @patch.object(ReplicateExecutor, "generate_image_from_replicate")
    async def test_replicate_produces_image_and_broadcast_adapter_handles_payload(self, mock_generate):
        """
        Integration test:
         - Mock ReplicateExecutor.generate_image_from_replicate to return a PIL Image
         - Simulate storing that image to disk
         - Build a broadcast payload with image path and base64-encoded caption
         - Call BroadcastAdapter.prepare_result and verify it handles both
        """
        # Arrange: mock generate_image_from_replicate to return an image
        test_img = self._make_test_image(size=(256, 256))
        mock_generate.return_value = test_img

        # Act: call the (mocked) executor to "generate" an image
        generated_image = await self.executor.generate_image_from_replicate(
            model=self.replicate_model,
            user_content="test prompt",
            width=256,
            height=256
        )

        # Save the returned image to disk
        saved_filename = os.path.join(self.output_dir, "integration_generated.png")
        generated_image.save(saved_filename, format="PNG")
        self.assertTrue(os.path.exists(saved_filename), "Generated image file should be saved.")

        # Build a broadcast-like payload with a base64-encoded caption
        caption_dict = {"text": "A mock generated image"}
        base64_caption = self._encode_dict_to_base64(caption_dict)
        broadcast_payload = {
            "result": {
                "model_id": "mock/model",
                "step_id": "replicate_step",
                "result": {
                    "image_path": saved_filename,
                    "caption": base64_caption
                }
            }
        }

        # Test caption decoding
        self.adapter.field = "result/result/caption"
        result_caption = self.adapter.prepare_result(broadcast_payload)
        # Explicitly decode if adapter doesn't
        if isinstance(result_caption, str):
            try:
                result_caption = self._decode_base64_to_dict(result_caption)
            except Exception as e:
                self.fail(f"Failed to decode base64 caption: {e}")
        self.assertIsInstance(result_caption, dict, "Expected decoded caption to be a dict")
        self.assertEqual(result_caption, caption_dict, "Decoded caption should match original")

        # Test accessing the entire result dict
        self.adapter.field = "result/result"
        result_dict = self.adapter.prepare_result(broadcast_payload)

        if not isinstance(result_dict, dict):
            if hasattr(result_dict, "to_dict"):
                result_dict = result_dict.to_dict()
            elif hasattr(result_dict, "to_json"):
                result_dict = json.loads(result_dict.to_json())
            elif hasattr(result_dict, "__json__"):
                result_dict = result_dict.__json__()
            else:
                self.fail("Result dict is not a dict and has no conversion method")

        self.assertIn("image_path", result_dict)
        self.assertEqual(result_dict["image_path"], saved_filename)
        self.assertIn("caption", result_dict)
        # Decode caption in result_dict if necessary
        if isinstance(result_dict["caption"], str):
            result_dict["caption"] = self._decode_base64_to_dict(result_dict["caption"])
        self.assertIsInstance(result_dict["caption"], dict)
        self.assertEqual(result_dict["caption"], caption_dict)

        mock_generate.assert_called_once()

    @patch.object(ReplicateExecutor, "generate_image_from_replicate")
    async def test_replicate_run_saved_and_read_via_broadcast_adapter_with_base64_image(self, mock_generate):
        """
        End-to-end test using the real database connection:
         - Mock ReplicateExecutor.generate_image_from_replicate to return a PIL Image
         - Create a BroadcastData with base64-encoded image and metadata
         - Write it using BroadcastAdapter.write() (real DB)
         - Read it back using BroadcastAdapter.read() and verify decoded image and metadata
        """
        # Arrange: mock image generation
        test_img = self._make_test_image(size=(128, 128))
        mock_generate.return_value = test_img

        # Encode image to base64
        base64_image = self._encode_image_to_base64(test_img)

        # Ensure session id consistency
        from core.services import session_manager as session_module
        session_module.session_manager.get_session_id = MagicMock(return_value="test-session")

        try:
            generated = await self.executor.run(self.replicate_model, {}, "test prompt")
            self.assertIsInstance(generated, BroadcastData)
            image_base64 = generated.get("image_base64")
            self.assertIsNotNone(image_base64)

            # Decode to Image and assert type
            image_bytes = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(image_bytes))
            img.load()

            self.assertIsInstance(img, Image.Image)
            step_id = uuid.uuid4().hex
            # Prepare BroadcastData with base64-encoded image and metadata
            result_data = {
                "model_id": self.replicate_model,
                "step_id": step_id,
                "result": {
                    "image_base64": base64_image,
                    "metadata": self._encode_dict_to_base64({"caption": "Base64 test image"})
                }
            }
            bd = BroadcastData(result_data)

            # Write to DB
            write_success = await self.adapter.write(step_id, bd)
            self.assertTrue(write_success, "BroadcastAdapter.write should return True")

            # Read it back
            self.adapter.field = "result"

            read_result = await self.adapter.read(self_step_id=step_id, ref_step_id=step_id,
                                           ignore_read_status=True)

            self.assertIsNotNone(read_result, "BroadcastAdapter.read returned None, expected saved data.")

            print(f"\n\n\n ATTANCIONE \n\n\n")

            if isinstance(read_result, list):
                print("it is a list\n")
                for item in read_result:
                    bc = BroadcastData(item)
                    image = bc.find_value_recursive_by_key("image_base64")

            if isinstance(read_result, BroadcastData):
                print("it is a BC\n")

                image = read_result.find_value_recursive_by_key("image_base64")

            if isinstance(read_result, dict):
                print("it is a dict\n")

                bc = BroadcastData(read_result)
                image = bc.find_value_recursive_by_key("image_base64")

            if image is None:
                print("it is a none, then we convert to BC first and get image\n")

                bc = BroadcastData(read_result)
                image = bc.find_value_recursive_by_key("image_base64")

            print("\n\n READ RESULT \n\n")
            print(read_result)
            print("\n\n IMAGE \n\n")
            print(image)


            self.assertIsNotNone(image)


            # Decode and verify the image
            decoded_image = self._decode_base64_to_image(image[0])

            self.assertIsInstance(decoded_image, Image.Image)
            self.assertEqual(decoded_image.size, (128, 128))


            bc = BroadcastData(read_result)
            metadata = bc.find_value_recursive_by_key("metadata")
            print("\n\n METADATA \n\n")
            print(metadata)
            decoded_metadata = self._decode_base64_to_dict(metadata[0])

            print(type(decoded_metadata))
            print(str(decoded_metadata))
            self.assertIsInstance(decoded_metadata, dict)
            self.assertEqual(decoded_metadata["caption"], "Base64 test image")

        finally:
            # Cleanup handled in tearDown
            pass

        mock_generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()