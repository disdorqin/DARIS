---
title: Framework Adapters
---


ARISE works with any callable that takes `(task: str, tools: list) -> str`. Built-in adapters convert `ToolSpec` objects into the native tool format for Strands, LangGraph, and CrewAI.

---

## Custom `agent_fn` (any framework)

The simplest integration — wrap any LLM call in a function:

```python
from arise import ARISE
from arise.rewards import task_success

def agent_fn(task: str, tools: list) -> str:
    # tools is a list of ToolSpec objects:
    # - tool.name: str
    # - tool.description: str
    # - tool.fn: callable
    # - tool.parameters: JSON schema dict

    tool_map = {t.name: t.fn for t in tools}
    tool_descriptions = "\n".join(f"- {t.name}: {t.description}" for t in tools)

    # Call your LLM here (OpenAI, Anthropic, etc.)
    response = your_llm_call(
        system="You are a helpful assistant.",
        user=f"Tools available:\n{tool_descriptions}\n\nTask: {task}",
    )

    # Execute any tool calls from the response, return the final answer
    return response

arise = ARISE(agent_fn=agent_fn, reward_fn=task_success)
```

The `ToolSpec.fn` is a plain Python callable — call it directly with keyword arguments matching the function signature.

---

## Strands Agents

ARISE auto-detects a Strands `Agent` instance when passed via the `agent=` parameter. You can also use `strands_adapter()` directly for more control.

```bash
pip install strands-agents
```

**Auto-detect (recommended):**

```python
from arise import ARISE
from arise.rewards import task_success
from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514")
agent = Agent(model=model, system_prompt="You are an SRE assistant.")

# Pass agent= and ARISE wraps it automatically
arise = ARISE(
    agent=agent,
    reward_fn=task_success,
    model="gpt-4o-mini",
)

arise.run("Check the error rate for service payment-api")
```

**Using `strands_adapter()` directly:**

```python
from arise import ARISE
from arise.adapters.strands import strands_adapter
from arise.rewards import task_success
from strands.models import BedrockModel

# From an existing agent
agent_fn = strands_adapter(existing_agent)

# Or create agents on the fly per episode
agent_fn = strands_adapter(
    model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514"),
    system_prompt="You are an SRE assistant.",
)

arise = ARISE(agent_fn=agent_fn, reward_fn=task_success)
```

ARISE tools are injected alongside any `@tool`-decorated functions the agent already has. The adapter converts `ToolSpec` objects into Strands-compatible callables with proper type annotations and docstrings.

---

## LangGraph

ARISE auto-detects a compiled LangGraph graph (any object with a `get_graph` method).

```bash
pip install langgraph langchain-core langchain-openai
```

**Auto-detect (recommended):**

```python
from arise import ARISE
from arise.rewards import task_success
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
graph = create_react_agent(llm, tools=[])

# Pass graph via agent= — auto-detected by get_graph attribute
arise = ARISE(
    agent=graph,
    reward_fn=task_success,
    model="gpt-4o-mini",
)

arise.run("Summarize the logs from the last hour")
```

**Using `langgraph_adapter()` directly:**

```python
from arise import ARISE
from arise.adapters.langgraph import langgraph_adapter
from arise.rewards import task_success
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
graph = create_react_agent(llm, tools=[])

agent_fn = langgraph_adapter(graph)
# Or create a new react agent per episode:
agent_fn = langgraph_adapter(
    model=ChatOpenAI(model="gpt-4o"),
    system_prompt="You are a helpful assistant.",
)

arise = ARISE(agent_fn=agent_fn, reward_fn=task_success)
```

ARISE tools are converted to `langchain_core.tools.tool`-decorated callables and merged with any tools the graph already has. Because LangGraph compiled graphs are immutable, the adapter creates a new `create_react_agent` instance per episode with the merged tool list.

---

## CrewAI

CrewAI crews are not auto-detected. Use `crewai_adapter()` explicitly.

```bash
pip install crewai
```

```python
from arise import ARISE
from arise.adapters.crewai import crewai_adapter
from arise.rewards import task_success
from crewai import Agent, Task, Crew

# Define your crew with a {task} placeholder in task description
analyst = Agent(
    role="Data Analyst",
    goal="Analyze data and answer questions",
    backstory="Expert data analyst with Python skills.",
)
task = Task(
    description="{task}",   # ARISE fills this in on each run
    agent=analyst,
    expected_output="A clear answer to the task.",
)
crew = Crew(agents=[analyst], tasks=[task])

agent_fn = crewai_adapter(crew)

arise = ARISE(agent_fn=agent_fn, reward_fn=task_success)
arise.run("Calculate the average response time from these logs: ...")
```

ARISE tools are injected into all crew agents before each `kickoff()` and removed afterward to prevent accumulation across calls.

---

## Raw OpenAI / Anthropic

Wrap the API call directly in an `agent_fn`. See the [quickstart](/getting-started/quickstart/) for a full example. For tool-calling APIs (function calling), convert `ToolSpec` objects to the API's tool format:

```python
import openai

def openai_agent_fn(task: str, tools: list) -> str:
    client = openai.OpenAI()

    # Convert ToolSpec to OpenAI function format
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
        }
        for t in tools
    ]
    tool_map = {t.name: t.fn for t in tools}

    messages = [{"role": "user", "content": task}]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools if openai_tools else None,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        # Execute tool calls
        messages.append(msg)
        for tc in msg.tool_calls:
            import json
            fn = tool_map[tc.function.name]
            args = json.loads(tc.function.arguments)
            result = fn(**args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })
```

See [`examples/api_agent.py`](https://github.com/abekek/arise/blob/main/examples/api_agent.py) for a complete HTTP agent example.

---

## Writing a Custom Adapter

Any function matching `(task: str, tools: list[ToolSpec]) -> str` is a valid `agent_fn`. The key contract:

- Receive the task string and current tool list
- Call tools via `tool.fn(*args, **kwargs)` — ARISE wraps these to record invocations
- Return a string (the agent's final answer)
- Let exceptions propagate — ARISE catches them and records them as failed steps

```python
def my_adapter(task: str, tools: list) -> str:
    # Your framework integration here
    result = your_framework.run(task=task, tools=tools)
    return str(result)

arise = ARISE(agent_fn=my_adapter, reward_fn=task_success)
```
