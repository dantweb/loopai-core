import sys
import os
from core.services.postgres_db_connect import get_db_cursor

# Add the project base directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_table():
    # Use the context manager provided by get_db_cursor()
    try:
        with get_db_cursor() as cursor:
            create_table_query = """
            CREATE TABLE loopai_broadcast (
                id SERIAL PRIMARY KEY,
                sessionid TEXT NOT NULL,
                stepid TEXT NOT NULL,
                data TEXT NOT NULL,
                readby TEXT default '',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            print("Table created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")


if __name__ == "__main__":
    create_table()
