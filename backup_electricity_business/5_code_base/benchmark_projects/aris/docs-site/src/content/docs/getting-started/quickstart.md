---
title: Quick Start
---


This walkthrough shows the complete evolution loop: an agent that can't do a task, ARISE detecting the gap, synthesizing a tool, and the agent succeeding on retry.

The full example lives at [`examples/quickstart_evolution.py`](https://github.com/abekek/arise/blob/main/examples/quickstart_evolution.py).

## Setup

```bash
pip install arise-ai[litellm]
export OPENAI_API_KEY=sk-...
```

## Step 1: Define your agent function

ARISE requires a function with signature `(task: str, tools: list) -> str`. Each tool in the list is a `ToolSpec` with `.name`, `.description`, and `.fn` attributes.

```python
import io, contextlib
from arise.llm import llm_call

def agent_fn(task: str, tools: list) -> str:
    tool_map = {t.name: t.fn for t in tools}
    tool_desc = "\n".join(f"- {t.name}: {t.description}" for t in tools)

    code = llm_call([{"role": "user", "content": (
        f"TOOLS:\n{tool_desc}\n\nTASK: {task}\n\n"
        "Write Python that calls ONLY the tools above. Print the final answer.\n"
        "If no tool fits, print 'TOOL_MISSING: <what you need>'. Code only, no markdown."
    )}], model="gpt-4o-mini")

    code = code.strip().removeprefix("```python").removeprefix("```").removesuffix("```")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, dict(tool_map))
        return buf.getvalue().strip() or "No output"
    except Exception as e:
        return f"Error: {e}"
```

## Step 2: Define a reward function

The reward function receives a `Trajectory` and returns a float in `[0.0, 1.0]`. Here we check whether the output contains a valid SHA-256 hash:

```python
import re
from arise.types import Trajectory

def sha256_reward(trajectory: Trajectory) -> float:
    outcome = trajectory.outcome or ""
    return 1.0 if re.search(r"\b[a-f0-9]{64}\b", outcome) else 0.0
```

## Step 3: Bootstrap with a seed skill

Start the library with a single tool. ARISE will evolve more as needed.

```python
import inspect
from arise import ARISE, SkillLibrary
from arise.config import ARISEConfig
from arise.types import Skill, SkillOrigin, SkillStatus

def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    with open(path) as f:
        return f.read()

library = SkillLibrary("./arise_skills")
skill = Skill(
    name="read_file",
    description="Read a file's contents",
    implementation=inspect.getsource(read_file),
    origin=SkillOrigin.MANUAL,
    status=SkillStatus.ACTIVE,
)
library.add(skill)
library.promote(skill.id)
```

## Step 4: Create the ARISE instance

```python
arise = ARISE(
    agent_fn=agent_fn,
    reward_fn=sha256_reward,
    model="gpt-4o-mini",
    skill_library=library,
    config=ARISEConfig(
        failure_threshold=1,        # evolve after just 1 failure (demo)
        max_evolutions_per_hour=5,
        verbose=True,
    ),
)
```

## Step 5: Run — watch the agent fail, then succeed

```python
task = "Compute the SHA-256 hash of /tmp/arise_demo/hello.txt"

# First run: agent fails — no hashing tool available
result = arise.run(task)
# [ARISE] Episode 1 | FAIL | reward=0.00 | skills=1

# Trigger evolution manually (or let it happen automatically after enough failures)
arise.evolve()
# [ARISE] Evolution triggered — analyzing gaps...
# [ARISE] Found 1 capability gaps.
# [ARISE] Synthesizing 1 tools in parallel (max_workers=3)...
# [ARISE] Skill 'compute_sha256' created and promoted!

# Check what was synthesized
for s in arise.skills:
    print(f"  - {s.name} ({s.origin.value})")
# - read_file (manual)
# - compute_sha256 (synthesized)

# Second run: agent uses the new tool and succeeds
result = arise.run(task)
# [ARISE] Episode 2 | OK | reward=1.00 | skills=2
print(result)
# b94d27b9934d3e08a52e52d7da7dabfac484efe04294e576...
```

## What you'd see in the terminal

```
============================================================
STEP 1: Agent attempts task (should fail)
============================================================
[ARISE] Episode 1 | FAIL | reward=0.00 | skills=1
Result: TOOL_MISSING: sha256 hashing

============================================================
STEP 2: ARISE evolves new tools from failure
============================================================
[ARISE] Evolution triggered — analyzing gaps...
[ARISE] Found 1 capability gaps.
[ARISE] Synthesizing 1 tools in parallel (max_workers=3)...
[ARISE] Skill 'compute_sha256' created and promoted!

Active skills after evolution:
  - read_file (manual)
  - compute_sha256 (synthesized)

============================================================
STEP 3: Agent retries task (should succeed)
============================================================
[ARISE] Episode 2 | OK | reward=1.00 | skills=2
Result: b94d27b9934d3e08a52e52d7da7dabfac484efe04294e576...

Expected: b94d27b9934d3e08a52e52d7da7dabfac484efe04294e576...
Match:    True
```

## Next steps

- Run multiple tasks in sequence with [`arise.train(tasks)`](/reference/api-arise/)
- Check evolution reports: `arise.last_evolution.tools_promoted`
- Explore the [reward functions guide](/guide/rewards/) for production-ready scoring
- See [Framework Adapters](/guide/adapters/) to use Strands, LangGraph, or CrewAI
- View your skill library with `arise status ./arise_skills`

:::tip[Automatic evolution]
In production, you don't need to call `evolve()` manually. ARISE triggers it automatically after `failure_threshold` consecutive failures. Set a higher threshold (default: 5) so evolution is triggered by meaningful patterns, not noise.
:::