"""Tests for SkillRegistry: S3-backed skill sharing registry."""

import json
import os
import sys

from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arise.registry.models import RegistryEntry
from arise.registry.client import SkillRegistry, _entry_to_dict, _dict_to_entry, _skill_from_entry
from arise.types import Skill, SkillOrigin, SkillStatus


# --- Mock S3 helper (same pattern as test_stores.py) ---

def _make_s3_mock(objects: dict | None = None):
    """Create a mock S3 client backed by an in-memory dict."""
    storage = objects or {}

    mock = MagicMock()

    def get_object(Bucket, Key):
        if Key not in storage:
            raise Exception(f"NoSuchKey: {Key}")
        body = MagicMock()
        body.read.return_value = storage[Key]
        return {"Body": body}

    def put_object(Bucket, Key, Body, **kwargs):
        storage[Key] = Body.encode() if isinstance(Body, str) else Body

    mock.get_object = MagicMock(side_effect=get_object)
    mock.put_object = MagicMock(side_effect=put_object)
    mock._storage = storage
    return mock


def _make_skill(name="add_numbers", description="Add two numbers together"):
    return Skill(
        name=name,
        description=description,
        implementation=f"def {name}(a, b):\n    return a + b",
        test_suite=f"def test_{name}():\n    assert {name}(1, 2) == 3",
        origin=SkillOrigin.SYNTHESIZED,
    )


# --- RegistryEntry serialization ---

def test_entry_serialize_roundtrip():
    entry = RegistryEntry(
        name="add_numbers",
        description="Add two numbers",
        implementation="def add_numbers(a, b):\n    return a + b",
        test_suite="def test_add_numbers():\n    assert add_numbers(1, 2) == 3",
        version=2,
        author="test-agent",
        downloads=5,
        avg_success_rate=0.9,
        tags=["math", "arithmetic"],
    )
    d = _entry_to_dict(entry)
    restored = _dict_to_entry(d)

    assert restored.name == "add_numbers"
    assert restored.description == "Add two numbers"
    assert restored.version == 2
    assert restored.author == "test-agent"
    assert restored.downloads == 5
    assert restored.avg_success_rate == 0.9
    assert restored.tags == ["math", "arithmetic"]
    assert "return a + b" in restored.implementation


def test_skill_from_entry():
    entry = RegistryEntry(
        name="multiply",
        description="Multiply two numbers",
        implementation="def multiply(a, b):\n    return a * b",
        test_suite="def test_multiply():\n    assert multiply(3, 4) == 12",
        version=1,
        avg_success_rate=0.95,
    )
    skill = _skill_from_entry(entry)

    assert skill.name == "multiply"
    assert skill.description == "Multiply two numbers"
    assert skill.version == 1
    assert "return a * b" in skill.implementation
    assert skill.origin == SkillOrigin.SYNTHESIZED


# --- publish ---

def test_publish_stores_entry_in_s3():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    entry = registry.publish(skill, tags=["math"])

    assert entry.name == "add_numbers"
    assert entry.version == 1
    assert entry.tags == ["math"]

    # Verify index was written
    index_key = "arise-registry/index.json"
    assert index_key in s3_mock._storage
    index = json.loads(s3_mock._storage[index_key])
    assert "add_numbers" in index["skills"]
    assert 1 in index["skills"]["add_numbers"]

    # Verify entry was written
    entry_key = "arise-registry/skills/add_numbers/v1.json"
    assert entry_key in s3_mock._storage
    stored = json.loads(s3_mock._storage[entry_key])
    assert stored["name"] == "add_numbers"
    assert stored["tags"] == ["math"]


def test_publish_increments_version_on_republish():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    entry1 = registry.publish(skill)
    assert entry1.version == 1

    entry2 = registry.publish(skill)
    assert entry2.version == 2

    index = json.loads(s3_mock._storage["arise-registry/index.json"])
    assert sorted(index["skills"]["add_numbers"]) == [1, 2]


