import pytest
from fastapi.testclient import TestClient
from arise.console.server import create_console_app


@pytest.fixture
def client(tmp_path):
    app = create_console_app(data_dir=str(tmp_path))
    return TestClient(app)


def test_list_agents_empty(client):
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_agent(client):
    resp = client.post("/api/agents", json={"name": "test-agent", "model": "gpt-4o-mini"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test-agent"
    assert data["status"] == "stopped"


def test_get_agent(client):
    create = client.post("/api/agents", json={"name": "test"})
    agent_id = create.json()["id"]
    resp = client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "test"


def test_get_nonexistent_agent(client):
    resp = client.get("/api/agents/nonexistent")
    assert resp.status_code == 404


def test_delete_agent(client):
    create = client.post("/api/agents", json={"name": "test"})
    agent_id = create.json()["id"]
    resp = client.delete(f"/api/agents/{agent_id}")
    assert resp.status_code == 204
    resp = client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 404
