"""
Tests for crud.py module
"""
import pytest
import numpy as np
from backend.crud import (
    compute_signatures,
    compute_signature_hash,
    create_network,
    get_all_networks,
    get_network_by_id,
    search_subgraph,
    delete_network
)

@pytest.mark.unit
class TestSignatureComputation:

    def test_compute_signatures_simple(self):
        matrix = np.array([[0, 1], [0, 0]])
        signatures = compute_signatures(matrix)

        assert len(signatures) == 2
        assert signatures[0] == 0
        assert signatures[1] == 5

    def test_compute_signatures_complex(self):
        matrix = np.array([
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0]
        ])
        signatures = compute_signatures(matrix)

        assert len(signatures) == 3
        assert all(isinstance(sig, int) for sig in signatures)

    def test_compute_signatures_empty(self):
        matrix = np.array([[0]])
        signatures = compute_signatures(matrix)

        assert len(signatures) == 1
        assert signatures[0] == 0

    def test_compute_signature_hash(self):
        signatures = [1, 2, 3]
        hash1 = compute_signature_hash(signatures)
        hash2 = compute_signature_hash(signatures)

        assert isinstance(hash1, str)
        assert len(hash1) == 64
        assert hash1 == hash2

    def test_compute_signature_hash_different_inputs(self):
        hash1 = compute_signature_hash([1, 2, 3])
        hash2 = compute_signature_hash([3, 2, 1])

        assert hash1 != hash2

@pytest.mark.db
class TestCreateNetwork:

    def test_create_network_success(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        result = create_network(**sample_network_data)

        assert 'network_id' in result
        assert result['name'] == 'Test_Network'
        assert result['node_count'] == 3
        assert result['edge_count'] == 2
        assert 'signature_hash' in result

    def test_create_network_with_empty_matrix(self, clean_database, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        data = {
            'name': 'Empty_Network',
            'network_type': 'test',
            'organism': 'Test',
            'description': '',
            'node_labels': ['A', 'B'],
            'adjacency_matrix': [[0, 0], [0, 0]]
        }

        result = create_network(**data)
        assert result['edge_count'] == 0

    def test_create_network_computes_signatures(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        result = create_network(**sample_network_data)
        network_id = result['network_id']

        cursor = clean_database.cursor()
        cursor.execute("SELECT signature_array FROM network_matrices WHERE network_id = %s", (network_id,))

        row = cursor.fetchone()
        assert row is not None
        assert len(row[0]) == 3

@pytest.mark.db
class TestGetNetworks:

    def test_get_all_networks_empty(self, clean_database, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        networks = get_all_networks()
        assert isinstance(networks, list)
        assert len(networks) == 0

    def test_get_all_networks_multiple(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        create_network(**sample_network_data)
        data2 = sample_network_data.copy()
        data2['name'] = 'Network_2'
        create_network(**data2)

        networks = get_all_networks()
        assert len(networks) == 2
        assert all('network_id' in net for net in networks)

    def test_get_network_by_id_exists(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        result = create_network(**sample_network_data)
        network_id = result['network_id']

        network = get_network_by_id(network_id)

        assert network is not None
        assert network['network_id'] == network_id
        assert network['name'] == 'Test_Network'
        assert 'adjacency_matrix' in network
        assert 'signature_array' in network

    def test_get_network_by_id_not_exists(self, clean_database, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        network = get_network_by_id(99999)
        assert network is None

@pytest.mark.db
class TestDeleteNetwork:

    def test_delete_network_success(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        result = create_network(**sample_network_data)
        network_id = result['network_id']

        deleted = delete_network(network_id)
        assert deleted is True

        network = get_network_by_id(network_id)
        assert network is None

    def test_delete_network_not_exists(self, clean_database, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        deleted = delete_network(99999)
        assert deleted is False

    def test_delete_network_cascades_matrix(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        result = create_network(**sample_network_data)
        network_id = result['network_id']

        delete_network(network_id)

        cursor = clean_database.cursor()
        cursor.execute("SELECT COUNT(*) FROM network_matrices WHERE network_id = %s", (network_id,))
        count = cursor.fetchone()[0]
        assert count == 0

@pytest.mark.db
@pytest.mark.slow
class TestSubgraphSearch:

    def test_search_subgraph_exact_match(self, clean_database, sample_glycolysis, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        create_network(**sample_glycolysis)

        matches = search_subgraph(
            query_matrix=sample_glycolysis['adjacency_matrix'],
            query_labels=sample_glycolysis['node_labels']
        )

        assert len(matches) >= 1
        assert any(m['match_type'] == 'exact' for m in matches)

    def test_search_subgraph_finds_superset(self, clean_database, sample_glycolysis,
                                            sample_partial_glycolysis, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        create_network(**sample_glycolysis)

        matches = search_subgraph(
            query_matrix=sample_partial_glycolysis['adjacency_matrix'],
            query_labels=sample_partial_glycolysis['node_labels']
        )

        assert len(matches) >= 1
        assert any(m['name'] == 'Glycolysis' for m in matches)

    def test_search_subgraph_no_matches(self, clean_database, sample_glycolysis, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        create_network(**sample_glycolysis)

        different_matrix = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]
        different_labels = ['X', 'Y', 'Z']

        matches = search_subgraph(
            query_matrix=different_matrix,
            query_labels=different_labels
        )

        assert isinstance(matches, list)

    def test_search_subgraph_prefiltering(self, clean_database, sample_network_data, monkeypatch):
        monkeypatch.setattr('backend.crud.get_db_connection', lambda: clean_database)

        create_network(**sample_network_data)

        large_matrix = [[0]*5 for _ in range(5)]
        large_labels = ['A', 'B', 'C', 'D', 'E']

        matches = search_subgraph(
            query_matrix=large_matrix,
            query_labels=large_labels
        )

        assert len(matches) == 0