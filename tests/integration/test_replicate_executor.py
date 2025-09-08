import base64
import os
import sys
import unittest
from io import BytesIO

from PIL import Image
import replicate
from core.services.session import session_manager

# Debugging: Print the Python path
print("Python Path (sys.path):")
for path in sys.path:
    print(path)

# Debugging: Print the current working directory
print(f"Current Working Directory: {os.getcwd()}")

# Debugging: Attempt to import the module with full path
try:
    from core.looper.executors.replicate_executor import ReplicateExecutor
    from core.models.broadcast_data import BroadcastData
    from core.services.logger_service import LoggerService
except ImportError as e:
    print(f"Import Error: {e}")
    raise

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

class TestReplicateExecutor(unittest.TestCase):
    def setUp(self):
        self.output_dir = 'tests/_data/generated/replicate'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Output Directory: {os.path.abspath(self.output_dir)}")
        self.logger = LoggerService()
        self.model = "black-forest-labs/flux-schnell"
        self.executor = ReplicateExecutor(self.model)


    def tearDown(self):
        pass


    def test_generate_image_from_replicate(self):
        # Define the test prompt
        user_content = {'loopai_project_id': 'OCVA', 'looai_project_descritption': 'Easy reading professional blog about health', 'loopai_mode': 'draw illustration for our blog', 'request': "Make a vibrant illustration for our blog based on the description in the field 'requestContent'. \n      Do not take the description literally, use allegoric or metaphoric choaice of ideas for painting the illustration. \n      But keep it nice looking. Try to be creative", 'requestContent': 'null'}

        try:
            # Generate the image
            executor_result = self.executor.run(
                model=self.model,
                system_content={"system": "You are a picure editor"},
                user_content=user_content
            )

        except Exception as e:
            self.fail(f"Image generation failed with error: {e}")

        print("Generated image var type: ", type(executor_result))

        generated_image_base64 = executor_result["image_base64"]
        generated_image_bytes = base64.b64decode(generated_image_base64)

        self.assertIsNotNone(generated_image_bytes, "Image generation failed.")

        generated_image = Image.open(BytesIO(generated_image_bytes))
        image_format = generated_image.format.lower()  # e.g., 'WEBP' -> 'webp'
        # e.g., 'WEBP' -> 'webp'
        print(f"Image format: {image_format}")

        # Save the generated image to a file with the correct extension
        output_file = os.path.join(self.output_dir, f"generated_image.{image_format}")
        print(f"Saving image to: {os.path.abspath(output_file)}")  # Debugging: Print the full path

        # Debugging: Verify the image object
        if generated_image:
            print(f"Image mode: {generated_image.mode}, size: {generated_image.size}")

        # Save the image with the correct format
        generated_image.save(output_file, format=image_format)

        # Debugging: Verify the file was saved
        if os.path.exists(output_file):
            print(f"File saved successfully: {output_file}")
        else:
            print(f"File not saved: {output_file}")

        self.assertTrue(os.path.exists(output_file), "Generated image file was not saved.")

        with Image.open(output_file) as img:
            self.assertEqual(img.size, (1024, 1024), "Generated image has incorrect dimensions.")

        self.logger.info(f"Generated image saved to: {output_file}")


if __name__ == '__main__':
    unittest.main()