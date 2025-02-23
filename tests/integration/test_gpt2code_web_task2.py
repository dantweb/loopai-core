# tests/integration/test_broadcast_adapter.py
import os
import unittest
import app_global_config as config
from app.core.controllers.loop_controller import LoopController
from app.core.services.postgres_db_connect import get_db_connection, DatabaseConnection



class TestBroadcastAdapter(unittest.TestCase):
    def setUp(self):
        # Ensure the output directory exists
        os.makedirs('../_data/generated', exist_ok=True)

        config.GLOBAL_USER_ID = 3
        config.GLOBAL_LOOP_ID = 35
        config.WEB_OR_CLI = 'cli'

        # Ensure no leftover files from previous tests
        self.output_file = '../_data/generated/gpt2code/test.txt'
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        # Get the database connection
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        # Release the database connection
        self.cursor.close()
        DatabaseConnection().release_connection(self.conn)

    def test_broadcast_output(self):
        # Path to the loop file
        # loop_file = '../_data/loops/loop_with_foreach.yaml'
        loop_file = '/home/dtkachev/PycharmProjects/loopAI/tests/loops/loop_gpt2code_web_task2.yaml'

        # Run the LoopController with the test loop
        controller = LoopController(loop_file)
        controller.run()

        # Check if the broadcast output is correctly stored in the database
        self.cursor.execute(
            "SELECT * FROM loopai_broadcast WHERE sessionid = %s AND stepid = %s",
            ("test_broadcast_session", "step1")
        )
        # row = self.cursor.fetchone()
        # self.assertIsNotNone(row, "Broadcast output was not stored in the database.")
        # self.assertIn("expected_content", row[1], "Broadcast output does not contain the expected content.")

if __name__ == '__main__':
    unittest.main()
