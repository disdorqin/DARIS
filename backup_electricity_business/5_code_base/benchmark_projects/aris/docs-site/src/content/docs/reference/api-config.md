---
title: API - ARISEConfig
---


All configuration for an ARISE instance. Pass to `ARISE(config=...)` or use individual fields as defaults.

```python
from arise import ARISEConfig

config = ARISEConfig(
    model="gpt-4o-mini",
    sandbox_backend="subprocess",
    failure_threshold=5,
    max_evolutions_per_hour=3,
    verbose=True,
)

arise = ARISE(agent_fn=my_agent, reward_fn=reward_fn, config=config)
```

## Fields

### Core

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | `str` | `"gpt-4o-mini"` | LLM model for tool synthesis (not your agent's model) |
| `verbose` | `bool` | `True` | Print episode status and evolution progress |

### Sandbox

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sandbox_backend` | `str` | `"subprocess"` | `"subprocess"` or `"docker"` |
| `sandbox_timeout` | `int` | `30` | Seconds before sandbox kills the process |

### Evolution Triggers

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `failure_threshold` | `int` | `5` | Consecutive failures before evolution triggers |
| `plateau_window` | `int` | `10` | Episodes to look back for plateau detection |
| `plateau_min_improvement` | `float` | `0.05` | Minimum success rate improvement to avoid plateau trigger |
| `max_evolutions_per_hour` | `int` | `3` | Rate limit for evolution cycles (cost control) |
| `max_refinement_attempts` | `int` | `3` | Max LLM retries to fix a failing skill |
| `max_synthesis_workers` | `int` | `3` | Max concurrent tool synthesis threads |

### Library

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_library_size` | `int` | `50` | Max number of active skills before synthesis stops |
| `skill_store_path` | `str` | `"./arise_skills"` | Local SQLite skill library path |
| `trajectory_store_path` | `str` | `"./arise_trajectories"` | Local SQLite trajectory store path |
| `max_trajectories` | `int` | `1000` | Max trajectories to retain (older ones are pruned) |

### Security

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `allowed_imports` | `list[str] \| None` | `None` | Whitelist of importable modules. `None` = no restriction. **Always set in production.** |

### Distributed Mode (S3 + SQS)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `s3_bucket` | `str \| None` | `None` | S3 bucket for distributed skill store |
| `s3_prefix` | `str` | `"arise"` | S3 key prefix |
| `sqs_queue_url` | `str \| None` | `None` | SQS queue URL for trajectory reporting |
| `aws_region` | `str` | `"us-east-1"` | AWS region |
| `skill_cache_ttl_seconds` | `int` | `30` | How often to refresh skills from S3 |

### Skill Registry

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `registry_bucket` | `str \| None` | `None` | S3 bucket for the skill registry |
| `registry_prefix` | `str` | `"arise-registry"` | S3 key prefix for the registry |
| `registry_check_before_synthesis` | `bool` | `True` | Check registry before calling the LLM to synthesize |

### Multi-Model Routing

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_routes` | `dict[str, str] \| None` | `None` | Route specific synthesis tasks to different models |
| `auto_select_model` | `bool` | `False` | Auto-promote the model with the best synthesis track record |

```python
config = ARISEConfig(
    model_routes={
        "gap_detection": "gpt-4o-mini",    # cheap for analysis
        "synthesis": "claude-sonnet-4-5-20250929",  # better code quality
        "refinement": "gpt-4o-mini",
    },
    auto_select_model=True,
)
```

### Telemetry

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_telemetry` | `bool` | `False` | Enable OpenTelemetry spans for evolution steps (requires `arise-ai[otel]`) |

## Examples

**Development (minimal config):**

```python
config = ARISEConfig(
    failure_threshold=2,    # evolve quickly
    verbose=True,
)
```

**Production (locked down):**

```python
config = ARISEConfig(
    model="gpt-4o-mini",
    sandbox_backend="docker",
    sandbox_timeout=30,
    failure_threshold=5,
    max_evolutions_per_hour=3,
    max_library_size=50,
    allowed_imports=["json", "re", "hashlib", "csv", "math", "base64", "datetime"],
    verbose=False,
)
```

**Distributed with registry:**

```python
config = ARISEConfig(
    s3_bucket="arise-skills-prod",
    sqs_queue_url="https://sqs.us-west-2.amazonaws.com/.../arise-trajectories",
    aws_region="us-west-2",
    registry_bucket="arise-registry-prod",
    registry_check_before_synthesis=True,
    model="gpt-4o-mini",
    allowed_imports=["json", "re", "hashlib"],
)
```