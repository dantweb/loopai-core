# tests/integration/test_integration.py
import os
import subprocess
import unittest

from core.controllers.loop_controller import LoopController


class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Ensure the output directory exists
        os.makedirs('_data/output', exist_ok=True)

        # Ensure no leftover files from previous tests
        self.output_file = '_data/output/test-output.csv'
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_integration(self):
        self.skipTest("")
        # Path to the loop file
        loop_file = '_data/loops/test-loop.yaml'

        # Run the LoopController with the test loop
        controller = LoopController(loop_file, '1', '1', '1')
        controller.run()

        # Check if the output file exists
        self.assertTrue(
            os.path.exists(self.output_file),
            "Output file was not created."
        )

        # Verify the contents of the output file
        with open(self.output_file, 'r', encoding='utf-8') as file:
            content = file.read()
            self.assertIn(
                'test run got correct result',
                content,
                "Output file does not contain the expected result."
            )


if __name__ == '__main__':
    unittest.main()
