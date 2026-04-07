---
title: Console
---

The ARISE Console is a web UI for creating agents, watching them evolve tools in real-time, and inspecting evolved code.

```bash
arise console
# Opens http://localhost:8080
```

## Features

### Agent Management

Create and manage multiple agents from the browser. Each agent has its own skill library, trajectory store, and configuration.

- **Create agents** — pick a model (OpenAI, Anthropic, Bedrock), write a system prompt, choose a reward function
- **Per-agent stats** — skills count, success rate, episode count, evolution count
- **Live status** — running, stopped, evolving

### Live Terminal Feed

Watch your agent work in real-time. The Live tab shows a terminal-style feed of episodes and evolution events streamed over WebSocket.

- Episodes with color-coded status (green OK, red FAIL)
- Evolution blocks: gap detection, synthesis progress, test results, promotion
- Run tasks interactively from the input bar
- Events persist across page reloads

### Skill Inspector

Click any evolved skill to see:

- Full implementation with syntax-highlighted Python code
- Test suite with standard and adversarial test results
- Performance metrics: success rate, invocations, latency, version
- Export as `.py` or deprecate

### Editable Configuration

Change agent settings on the fly from the Config tab:

- System prompt
- Reward function (task_success, answer_match, code_execution, efficiency, LLM judge)
- Failure threshold
- Sandbox backend

Changes take effect on the next run — the ARISE instance is recreated with the new config.

### Global Views

- **All Skills** — table of every skill across all agents, sortable by success rate
- **Evolution Log** — timeline of evolution cycles with gaps detected, tools promoted/rejected

## Configuration

```bash
# Custom port
arise console --port 3000

# Custom data directory
arise console --data-dir ./my-arise-data

# Custom host
arise console --host 127.0.0.1
```

Agent data is stored in `~/.arise/console/` by default:
- `agents.json` — agent configs (persisted across restarts)
- `agents/<id>/skills/` — SQLite skill library per agent
- `agents/<id>/trajectories/` — SQLite trajectory store per agent
- `agents/<id>/events.jsonl` — live feed event log

## Reward Functions

The Console includes these reward function presets:

| Function | Description |
|----------|-------------|
| `task_success` | Checks metadata signals (expected output, success flag). Falls back to 1.0 if no errors. |
| `answer_match_reward` | Compares output against expected answer. 1.0 exact, 0.7 substring, 0.0 no match. |
| `code_execution_reward` | 1.0 if no tool errors, minus 0.25 per error. |
| `efficiency_reward` | Penalizes extra steps. 1.0 for 1 step, -0.1 per additional. |
| `llm_judge_reward` | LLM rates response quality 0-1. Uses the agent's own model. ~$0.001/call. |

## Model Support

The Console auto-maps short model names to provider-specific IDs when AWS credentials are available:

| Short Name | Maps To |
|-----------|---------|
| `claude-sonnet-4-5` | `bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `claude-sonnet-4` | `bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0` |
| `claude-haiku-4-5` | `bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `gpt-4o` | `gpt-4o` (requires `OPENAI_API_KEY`) |
| `gpt-4o-mini` | `gpt-4o-mini` (requires `OPENAI_API_KEY`) |

You can also use full provider-prefixed names directly: `bedrock/...`, `anthropic/...`, `openai/...`.
