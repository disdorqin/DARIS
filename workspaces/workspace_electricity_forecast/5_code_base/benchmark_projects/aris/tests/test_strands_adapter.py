"""Tests for the Strands Agents SDK adapter.

All tests mock the strands package so they run without strands-agents installed.
"""

from __future__ import annotations

import sys
import types
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest

from arise.types import ToolSpec


# ---------------------------------------------------------------------------
# Fixtures: mock the entire strands package before importing the adapter
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_strands(monkeypatch):
    """Inject a mock strands package into sys.modules so the adapter can import it."""
    strands_mod = types.ModuleType("strands")
    strands_tools_mod = types.ModuleType("strands.tools")
    strands_models_mod = types.ModuleType("strands.models")

    # strands.tools.tool: a decorator that just returns the function as-is
    def fake_tool_decorator(fn):
        fn._is_strands_tool = True
        return fn

    strands_tools_mod.tool = fake_tool_decorator

    # strands.Agent: a mock class that records calls
    mock_agent_cls = MagicMock()
    strands_mod.Agent = mock_agent_cls
    strands_mod.tools = strands_tools_mod
    strands_mod.models = strands_models_mod

    monkeypatch.setitem(sys.modules, "strands", strands_mod)
    monkeypatch.setitem(sys.modules, "strands.tools", strands_tools_mod)
    monkeypatch.setitem(sys.modules, "strands.models", strands_models_mod)

    return mock_agent_cls


# ---------------------------------------------------------------------------
# Helper to build simple ToolSpec objects
# ---------------------------------------------------------------------------

def _make_tool_spec(name: str = "greet", description: str = "Say hello") -> ToolSpec:
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    return ToolSpec(
        name=name,
        description=description,
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        },
        fn=greet,
    )


def _make_tool_spec_with_default() -> ToolSpec:
    def add(a: int, b: int = 0) -> int:
        return a + b

    return ToolSpec(
        name="add",
        description="Add two numbers.",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer", "default": 0},
            },
            "required": ["a"],
        },
        fn=add,
    )


# ---------------------------------------------------------------------------
# Tests: _toolspec_to_strands_tool
# ---------------------------------------------------------------------------

class TestToolSpecConversion:
    def test_basic_conversion(self, mock_strands):
        from arise.adapters.strands import _toolspec_to_strands_tool

        ts = _make_tool_spec()
        strands_tool = _toolspec_to_strands_tool(ts)

        assert callable(strands_tool)
        assert strands_tool.__name__ == "greet"
        assert strands_tool.__doc__ == "Say hello"
        assert hasattr(strands_tool, "_is_strands_tool")

    def test_preserves_annotations(self, mock_strands):
        from arise.adapters.strands import _toolspec_to_strands_tool

        ts = _make_tool_spec()
        strands_tool = _toolspec_to_strands_tool(ts)

        assert strands_tool.__annotations__["name"] is str
        assert strands_tool.__annotations__["return"] is str

    def test_tool_is_callable(self, mock_strands):
        from arise.adapters.strands import _toolspec_to_strands_tool

        ts = _make_tool_spec()
        strands_tool = _toolspec_to_strands_tool(ts)

        result = strands_tool(name="World")
        assert result == "Hello, World!"

    def test_tool_with_defaults(self, mock_strands):
        from arise.adapters.strands import _toolspec_to_strands_tool

        ts = _make_tool_spec_with_default()
        strands_tool = _toolspec_to_strands_tool(ts)

        assert strands_tool(a=3) == 3
        assert strands_tool(a=3, b=7) == 10

    def test_annotations_for_numeric_types(self, mock_strands):
        from arise.adapters.strands import _toolspec_to_strands_tool

        ts = _make_tool_spec_with_default()
        strands_tool = _toolspec_to_strands_tool(ts)

        assert strands_tool.__annotations__["a"] is int
        assert strands_tool.__annotations__["b"] is int

    def test_hyphenated_name_sanitized(self, mock_strands):
        from arise.adapters.strands import _toolspec_to_strands_tool

        ts = _make_tool_spec(name="my-tool", description="A tool with hyphens")
        strands_tool = _toolspec_to_strands_tool(ts)

        assert strands_tool.__name__ == "my_tool"


