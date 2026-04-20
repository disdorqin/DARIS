# ARISE — Adaptive Runtime Improvement through Self-Evolution

[![PyPI version](https://img.shields.io/pypi/v/arise-ai.svg)](https://pypi.org/project/arise-ai/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://pypi.org/project/arise-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-arise--ai.dev-blue)](https://arise-ai.dev)

**Your agent works great on the tasks you planned for. ARISE handles the ones you didn't.**

ARISE is a framework-agnostic middleware that gives LLM agents the ability to create their own tools at runtime. When your agent fails at a task, ARISE detects the capability gap, synthesizes a Python tool, validates it in a sandbox, and promotes it to the active library — no human intervention required.

**[Documentation](https://arise-ai.dev)** | **[Quick Start](https://arise-ai.dev/getting-started/quickstart/)** | **[PyPI](https://pypi.org/project/arise-ai/)**

```bash
pip install arise-ai
```

```python
from arise import ARISE
from arise.rewards import task_success

arise = ARISE(
    agent_fn=my_agent,           # any (task, tools) -> str function
    reward_fn=task_success,
    model="gpt-4o-mini",         # cheap model for tool synthesis
)

result = arise.run("Fetch all users from the paginated API")
# Agent fails → ARISE synthesizes fetch_all_paginated tool → agent succeeds
```

## What It Looks Like

```
Episode 1  | FAIL  | reward=0.00 | skills=2   Task: "Fetch paginated users with auth"
Episode 2  | FAIL  | reward=0.00 | skills=2
Episode 3  | FAIL  | reward=0.00 | skills=2

[Evolution triggered — 3 failures on API tasks]
  → Synthesizing 'parse_json_response'... 3/3 tests passed ✓
  → Synthesizing 'fetch_all_paginated'... sandbox fail → refine → 1/1 passed ✓

Episode 4  | OK    | reward=1.00 | skills=4   Agent now has the tools it needs
```

## Key Features

- **Self-evolving tool library** — fail → detect gap → synthesize → sandbox test → promote
- **Framework-agnostic** — any `(task, tools) -> str` function, [Strands](https://arise-ai.dev/guide/adapters/#strands-agents), [LangGraph](https://arise-ai.dev/guide/adapters/#langgraph), [CrewAI](https://arise-ai.dev/guide/adapters/#crewai)
- **Sandboxed validation** — subprocess or Docker, adversarial testing, import restrictions
- **Distributed mode** — S3 + SQS for stateless deployments (Lambda, ECS, AgentCore)
- **Skill registry** — share evolved tools across projects
- **Version control + rollback** — SQLite checkpoints, `arise rollback <version>`
- **A/B testing** — refined skills tested against originals before promotion
- **Web Console** — create agents, watch evolution live, inspect evolved code (`arise console`)
- **Dashboard** — terminal TUI and web UI for monitoring

## Benchmark Results

| Model | Condition | AcmeCorp (SRE) | DataCorp (Data Eng) |
|-------|-----------|---------------|-------------------|
| **Claude Sonnet** | **ARISE** | **78%** | — |
| Claude Sonnet | No tools | 63% | — |
| GPT-4o-mini | ARISE | 57% | **92%** |
| GPT-4o-mini | No tools | 48% | 50% |

ARISE improves task success by **+9–42 percentage points** across models and domains. See the [full benchmark results](https://arise-ai.dev/benchmarks/).

## ARISE Console

A web UI for creating agents, watching evolution live, and inspecting evolved tools:

```bash
arise console
# Opens http://localhost:8080
```

- **Create agents** — pick model, set system prompt, choose reward function
- **Live terminal feed** — watch episodes and evolution in real-time via WebSocket
- **Skill inspector** — syntax-highlighted code, test suite, performance metrics
- **Editable config** — change reward function, system prompt, failure threshold on the fly
- **All Skills / Evolution Log** — global views across all agents

## Documentation

Full documentation at **[arise-ai.dev](https://arise-ai.dev)**:

- [Installation](https://arise-ai.dev/getting-started/installation/) — install and configure
- [Quick Start](https://arise-ai.dev/getting-started/quickstart/) — complete evolution loop walkthrough
- [How It Works](https://arise-ai.dev/getting-started/how-it-works/) — the 5-step evolution pipeline
- [Reward Functions](https://arise-ai.dev/guide/rewards/) — built-in and custom reward functions
- [Safety & Validation](https://arise-ai.dev/guide/safety/) — sandbox, adversarial testing, production recommendations
- [Distributed Mode](https://arise-ai.dev/guide/distributed/) — S3 + SQS for stateless deployments
- [Framework Adapters](https://arise-ai.dev/guide/adapters/) — Strands, LangGraph, CrewAI, raw OpenAI/Anthropic
- [CLI Reference](https://arise-ai.dev/reference/cli/) — all CLI commands
- [API Reference](https://arise-ai.dev/reference/api-arise/) — ARISE class, config, types

## Examples

| Example | Description |
|---------|-------------|
| [`quickstart_evolution.py`](./examples/quickstart_evolution.py) | Full evolution loop: agent fails → ARISE evolves tool → agent succeeds |
| [`quickstart.py`](./examples/quickstart.py) | Math agent evolves statistics tools |
| [`api_agent.py`](./examples/api_agent.py) | HTTP agent evolves auth + pagination (mock server) |
| [`devops_agent.py`](./examples/devops_agent.py) | DevOps agent evolves log analysis tools |
| [`strands_agent.py`](./examples/strands_agent.py) | Strands integration with Bedrock |
| [`demo/agentcore/`](./demo/agentcore/) | AgentCore deployment with A2A protocol |

## Install

```bash
pip install arise-ai              # core (just pydantic)
pip install arise-ai[aws]         # + boto3 for distributed mode
pip install arise-ai[litellm]     # + litellm for multi-provider LLM
pip install arise-ai[docker]      # + docker sandbox backend
pip install arise-ai[dashboard]   # + rich, fastapi for dashboard
pip install arise-ai[otel]        # + opentelemetry for tracing
pip install arise-ai[all]         # everything
```

## Related Work

ARISE builds on ideas from [LATM](https://arxiv.org/abs/2305.17126), [VOYAGER](https://arxiv.org/abs/2305.16291), [CREATOR](https://arxiv.org/abs/2305.14318), [ADAS](https://arxiv.org/abs/2408.08435), and [CRAFT](https://arxiv.org/abs/2309.17428). ARISE adds the production layer: framework-agnostic integration, sandboxed validation, adversarial testing, version control, distributed deployment, and A/B testing.

## License

MIT
