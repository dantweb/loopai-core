import base64
import io
import unittest
import os
from dotenv import load_dotenv
from PIL import Image
from core.models.broadcast_data import BroadcastData
from core.services.session import session_manager

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), "test_executor_compatibility.env")
load_dotenv(env_path)

class TestExecutorCompatibility(unittest.TestCase):
    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)


    def setUp(self):
        # Example model identifiers
        self.dalle_model = "dall-e-3"  # DALL-E 3 model
        self.replicate_model = "black-forest-labs/flux-schnell"
        self.output_dir_dalle = 'tests/_data/generated/dalle'
        os.makedirs(self.output_dir_dalle, exist_ok=True)
        # Initialize mock user content as a BroadcastData instance
        self.user_content = BroadcastData(
            {"content": "A futuristic cityscape at night", "metadata": {"example_key": "example_value"}}
        )
        self.width = 1024
        self.height = 1024


    def test_executor_output_compatibility(self):
        # Generate images using both executors
        from core.looper.executors.dalle2_executor import Dalle2Executor
        from core.looper.executors.replicate_executor import ReplicateExecutor

        session_manager.set_environment({"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")})

        # Initialize executors
        dalle_executor = Dalle2Executor(self.dalle_model)
        replicate_executor = ReplicateExecutor(self.replicate_model)

        # Call the real Dalle2Executor
        try:
            executor_result = dalle_executor.run(
                model=self.dalle_model,
                system_content={"system": "You are a pciture editor"},
                user_content=self.user_content,
            )
            output_file = os.path.join(self.output_dir_dalle, f"generated_image_dalle.png")

            dalle_image_base64 = executor_result["image_base64"]

            image_bytes = base64.b64decode(dalle_image_base64)
            dalle_image = Image.open(io.BytesIO(image_bytes))
            dalle_image.load()
            dalle_image.save(output_file, format="png")

        except Exception as e:
            self.fail(f"Dalle2Executor failed with error: {e}")

        # Call the real ReplicateExecutor
        try:
            executor_result = replicate_executor.run(
                model=self.replicate_model,
                system_content={"system": "You are a pciture editor"},
                user_content=self.user_content,
            )
        except Exception as e:
            self.fail(f"ReplicateExecutor failed with error: {e}")

        image_base64 = executor_result["image_base64"]
        image_bytes = base64.b64decode(image_base64)
        replicate_image = Image.open(io.BytesIO(image_bytes))
        replicate_image.load()

        print(f"DALL-E Image Type: {type(dalle_image)}")
        print(f"Replicate Image Type: {type(replicate_image)}")

        # Assert that both images are of the same type and dimensions
        self.assertIsInstance(dalle_image, Image.Image, "DalleExecutor did not return a PIL.Image")
        self.assertIsInstance(replicate_image, Image.Image, "ReplicateExecutor did not return a PIL.Image")
        self.assertEqual(dalle_image.size, replicate_image.size, "Image sizes do not match")
        self.assertEqual(dalle_image.mode, replicate_image.mode, "Image modes do not match")


if __name__ == "__main__":
    unittest.main()