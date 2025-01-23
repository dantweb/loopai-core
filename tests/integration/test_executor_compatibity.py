import unittest
import os
from dotenv import load_dotenv
from PIL import Image
from core.models.broadcast_data import BroadcastData

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), "test_executor_compatibility.env")
load_dotenv(env_path)

class TestExecutorCompatibility(unittest.TestCase):
    def setUp(self):
        # Example model identifiers
        self.dalle_model = "dall-e-3"  # DALL-E 3 model
        self.replicate_model = "black-forest-labs/flux-schnell"  # Replicate model

        # Initialize mock user content as a BroadcastData instance
        self.user_content = BroadcastData(
            {"content": "A futuristic cityscape at night", "metadata": {"example_key": "example_value"}}
        )
        self.width = 1024
        self.height = 1024

    def test_executor_output_compatibility(self):
        # Generate images using both executors
        from loopai_src.core.looper.executors.dalle2_executor import Dalle2Executor
        from loopai_src.core.looper.executors.replicate_executor import ReplicateExecutor

        # Initialize executors
        dalle_executor = Dalle2Executor(self.dalle_model)
        replicate_executor = ReplicateExecutor(self.replicate_model)

        # Call the real Dalle2Executor
        try:
            dalle_image = dalle_executor.generate_image_from_dalle(
                model=self.dalle_model,
                user_content=self.user_content,
                width=self.width,
                height=self.height,
            )
        except Exception as e:
            self.fail(f"Dalle2Executor failed with error: {e}")

        # Call the real ReplicateExecutor
        try:
            replicate_image = replicate_executor.generate_image_from_replicate(
                model=self.replicate_model,
                user_content=self.user_content,  # Only send string content
                width=self.width,
                height=self.height,
            )
        except Exception as e:
            self.fail(f"ReplicateExecutor failed with error: {e}")

        # Print image types for debugging
        print(f"DALL-E Image Type: {type(dalle_image)}")
        print(f"Replicate Image Type: {type(replicate_image)}")

        # Assert that both images are of the same type and dimensions
        self.assertIsInstance(dalle_image, Image.Image, "DalleExecutor did not return a PIL.Image")
        self.assertIsInstance(replicate_image, Image.Image, "ReplicateExecutor did not return a PIL.Image")
        self.assertEqual(dalle_image.size, replicate_image.size, "Image sizes do not match")
        self.assertEqual(dalle_image.mode, replicate_image.mode, "Image modes do not match")


if __name__ == "__main__":
    unittest.main()