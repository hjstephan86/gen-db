"""
Tests for database.py module
"""
import pytest
import psycopg2
from backend.database import get_db_connection, get_db_cursor

@pytest.mark.db
class TestDatabaseConnection:

    def test_get_db_connection_success(self, test_db_config, monkeypatch):
        monkeypatch.setattr('backend.database.DATABASE_CONFIG', test_db_config)

        with get_db_connection() as conn:
            assert conn is not None
            assert not conn.closed

    def test_get_db_connection_commit(self, clean_database):
        cursor = clean_database.cursor()
        cursor.execute('''
            INSERT INTO biological_networks
            (name, network_type, organism, description, node_count, edge_count)
            VALUES ('Test', 'metabolic', 'Test', 'Test', 3, 2)
        ''')
        clean_database.commit()

        cursor.execute("SELECT COUNT(*) FROM biological_networks")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_get_db_connection_rollback_on_error(self, test_db_config, monkeypatch):
        monkeypatch.setattr('backend.database.DATABASE_CONFIG', test_db_config)

        with pytest.raises(psycopg2.Error):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO biological_networks (invalid_column) VALUES ('test')")

    def test_get_db_connection_closes_after_context(self, test_db_config, monkeypatch):
        monkeypatch.setattr('backend.database.DATABASE_CONFIG', test_db_config)

        with get_db_connection() as conn:
            pass

        assert conn.closed

    def test_get_db_cursor_returns_dict_cursor(self, db_connection):
        cursor = get_db_cursor(db_connection)
        assert cursor is not None
        assert cursor.connection == db_connection