def test_publish_no_tags_defaults_to_empty_list():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    entry = registry.publish(skill)
    assert entry.tags == []


# --- search ---

def test_search_returns_matching_entries():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill(name="add_numbers", description="Add two numbers together")
    registry.publish(skill, tags=["math", "arithmetic"])

    results = registry.search("add numbers math")
    assert len(results) == 1
    assert results[0].name == "add_numbers"


def test_search_returns_empty_for_no_matches():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill(name="add_numbers", description="Add two numbers")
    registry.publish(skill)

    results = registry.search("completely unrelated query xyz")
    assert results == []


def test_search_returns_empty_on_empty_registry():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    results = registry.search("anything")
    assert results == []


def test_search_ranks_by_relevance():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill_a = _make_skill(name="add_numbers", description="Add two numbers together arithmetic")
    skill_b = _make_skill(name="sort_list", description="Sort a list of items")

    registry.publish(skill_a, tags=["math", "add", "numbers"])
    registry.publish(skill_b, tags=["list", "sort"])

    results = registry.search("add numbers arithmetic math")
    assert len(results) >= 1
    assert results[0].name == "add_numbers"


def test_search_respects_limit():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    for i in range(5):
        skill = _make_skill(name=f"math_tool_{i}", description=f"math tool number {i}")
        registry.publish(skill, tags=["math"])

    results = registry.search("math", limit=2)
    assert len(results) <= 2


# --- pull ---

def test_pull_returns_skill_object():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    registry.publish(skill)

    pulled = registry.pull("add_numbers")
    assert isinstance(pulled, Skill)
    assert pulled.name == "add_numbers"
    assert "return a + b" in pulled.implementation


def test_pull_specific_version():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    registry.publish(skill)

    # Modify and republish
    skill2 = Skill(
        name="add_numbers",
        description="Updated add numbers",
        implementation="def add_numbers(a, b):\n    return int(a) + int(b)",
        test_suite="def test_add_numbers():\n    assert add_numbers(1, 2) == 3",
        origin=SkillOrigin.REFINED,
    )
    registry.publish(skill2)

    pulled_v1 = registry.pull("add_numbers", version=1)
    assert "int(a)" not in pulled_v1.implementation

    pulled_v2 = registry.pull("add_numbers", version=2)
    assert "int(a)" in pulled_v2.implementation


def test_pull_defaults_to_latest_version():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    registry.publish(skill)

    skill2 = Skill(
        name="add_numbers",
        description="Better add numbers",
        implementation="def add_numbers(a, b):\n    return int(a + b)",
        test_suite="def test_add_numbers():\n    assert add_numbers(1, 2) == 3",
        origin=SkillOrigin.REFINED,
    )
    registry.publish(skill2)

    pulled = registry.pull("add_numbers")
    assert "int(a + b)" in pulled.implementation


def test_pull_increments_downloads():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill()
    registry.publish(skill)

    registry.pull("add_numbers")
    registry.pull("add_numbers")

    entry_key = "arise-registry/skills/add_numbers/v1.json"
    stored = json.loads(s3_mock._storage[entry_key])
    assert stored["downloads"] == 2


def test_pull_raises_for_missing_skill():
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    try:
        registry.pull("nonexistent_skill")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "nonexistent_skill" in str(e)


# --- SkillForge integration ---

