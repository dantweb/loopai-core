import os
import sys
import unittest
from PIL import Image
import replicate

# Debugging: Print the Python path
print("Python Path (sys.path):")
for path in sys.path:
    print(path)

# Debugging: Print the current working directory
print(f"Current Working Directory: {os.getcwd()}")

# Debugging: Attempt to import the module with full path
try:
    from loopai_src.core.looper.executors.replicate_executor import ReplicateExecutor
    from loopai_src.core.models.broadcast_data import BroadcastData
    from loopai_src.core.services.logger_service import LoggerService
    print("Imports successful!")
except ImportError as e:
    print(f"Import Error: {e}")
    raise

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


class TestReplicateExecutor(unittest.TestCase):
    def setUp(self):
        # Ensure the output directory exists
        self.output_dir = '../_data/generated/replicate'
        os.makedirs(self.output_dir, exist_ok=True)

        # Debugging: Print the output directory path
        print(f"Output Directory: {os.path.abspath(self.output_dir)}")

        # Initialize the logger
        self.logger = LoggerService()

        # Initialize the ReplicateExecutor with a model
        self.model = "black-forest-labs/flux-schnell"  # Example model, replace with your desired model
        self.executor = ReplicateExecutor(self.model)

    def tearDown(self):
        pass
        # for file in os.listdir(self.output_dir):
        #     file_path = os.path.join(self.output_dir, file)
        #     if os.path.isfile(file_path):
        #         print(f"Removing file: {file_path}")  # Debugging
        #         os.remove(file_path)

    def test_generate_image_from_replicate(self):
        # Define the test prompt
        user_content = "a futuristic cityscape at night"

        # Generate the image
        generated_image = self.executor.generate_image_from_replicate(
            model=self.model,
            user_content=user_content,
            width=1024,
            height=1024
        )

        print("Generated image: ", generated_image)

        # Verify that the image was generated
        self.assertIsNotNone(generated_image, "Image generation failed.")

        # Get the image format from the response (e.g., 'webp')
        image_format = generated_image.format.lower()  # e.g., 'WEBP' -> 'webp'
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

        # Verify that the file was saved
        self.assertTrue(os.path.exists(output_file), "Generated image file was not saved.")

        # Verify that the saved file is a valid image
        with Image.open(output_file) as img:
            self.assertEqual(img.size, (1024, 1024), "Generated image has incorrect dimensions.")

        self.logger.info(f"Generated image saved to: {output_file}")


if __name__ == '__main__':
    unittest.main()