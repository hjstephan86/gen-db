"""
Tests for app.py FastAPI application
"""
import pytest
from fastapi.testclient import TestClient

from backend.app import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.unit
class TestHealthEndpoint:

    def test_health_check(self, client):
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.integration
class TestNetworkEndpoints:

    def test_get_networks_empty(self, client, clean_database, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        response = client.get("/api/networks")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    def test_create_network_valid(self, client, clean_database, sample_network_data, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        response = client.post("/api/networks", json=sample_network_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "network_id" in data["data"]

    def test_create_network_invalid_data(self, client):
        invalid_data = {
            "name": "Test",
        }

        response = client.post("/api/networks", json=invalid_data)
        assert response.status_code == 422

    def test_get_network_by_id_exists(self, client, clean_database, sample_network_data, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        create_response = client.post("/api/networks", json=sample_network_data)
        network_id = create_response.json()["data"]["network_id"]

        response = client.get("/api/networks/" + str(network_id))

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["network_id"] == network_id

    def test_get_network_by_id_not_exists(self, client, clean_database, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        response = client.get("/api/networks/99999")
        assert response.status_code == 404

    def test_delete_network_success(self, client, clean_database, sample_network_data, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        create_response = client.post("/api/networks", json=sample_network_data)
        network_id = create_response.json()["data"]["network_id"]

        response = client.delete("/api/networks/" + str(network_id))

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_network_not_exists(self, client, clean_database, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        response = client.delete("/api/networks/99999")
        assert response.status_code == 404

@pytest.mark.integration
class TestSearchEndpoint:

    def test_search_networks_valid(self, client, clean_database, sample_glycolysis, monkeypatch):
        from backend import crud
        monkeypatch.setattr(crud, 'get_db_connection', lambda: clean_database)

        client.post("/api/networks", json=sample_glycolysis)

        search_data = {
            "node_labels": ["Glucose", "G6P"],
            "adjacency_matrix": [[0, 1], [0, 0]]
        }

        response = client.post("/api/networks/search", json=search_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_search_networks_invalid_data(self, client):
        invalid_data = {
            "node_labels": ["A", "B"],
        }

        response = client.post("/api/networks/search", json=invalid_data)
        assert response.status_code == 422