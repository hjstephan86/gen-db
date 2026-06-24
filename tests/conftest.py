"""
Pytest configuration and shared fixtures
Provides database setup, teardown, and test data
"""
import pytest
import psycopg2
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend import database

TEST_DB_CONFIG = {
    'dbname': 'gen_test',
    'user': 'dbuser',
    'password': 'dbpassword',
    'host': 'localhost',
    'port': 5432
}

@pytest.fixture(scope='session')
def test_db_config():
    return TEST_DB_CONFIG.copy()

@pytest.fixture(scope='session', autouse=True)
def setup_test_database(test_db_config):
    conn = psycopg2.connect(
        dbname='postgres',
        user=test_db_config['user'],
        password=test_db_config['password'],
        host=test_db_config['host'],
        port=test_db_config['port']
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("DROP DATABASE IF EXISTS " + test_db_config['dbname'])
    cursor.execute("CREATE DATABASE " + test_db_config['dbname'])
    cursor.close()
    conn.close()

    conn = psycopg2.connect(**test_db_config)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biological_networks (
            network_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            network_type VARCHAR(50),
            organism VARCHAR(100),
            description TEXT,
            node_count INTEGER NOT NULL,
            edge_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS network_matrices (
            network_id INTEGER PRIMARY KEY REFERENCES biological_networks(network_id) ON DELETE CASCADE,
            node_labels TEXT[] NOT NULL,
            adjacency_matrix INTEGER[][] NOT NULL,
            signature_array BIGINT[] NOT NULL,
            signature_hash VARCHAR(64)
        );

        CREATE INDEX IF NOT EXISTS idx_networks_type ON biological_networks(network_type);
        CREATE INDEX IF NOT EXISTS idx_networks_node_count ON biological_networks(node_count);
        CREATE INDEX IF NOT EXISTS idx_matrices_hash ON network_matrices(signature_hash);
    ''')

    conn.commit()
    cursor.close()
    conn.close()

    yield

    conn = psycopg2.connect(
        dbname='postgres',
        user=test_db_config['user'],
        password=test_db_config['password'],
        host=test_db_config['host'],
        port=test_db_config['port']
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("DROP DATABASE IF EXISTS " + test_db_config['dbname'])
    cursor.close()
    conn.close()

@pytest.fixture
def db_connection(test_db_config, monkeypatch):
    monkeypatch.setattr(database, 'DATABASE_CONFIG', test_db_config)

    with database.get_db_connection() as conn:
        yield conn
        conn.rollback()

@pytest.fixture
def clean_database(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("TRUNCATE biological_networks CASCADE")
    db_connection.commit()
    yield db_connection

@pytest.fixture
def sample_network_data():
    return {
        'name': 'Test_Network',
        'network_type': 'metabolic',
        'organism': 'Test organism',
        'description': 'Test description',
        'node_labels': ['A', 'B', 'C'],
        'adjacency_matrix': [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    }

@pytest.fixture
def sample_glycolysis():
    return {
        'name': 'Glycolysis',
        'network_type': 'metabolic',
        'organism': 'Homo sapiens',
        'description': 'Glucose breakdown pathway',
        'node_labels': ['Glucose', 'G6P', 'F6P', 'FBP', 'DHAP', 'G3P', 'Pyruvate'],
        'adjacency_matrix': [
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0]
        ]
    }

@pytest.fixture
def sample_partial_glycolysis():
    return {
        'name': 'Partial_Glycolysis',
        'network_type': 'metabolic',
        'organism': 'Homo sapiens',
        'description': 'Partial glucose pathway',
        'node_labels': ['Glucose', 'G6P', 'F6P'],
        'adjacency_matrix': [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    }