# ---------------------------------------------------------------------------
# Tests: strands_adapter with model parameter
# ---------------------------------------------------------------------------

class TestStrandsAdapterWithModel:
    def test_creates_agent_fn(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        mock_model = MagicMock()
        agent_fn = strands_adapter(model=mock_model)

        assert callable(agent_fn)

    def test_agent_fn_calls_strands_agent(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        mock_model = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = "The answer is 42."
        mock_strands.return_value = mock_agent_instance

        agent_fn = strands_adapter(model=mock_model, system_prompt="Be helpful.")
        tools = [_make_tool_spec()]

        result = agent_fn("What is 6*7?", tools)

        # Agent constructor was called
        mock_strands.assert_called_once()
        ctor_kwargs = mock_strands.call_args
        assert ctor_kwargs.kwargs["model"] is mock_model
        assert ctor_kwargs.kwargs["system_prompt"] == "Be helpful."
        assert len(ctor_kwargs.kwargs["tools"]) == 1

        # Agent instance was called with the task
        mock_agent_instance.assert_called_once_with("What is 6*7?")
        assert result == "The answer is 42."

    def test_result_converted_to_string(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        mock_model = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = 42  # non-string result
        mock_strands.return_value = mock_agent_instance

        agent_fn = strands_adapter(model=mock_model)
        result = agent_fn("task", [])

        assert result == "42"
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: strands_adapter with existing agent
# ---------------------------------------------------------------------------

class TestStrandsAdapterWithAgent:
    def test_merges_existing_tools(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        existing_tool = MagicMock()
        existing_tool.__name__ = "existing"

        mock_existing_agent = MagicMock()
        mock_existing_agent.model = MagicMock()
        mock_existing_agent.tools = [existing_tool]
        mock_existing_agent.system_prompt = "Original prompt"

        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = "done"
        mock_strands.return_value = mock_agent_instance

        agent_fn = strands_adapter(agent=mock_existing_agent)
        arise_tools = [_make_tool_spec()]

        result = agent_fn("do something", arise_tools)

        ctor_kwargs = mock_strands.call_args.kwargs
        # Should have existing_tool + 1 ARISE tool = 2 tools total
        assert len(ctor_kwargs["tools"]) == 2
        assert ctor_kwargs["model"] is mock_existing_agent.model
        assert ctor_kwargs["system_prompt"] == "Original prompt"

    def test_positional_agent_argument(self, mock_strands):
        """strands_adapter(agent) should work as a positional argument."""
        from arise.adapters.strands import strands_adapter

        mock_existing_agent = MagicMock()
        mock_existing_agent.model = MagicMock()
        mock_existing_agent.tools = []
        mock_existing_agent.system_prompt = "Test prompt"

        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = "positional works"
        mock_strands.return_value = mock_agent_instance

        # Pass agent as positional (not keyword)
        agent_fn = strands_adapter(mock_existing_agent)
        result = agent_fn("task", [])

        assert result == "positional works"
        mock_agent_instance.assert_called_once_with("task")

    def test_callback_handler_none_when_agent_provided(self, mock_strands):
        """When wrapping an existing agent, callback_handler should be None."""
        from arise.adapters.strands import strands_adapter

        mock_existing_agent = MagicMock()
        mock_existing_agent.model = MagicMock()
        mock_existing_agent.tools = []
        mock_existing_agent.system_prompt = None

        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = "ok"
        mock_strands.return_value = mock_agent_instance

        agent_fn = strands_adapter(mock_existing_agent)
        agent_fn("task", [])

        ctor_kwargs = mock_strands.call_args.kwargs
        assert ctor_kwargs["callback_handler"] is None

    def test_works_with_no_existing_tools(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        mock_existing_agent = MagicMock()
        mock_existing_agent.model = MagicMock()
        mock_existing_agent.tools = None
        mock_existing_agent.system_prompt = None

        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = "ok"
        mock_strands.return_value = mock_agent_instance

        agent_fn = strands_adapter(agent=mock_existing_agent)
        result = agent_fn("task", [_make_tool_spec()])

        ctor_kwargs = mock_strands.call_args.kwargs
        assert len(ctor_kwargs["tools"]) == 1


# ---------------------------------------------------------------------------
# Tests: validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_raises_if_no_agent_or_model(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        with pytest.raises(ValueError, match="Either 'agent'.*or 'model'"):
            strands_adapter()

    def test_import_error_without_strands(self, monkeypatch):
        # Remove the mock strands and force reimport to simulate not installed
        monkeypatch.delitem(sys.modules, "strands", raising=False)
        monkeypatch.delitem(sys.modules, "strands.tools", raising=False)
        monkeypatch.delitem(sys.modules, "strands.models", raising=False)
        monkeypatch.delitem(sys.modules, "arise.adapters.strands", raising=False)

        # Patch builtins.__import__ to block strands
        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def mock_import(name, *args, **kwargs):
            if name == "strands" or name.startswith("strands."):
                raise ImportError("No module named 'strands'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Now reimport the module fresh
        import importlib
        mod = importlib.import_module("arise.adapters.strands")
        importlib.reload(mod)

        with pytest.raises(ImportError, match="strands-agents"):
            mod._check_strands_installed()


# ---------------------------------------------------------------------------
# Tests: multiple tools
# ---------------------------------------------------------------------------

class TestMultipleTools:
    def test_multiple_arise_tools_converted(self, mock_strands):
        from arise.adapters.strands import strands_adapter

        mock_model = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = "result"
        mock_strands.return_value = mock_agent_instance

        agent_fn = strands_adapter(model=mock_model)
        tools = [
            _make_tool_spec(name="tool_a", description="Tool A"),
            _make_tool_spec(name="tool_b", description="Tool B"),
            _make_tool_spec_with_default(),
        ]

        result = agent_fn("use all tools", tools)

        ctor_kwargs = mock_strands.call_args.kwargs
        assert len(ctor_kwargs["tools"]) == 3
        assert result == "result"


# ---------------------------------------------------------------------------
# Tests: ARISE constructor with agent= parameter
# ---------------------------------------------------------------------------

class TestARISEAgentParam:
    def test_arise_accepts_strands_agent(self, mock_strands):
        """ARISE(agent=strands_agent) should auto-wrap via strands_adapter."""
        from arise.agent import ARISE

        mock_existing_agent = MagicMock()
        # Strands Agent has tool_registry attribute
        mock_existing_agent.tool_registry = MagicMock()
        mock_existing_agent.model = MagicMock()
        mock_existing_agent.tools = []
        mock_existing_agent.system_prompt = "test"

        arise = ARISE(
            agent=mock_existing_agent,
            reward_fn=lambda t: 1.0,
        )

        assert arise.agent_fn is not None
        assert callable(arise.agent_fn)

    def test_arise_rejects_both_agent_and_agent_fn(self, mock_strands):
        """Providing both agent= and agent_fn= should raise ValueError."""
        from arise.agent import ARISE

        mock_existing_agent = MagicMock()
        mock_existing_agent.tool_registry = MagicMock()

        with pytest.raises(ValueError, match="not both"):
            ARISE(
                agent=mock_existing_agent,
                agent_fn=lambda task, tools: "nope",
                reward_fn=lambda t: 1.0,
            )

    def test_arise_rejects_neither_agent_nor_agent_fn(self, mock_strands):
        """Providing neither agent= nor agent_fn= should raise ValueError."""
        from arise.agent import ARISE

        with pytest.raises(ValueError, match="must be provided"):
            ARISE(reward_fn=lambda t: 1.0)

    def test_arise_rejects_unknown_agent_type(self, mock_strands):
        """Passing an object without tool_registry should raise TypeError."""
        from arise.agent import ARISE

        unknown_agent = MagicMock(spec=[])  # no attributes

        with pytest.raises(TypeError, match="Unsupported agent type"):
            ARISE(
                agent=unknown_agent,
                reward_fn=lambda t: 1.0,
            )
