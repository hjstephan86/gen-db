"""
End-to-end integration tests
"""
import pytest
from fastapi.testclient import TestClient

from backend.app import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.integration
@pytest.mark.slow
class TestCompleteWorkflow:

    def test_create_search_delete_workflow(self, client, clean_database,
                                          sample_glycolysis, sample_partial_glycolysis,
                                          monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        response1 = client.post("/api/networks", json=sample_glycolysis)
        assert response1.status_code == 200
        full_id = response1.json()["data"]["network_id"]

        response2 = client.post("/api/networks", json=sample_partial_glycolysis)
        assert response2.status_code == 200
        partial_id = response2.json()["data"]["network_id"]

        response3 = client.get("/api/networks")
        assert len(response3.json()["data"]) == 2

        search_data = {
            "node_labels": sample_partial_glycolysis["node_labels"],
            "adjacency_matrix": sample_partial_glycolysis["adjacency_matrix"]
        }
        response4 = client.post("/api/networks/search", json=search_data)
        matches = response4.json()["data"]
        assert len(matches) >= 1

        response5 = client.delete("/api/networks/" + str(full_id))
        assert response5.status_code == 200

        response6 = client.delete("/api/networks/" + str(partial_id))
        assert response6.status_code == 200

        response7 = client.get("/api/networks")
        assert len(response7.json()["data"]) == 0

    def test_concurrent_network_creation(self, client, clean_database, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        networks = []
        for i in range(5):
            networks.append({
                "name": "Network_" + str(i),
                "network_type": "test",
                "organism": "Test",
                "description": "",
                "node_labels": ["A", "B"],
                "adjacency_matrix": [[0, 1], [0, 0]]
            })

        for network_data in networks:
            response = client.post("/api/networks", json=network_data)
            assert response.status_code == 200

        response = client.get("/api/networks")
        assert len(response.json()["data"]) == 5