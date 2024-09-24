# tests/integration/test_broadcast_adapter.py
import os
import unittest
from app.core.controllers.loop_controller import LoopController
from app.core.services.postgres_db_connect import get_db_connection, DatabaseConnection


class TestBroadcastAdapter(unittest.TestCase):
    def setUp(self):
        # Ensure the output directory exists
        os.makedirs('../_data/generated.old.but.gold', exist_ok=True)

        # Ensure no leftover files from previous tests
        self.output_file = '../_data/generated.old.but.gold/gpt2code/test.txt'
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
        loop_file = '/../loops/loop_g2c_wp_loopai_cons.yaml'

        # Run the LoopController with the test loop
        controller = LoopController(loop_file)
        controller.run()


if __name__ == '__main__':
    unittest.main()
