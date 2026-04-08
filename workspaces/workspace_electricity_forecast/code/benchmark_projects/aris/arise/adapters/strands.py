"""Strands Agents SDK adapter for ARISE.

Converts ARISE ToolSpec objects into Strands-compatible tools and wraps
a Strands Agent so it conforms to ARISE's agent_fn interface.

Usage:
    from arise import ARISE
    from arise.adapters import strands_adapter
    from strands.models import BedrockModel

    agent_fn = strands_adapter(
        model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514"),
        system_prompt="You are a helpful assistant.",
    )

    arise = ARISE(agent_fn=agent_fn, reward_fn=my_reward_fn)
"""

from __future__ import annotations

import functools
from typing import Any, Callable

from arise.types import ToolSpec


def _check_strands_installed() -> None:
    """Raise a helpful ImportError if strands-agents is not installed."""
    try:
        import strands  # noqa: F401
    except ImportError:
        raise ImportError(
            "The strands-agents package is required for the Strands adapter. "
            "Install it with: pip install strands-agents"
        ) from None


# JSON Schema type string -> Python type mapping for building signatures
_SCHEMA_TYPE_TO_PYTHON: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _toolspec_to_strands_tool(tool_spec: ToolSpec) -> Callable:
    """Convert an ARISE ToolSpec into a Strands @tool-decorated callable.

    Strands discovers tool metadata from:
    - Function name (__name__)
    - Docstring (__doc__)
    - Type annotations (__annotations__)
    - inspect.signature parameters

    We dynamically construct a wrapper function that carries all of this
    metadata so Strands can register it properly.
    """
    from strands.tools import tool

    params_schema = tool_spec.parameters
    properties = params_schema.get("properties", {})
    required = set(params_schema.get("required", []))

    # Build parameter annotations dict for the wrapper
    annotations: dict[str, type] = {}
    for param_name, param_schema in properties.items():
        py_type = _SCHEMA_TYPE_TO_PYTHON.get(param_schema.get("type", "string"), str)
        annotations[param_name] = py_type
    annotations["return"] = str

    # Build the parameter string for exec-based function creation.
    # We need a real function with a proper signature so that inspect.signature
    # works correctly for Strands' tool introspection.
    param_parts: list[str] = []
    for param_name, param_schema in properties.items():
        if param_name in required:
            param_parts.append(param_name)
        else:
            default = param_schema.get("default")
            param_parts.append(f"{param_name}={default!r}")

    param_str = ", ".join(param_parts)

    # We use exec to create a function with the exact parameter signature
    # that Strands expects. The function delegates to the original ToolSpec.fn.
    func_name = tool_spec.name
    # Sanitize the function name to be a valid Python identifier
    safe_name = func_name.replace("-", "_").replace(" ", "_")
    if not safe_name.isidentifier():
        safe_name = f"tool_{safe_name}"

    func_code = f"def {safe_name}({param_str}):\n    return _original_fn({', '.join(f'{p}={p}' for p in properties)})"

    namespace: dict[str, Any] = {"_original_fn": tool_spec.fn}
    exec(func_code, namespace)  # noqa: S102
    wrapper = namespace[safe_name]

    wrapper.__name__ = safe_name
    wrapper.__qualname__ = safe_name
    wrapper.__doc__ = tool_spec.description
    wrapper.__annotations__ = annotations

    # Apply the Strands @tool decorator
    decorated = tool(wrapper)
    return decorated


def strands_adapter(
    agent: Any | None = None,
    *,
    model: Any | None = None,
    system_prompt: str | None = None,
    **agent_kwargs: Any,
) -> Callable[[str, list[ToolSpec]], str]:
    """Create an ARISE-compatible agent_fn backed by a Strands Agent.

    Can be called in two ways:

    1. With an existing Agent (preferred)::

        agent_fn = strands_adapter(my_agent)

    2. With model/system_prompt to create agents on the fly::

        agent_fn = strands_adapter(model=BedrockModel(...), system_prompt="...")

    Args:
        agent: An existing ``strands.Agent`` instance. If provided, ``model``
            and ``system_prompt`` are ignored. ARISE tools will be injected
            alongside any tools the agent already has.
        model: A Strands model instance (e.g. ``BedrockModel``). Used to
            create a new Agent when ``agent`` is not provided.
        system_prompt: Optional system prompt for the Strands Agent.
        **agent_kwargs: Additional keyword arguments forwarded to the
            ``strands.Agent`` constructor.

    Returns:
        A callable with signature ``(task: str, tools: list[ToolSpec]) -> str``
        suitable for passing as ``agent_fn`` to :class:`arise.ARISE`.

    Raises:
        ImportError: If ``strands-agents`` is not installed.
        ValueError: If neither ``agent`` nor ``model`` is provided.
    """
    _check_strands_installed()

    if agent is None and model is None:
        raise ValueError(
            "Either 'agent' (an existing strands.Agent) or 'model' "
            "(a Strands model instance) must be provided."
        )

    def agent_fn(task: str, tools: list[ToolSpec]) -> str:
        from strands import Agent

        # Convert ARISE ToolSpecs to Strands tools
        strands_tools = [_toolspec_to_strands_tool(ts) for ts in tools]

        if agent is not None:
            # Use existing agent instance -- inject ARISE tools alongside
            # any tools the agent already has.
            existing_tools = list(agent.tools) if hasattr(agent, "tools") and agent.tools else []
            all_tools = existing_tools + strands_tools
            # Create a new agent with the same config but merged tools
            agent_instance = Agent(
                model=agent.model,
                tools=all_tools,
                system_prompt=getattr(agent, "system_prompt", None),
                callback_handler=None,
            )
        else:
            # Create a fresh agent with the provided model config
            kwargs: dict[str, Any] = {**agent_kwargs}
            kwargs["model"] = model
            kwargs["tools"] = strands_tools
            if system_prompt is not None:
                kwargs["system_prompt"] = system_prompt
            kwargs.setdefault("callback_handler", None)
            agent_instance = Agent(**kwargs)

        result = agent_instance(task)
        return str(result)

    return agent_fn
