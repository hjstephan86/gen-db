import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_CONFIG = {
    'dbname': 'gen',
    'user': 'dbuser',
    'password': 'dbpassword',
    'host': 'localhost',
    'port': 5432
}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(**DATABASE_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_db_cursor(conn):
    """Get a cursor with RealDictCursor for dict-like results"""
    return conn.cursor(cursor_factory=RealDictCursor)