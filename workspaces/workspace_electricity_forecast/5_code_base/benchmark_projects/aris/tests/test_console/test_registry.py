import os
import tempfile
import pytest
from arise.console.registry import AgentRegistry
from arise.console.schemas import AgentCreate


@pytest.fixture
def registry(tmp_path):
    return AgentRegistry(data_dir=str(tmp_path))


def test_create_agent(registry):
    req = AgentCreate(name="test-agent", model="gpt-4o-mini")
    agent = registry.create(req)
    assert agent["id"]
    assert agent["name"] == "test-agent"
    assert agent["status"] == "stopped"


def test_list_agents(registry):
    registry.create(AgentCreate(name="a1"))
    registry.create(AgentCreate(name="a2"))
    agents = registry.list()
    assert len(agents) == 2


def test_get_agent(registry):
    created = registry.create(AgentCreate(name="test"))
    agent = registry.get(created["id"])
    assert agent["name"] == "test"


def test_get_nonexistent_agent(registry):
    assert registry.get("nonexistent") is None


def test_delete_agent(registry):
    created = registry.create(AgentCreate(name="test"))
    registry.delete(created["id"])
    assert registry.get(created["id"]) is None


def test_persistence(tmp_path):
    reg1 = AgentRegistry(data_dir=str(tmp_path))
    reg1.create(AgentCreate(name="persisted"))

    reg2 = AgentRegistry(data_dir=str(tmp_path))
    agents = reg2.list()
    assert len(agents) == 1
    assert agents[0]["name"] == "persisted"
