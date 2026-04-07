---
title: Reward Functions
---


The reward function is the signal ARISE uses to decide whether an agent succeeded. It receives a `Trajectory` and returns a float in `[0.0, 1.0]`. Scores below `0.5` are treated as failures.

```python
from arise.types import Trajectory

def my_reward(trajectory: Trajectory) -> float:
    ...
    return 1.0  # success
```

## The Trajectory Object

```python
@dataclass
class Trajectory:
    task: str                        # the task string passed to arise.run()
    steps: list[Step]                # every tool call the agent made
    outcome: str                     # agent's final response (truncated to 1000 chars)
    reward: float                    # filled in after reward_fn runs
    skill_library_version: int       # library version when this episode ran
    timestamp: datetime
    metadata: dict[str, Any]         # kwargs passed to arise.run(task, **kwargs)
```

Each `Step` in `trajectory.steps`:

```python
@dataclass
class Step:
    observation: str
    reasoning: str
    action: str              # tool name that was called
    action_input: dict       # args passed to the tool
    result: str              # tool return value (truncated to 500 chars)
    error: str | None        # exception message if the tool raised
    latency_ms: float
```

Pass signals to your reward function via `arise.run()` keyword arguments — they land in `trajectory.metadata`:

```python
arise.run(task, success=True)
arise.run(task, expected="42")
arise.run(task, expected_output="42", rubric="must be an integer")
```

---

## Built-in Reward Functions

All built-ins are importable from `arise.rewards`:

```python
from arise.rewards import (
    task_success,
    code_execution_reward,
    answer_match_reward,
    efficiency_reward,
    llm_judge_reward,
)
```

### `task_success`

General-purpose reward. Checks signals in order:

1. `metadata['success']` — explicit `True`/`False` from the caller
2. `metadata['expected']` — if provided, checks whether that string appears in `outcome`
3. Step errors — returns `0.0` if any tool call raised an exception
4. Falls back to `1.0` (assumes success)

```python
from arise.rewards import task_success

arise = ARISE(agent_fn=my_agent, reward_fn=task_success)

# Explicit control
arise.run(task, success=True)
arise.run(task, success=False)

# Expected output matching
arise.run(task, expected="Paris")  # 1.0 if "Paris" in outcome, else 0.0
```

**Best for:** general tasks where you can provide an explicit signal or expected answer.

---

### `code_execution_reward`

Scores based on tool execution errors: `1.0` if no errors, minus `0.25` per error, floored at `0.0`.

```python
from arise.rewards import code_execution_reward

arise = ARISE(agent_fn=my_agent, reward_fn=code_execution_reward)
```

**Best for:** agents that call tools heavily (APIs, file I/O, code execution) where clean execution is the primary success signal.

---

### `answer_match_reward`

Strict output matching against `metadata['expected_output']` or `metadata['expected']`:

- `1.0` — exact match (stripped)
- `0.7` — substring match (case-insensitive)
- `0.0` — no match
- `0.5` — no expected value provided

```python
from arise.rewards import answer_match_reward

arise.run("What is 2 + 2?", expected_output="4")
```

**Best for:** Q&A agents, extraction tasks, factual queries with known correct answers.

---

### `efficiency_reward`

Penalizes extra steps. Score = `max(0.0, 1.0 - (n_steps - 1) * 0.1)`. An agent that solves a task in 1 step gets `1.0`; each additional step reduces the score by `0.1`.

```python
from arise.rewards import efficiency_reward
```

**Best for:** agents where conciseness matters — penalizes agents that call tools redundantly or loop unnecessarily.

---

### `llm_judge_reward`

Uses an LLM to rate the trajectory quality on a 0–1 scale. Sends the task, outcome, and step summary to the judge model.

```python
from arise.rewards import llm_judge_reward
from functools import partial

reward = partial(llm_judge_reward, model="gpt-4o-mini")
arise = ARISE(agent_fn=my_agent, reward_fn=reward)
```

**Cost:** ~$0.001 per call with gpt-4o-mini.

**Best for:** open-ended tasks where correctness is hard to measure programmatically (summaries, plans, explanations).

:::warning[Cost]
`llm_judge_reward` makes an LLM call on every episode. At scale, prefer a programmatic reward and use `llm_judge_reward` only for evaluation or for tasks with no other signal.
:::
---

## `LearnedReward`

Learns from human feedback via few-shot prompting. Falls back to `task_success` until `min_examples` are collected.

```python
from arise.rewards.learned import LearnedReward

reward = LearnedReward(
    min_examples=10,          # fall back to task_success until this many examples
    persist_path="./feedback", # save/load feedback across restarts
    model="gpt-4o-mini",
    max_examples=50,           # keep the most recent N examples
)

# Collect feedback from human review
reward.add_feedback(trajectory, score=0.9)
reward.add_feedback(trajectory2, score=0.2)

arise = ARISE(agent_fn=my_agent, reward_fn=reward)
```

**Best for:** domain-specific tasks where success is subjective and you have humans to rate a few examples.

---

## `CompositeReward`

Weighted blend of multiple reward functions.

```python
from arise.rewards import task_success, efficiency_reward, code_execution_reward
from arise.rewards.composite import CompositeReward

reward = CompositeReward([
    (task_success,          0.6),  # weight 60%
    (code_execution_reward, 0.3),  # weight 30%
    (efficiency_reward,     0.1),  # weight 10%
])

arise = ARISE(agent_fn=my_agent, reward_fn=reward)
```

Weights are normalized automatically — they don't need to sum to 1.

**Best for:** production systems where you care about correctness, tool health, and efficiency simultaneously.

---

## Writing a Custom Reward

Any callable that takes a `Trajectory` and returns a float works:

```python
def domain_reward(trajectory: Trajectory) -> float:
    """Custom reward for a report-generation agent."""
    outcome = trajectory.outcome.lower()

    # Must contain required sections
    required = ["summary", "recommendations", "conclusion"]
    if not all(kw in outcome for kw in required):
        return 0.0

    # Penalize tool errors
    errors = sum(1 for s in trajectory.steps if s.error)
    error_penalty = errors * 0.1

    # Bonus for conciseness
    length_bonus = 0.1 if len(outcome) < 2000 else 0.0

    return max(0.0, min(1.0, 1.0 - error_penalty + length_bonus))

arise = ARISE(agent_fn=my_agent, reward_fn=domain_reward)
```

:::tip[Reward signals via metadata]
Pass signals from your application into the reward function using `arise.run()` kwargs:

```python
arise.run(task, validated=True, quality_score=0.87)

# In your reward function:
def my_reward(trajectory: Trajectory) -> float:
    if trajectory.metadata.get("validated"):
        return trajectory.metadata.get("quality_score", 0.5)
    return 0.0
```
:::
