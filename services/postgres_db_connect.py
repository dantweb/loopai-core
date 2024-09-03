import psycopg2
from psycopg2.extras import RealDictCursor
from config import POSTGRESQL_DB_HOST, POSTGRESQL_DB_USER, POSTGRESQL_DB_PASSWORD, POSTGRESQL_DB_NAME, \
    POSTGRESQL_DB_PORT
from core.services.logger_service import LoggerService
from contextlib import contextmanager


class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(
                host=POSTGRESQL_DB_HOST,
                user=POSTGRESQL_DB_USER,
                password=POSTGRESQL_DB_PASSWORD,
                database=POSTGRESQL_DB_NAME,
                port=POSTGRESQL_DB_PORT
            )
            yield conn
        except (Exception, psycopg2.DatabaseError) as error:
            logger_service = LoggerService()
            logger_service.error(f"Error connecting to the database: {error}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()


# Global method to get the database cursor
def get_db_cursor():
    db_conn = DatabaseConnection()
    return db_conn.get_cursor()