def test_forge_uses_registry_skill_when_match_found():
    """Forge should pull from registry and skip synthesis when high-quality match found."""
    from arise.skills.forge import SkillForge
    from arise.types import GapAnalysis, SandboxResult, TestResult

    # Set up registry with a high-quality skill
    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill(name="add_numbers", description="Add two numbers together")
    entry = registry.publish(skill)

    # Manually set high avg_success_rate in the stored entry
    entry_key = "arise-registry/skills/add_numbers/v1.json"
    stored = json.loads(s3_mock._storage[entry_key])
    stored["avg_success_rate"] = 0.95
    s3_mock._storage[entry_key] = json.dumps(stored).encode()

    # Mock sandbox that always passes
    sandbox_mock = MagicMock()
    sandbox_mock.test_skill.return_value = SandboxResult(
        success=True,
        test_results=[TestResult(passed=True, test_name="test_add_numbers")],
        total_passed=1,
        total_failed=0,
    )

    forge = SkillForge(
        model="gpt-4o-mini",
        sandbox=sandbox_mock,
        max_retries=3,
        registry=registry,
    )

    gap = GapAnalysis(
        description="Add two numbers together",
        suggested_name="add_numbers",
        suggested_signature="def add_numbers(a, b) -> int",
    )

    # Mock library
    library_mock = MagicMock()
    library_mock.get_active_skills.return_value = []

    result = forge.synthesize(gap, library_mock)

    # Should have used registry skill, not called LLM
    assert result.name == "add_numbers"
    sandbox_mock.test_skill.assert_called_once()


def test_forge_skips_registry_when_low_success_rate():
    """Forge should not use registry entry with low avg_success_rate."""
    from arise.skills.forge import SkillForge
    from arise.types import GapAnalysis, SandboxResult, TestResult

    s3_mock = _make_s3_mock()
    registry = SkillRegistry(bucket="test-bucket", prefix="arise-registry", s3_client=s3_mock)

    skill = _make_skill(name="add_numbers", description="Add two numbers")
    registry.publish(skill)

    # avg_success_rate defaults to 0.0 — below 0.7 threshold

    sandbox_mock = MagicMock()
    sandbox_mock.test_skill.return_value = SandboxResult(
        success=True, test_results=[], total_passed=1, total_failed=0
    )

    forge = SkillForge(
        model="gpt-4o-mini",
        sandbox=sandbox_mock,
        max_retries=1,
        registry=registry,
    )

    gap = GapAnalysis(
        description="Add two numbers together",
        suggested_name="add_numbers",
        suggested_signature="def add_numbers(a, b) -> int",
    )

    library_mock = MagicMock()
    library_mock.get_active_skills.return_value = []

    # Should fall through to LLM synthesis — patch llm_call_structured
    with patch("arise.skills.forge.llm_call_structured") as mock_llm:
        mock_llm.return_value = {
            "name": "add_numbers",
            "description": "Add two numbers",
            "implementation": "def add_numbers(a, b):\n    return a + b",
            "test_suite": "def test_add_numbers():\n    assert add_numbers(1, 2) == 3",
        }
        result = forge.synthesize(gap, library_mock)

    mock_llm.assert_called_once()
    assert result.name == "add_numbers"


def test_forge_falls_back_to_synthesis_when_registry_is_none():
    """Forge without registry should proceed directly to LLM synthesis."""
    from arise.skills.forge import SkillForge
    from arise.types import GapAnalysis, SandboxResult

    sandbox_mock = MagicMock()
    sandbox_mock.test_skill.return_value = SandboxResult(
        success=True, test_results=[], total_passed=1, total_failed=0
    )

    forge = SkillForge(
        model="gpt-4o-mini",
        sandbox=sandbox_mock,
        max_retries=1,
        registry=None,
    )

    gap = GapAnalysis(
        description="Add two numbers",
        suggested_name="add_numbers",
        suggested_signature="def add_numbers(a, b) -> int",
    )

    library_mock = MagicMock()
    library_mock.get_active_skills.return_value = []

    with patch("arise.skills.forge.llm_call_structured") as mock_llm:
        mock_llm.return_value = {
            "name": "add_numbers",
            "description": "Add two numbers",
            "implementation": "def add_numbers(a, b):\n    return a + b",
            "test_suite": "",
        }
        result = forge.synthesize(gap, library_mock)

    mock_llm.assert_called_once()
    assert result.name == "add_numbers"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
