---
title: ARISE — Self-Evolving Agent Framework
description: Agents that create their own tools at runtime
---


**Your agent works great on the tasks you planned for. ARISE handles the ones you didn't.**

ARISE is a framework-agnostic middleware that gives LLM agents the ability to create their own tools at runtime. When your agent fails at a task, ARISE detects the capability gap, synthesizes a Python tool, validates it in a sandbox, and promotes it to the active library — no human intervention required.

```bash
pip install arise-ai
```

```python
from arise import ARISE
from arise.rewards import task_success

arise = ARISE(
    agent_fn=my_agent,       # any (task, tools) -> str function
    reward_fn=task_success,
    model="gpt-4o-mini",     # cheap model for tool synthesis
)

result = arise.run("Fetch all users from the paginated API")
# Agent fails → ARISE synthesizes fetch_all_paginated → agent succeeds
```

**What it looks like in your terminal:**

```
Episode 1  | FAIL  | reward=0.00 | skills=2   Task: "Fetch paginated users with auth"
Episode 2  | FAIL  | reward=0.00 | skills=2
Episode 3  | FAIL  | reward=0.00 | skills=2

[Evolution triggered — 3 failures on API tasks]
  → Synthesizing 'parse_json_response'... 3/3 tests passed ✓
  → Synthesizing 'fetch_all_paginated'... sandbox fail → refine → 1/1 passed ✓

Episode 4  | OK    | reward=1.00 | skills=4   Agent now has the tools it needs
```

---

## Key Features

- **Self-evolving tool library** — fail → detect gap → synthesize → test → promote
- **Framework-agnostic** — any `(task, tools) -> str` function, Strands, LangGraph, CrewAI
- **Sandboxed validation** — subprocess or Docker, adversarial testing, import restrictions
- **Distributed mode** — S3 + SQS for stateless deployments (Lambda, ECS, AgentCore)
- **Skill registry** — share evolved tools across projects
- **Version control + rollback** — SQLite checkpoints, `arise rollback <version>`
- **A/B testing** — refined skills tested against originals before promotion
- **Reward learning** — learn reward functions from human feedback

---

## Get Started

- [Installation](/getting-started/installation/)
- [Quick Start](/getting-started/quickstart/)
- [How It Works](/getting-started/how-it-works/)

---

## Benchmark Results

| Model | Condition | AcmeCorp (SRE) | DataCorp (Data Eng) |
|-------|-----------|---------------|-------------------|
| **Claude Sonnet** | **ARISE** | **78%** | — |
| Claude Sonnet | No tools | 63% | — |
| GPT-4o-mini | ARISE | 57% | **92%** |
| GPT-4o-mini | No tools | 48% | 50% |

ARISE improves task success by **+9–42 percentage points** across models and domains. Self-evolved tools consistently outperform hand-written baselines because they're shaped by the agent's actual failure patterns.

[Full benchmark details →](/benchmarks/)
