---
title: API - ARISE
---


The main entry point. Wraps your agent function and manages the skill library, trajectory recording, and evolution pipeline.

```python
from arise import ARISE
```

## Constructor

```python
ARISE(
    agent_fn=None,           # (task: str, tools: list) -> str
    reward_fn=task_success,  # (trajectory: Trajectory) -> float
    model="gpt-4o-mini",     # LLM for synthesis (not your agent's model)
    sandbox=None,            # custom Sandbox instance
    skill_library=None,      # custom SkillLibrary (local mode)
    config=None,             # ARISEConfig (overrides model if set)
    agent=None,              # Strands Agent or LangGraph compiled graph
    skill_store=None,        # remote SkillStore (distributed mode)
    trajectory_reporter=None # remote TrajectoryReporter (distributed mode)
)
```

Provide either `agent_fn` or `agent`, not both.

When `agent` is provided, ARISE auto-detects the framework:
- Strands `Agent` (has `tool_registry`) → wraps with `strands_adapter`
- LangGraph compiled graph (has `get_graph`) → wraps with `langgraph_adapter`

## Methods

```python
class ARISE:
    def run(self, task: str, **kwargs) -> str: ...
    def train(self, tasks: list[str], num_episodes: int = None) -> None: ...
    def evolve(self) -> None: ...
    def add_skill(self, fn: Callable, description: str = "") -> None: ...
    def remove_skill(self, name: str) -> None: ...
    def start_ab_test(self, skill_a: Skill, skill_b: Skill, min_episodes: int = 20) -> SkillABTest: ...
    def export(self, path: str) -> None: ...
    def rollback(self, version: int) -> None: ...
```

| Method | Description |
|--------|-------------|
| `run(task, **kwargs)` | Run a single task. Records the trajectory, computes the reward, and triggers evolution if thresholds are met. Kwargs land in `trajectory.metadata`. |
| `train(tasks, num_episodes)` | Run multiple tasks in sequence, cycling through the list. Defaults to `len(tasks)` episodes. |
| `evolve()` | Manually trigger one evolution cycle. Only works in local mode. |
| `add_skill(fn, description)` | Add a hand-written Python function to the skill library. Promoted immediately. Not available in distributed mode. |
| `remove_skill(name)` | Deprecate an active skill by name. Raises `ValueError` if not found. |
| `start_ab_test(skill_a, skill_b, min_episodes)` | Start an A/B test between two skill versions. Called automatically by `evolve()` when patching. |
| `export(path)` | Export all active skills as individual `.py` files. |
| `rollback(version)` | Roll back the skill library to a previous version checkpoint. |

### Usage Examples

```python
# Single task
result = arise.run("Compute the SHA-256 of /tmp/data.txt")

# Pass signals to your reward function
result = arise.run(task, success=True)
result = arise.run(task, expected="Paris")
result = arise.run(task, expected_output="42")
```

```python
# Training loop
tasks = [
    "Fetch users from /api/users",
    "Parse the metrics response",
    "Compute the SHA-256 of /tmp/data.txt",
]
arise.train(tasks, num_episodes=30)
```

```python
# Add a hand-written skill
def compute_sha256(path: str) -> str:
    """Compute SHA-256 hash of a file."""
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

arise.add_skill(compute_sha256, description="Compute SHA-256 hash of a file")
```

---

## Properties

```python
class ARISE:
    skills: list[Skill]
    stats: dict
    last_evolution: EvolutionReport | None
    evolution_history: list[EvolutionReport]
```

| Property | Type | Description |
|----------|------|-------------|
| `skills` | `list[Skill]` | Currently active skills. |
| `stats` | `dict` | Summary statistics: episode count, active/testing/deprecated counts, success rates, top performers. |
| `last_evolution` | `EvolutionReport \| None` | Most recent evolution report, or `None` if no evolution has run. |
| `evolution_history` | `list[EvolutionReport]` | All evolution reports from this session. |

```python
# Stats example
print(arise.stats)
# {
#   "episodes_run": 42,
#   "active": 4,
#   "testing": 1,
#   "deprecated": 2,
#   "total_skills": 7,
#   "library_version": 8,
#   "avg_success_rate": 0.847,
#   "recent_success_rate": 0.9,
#   "top_performers": [
#     {"name": "compute_sha256", "success_rate": 1.0, "invocations": 23},
#   ]
# }
```

```python
# Evolution report
report = arise.last_evolution
if report:
    print(report.tools_promoted)  # ["compute_sha256"]
    print(report.tools_rejected)  # [{"name": "fetch_api", "reason": "sandbox failure"}]
    print(report.duration_ms)     # 45000
    print(report.gaps_detected)   # ["compute_sha256", "fetch_all_paginated"]
```

---

## Factory Functions

```python
from arise import create_distributed_arise, ARISEConfig

config = ARISEConfig(
    s3_bucket="my-skills-bucket",
    sqs_queue_url="https://sqs.us-west-2.amazonaws.com/.../arise-trajectories",
    aws_region="us-west-2",
)

arise = create_distributed_arise(
    agent_fn=my_agent,
    reward_fn=task_success,
    config=config,
)
```

`create_distributed_arise()` is a convenience factory for distributed mode. Requires `config.s3_bucket` and `config.sqs_queue_url`.
