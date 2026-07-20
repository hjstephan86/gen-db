import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from .config import get_config

logger = logging.getLogger(__name__)


def get_database_config():
    """
    Holt Datenbank-Konfiguration aus der Pydantic Config
    
    Returns:
        Dictionary mit Datenbankverbindungsparametern
    """
    config = get_config()
    return {
        'dbname': config.database_name,
        'user': config.database_user,
        'password': config.database_password,
        'host': config.database_host,
        'port': config.database_port,
    }


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    database_config = get_database_config()
    logger.debug(f"Connecting to {database_config['host']}:{database_config['port']}/{database_config['dbname']}")
    
    conn = psycopg2.connect(**database_config)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise e
    finally:
        conn.close()


def get_db_cursor(conn):
    """Get a cursor with RealDictCursor for dict-like results"""
    return conn.cursor(cursor_factory=RealDictCursor)
