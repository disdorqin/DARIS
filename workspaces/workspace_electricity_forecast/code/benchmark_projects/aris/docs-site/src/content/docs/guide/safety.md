---
title: Safety & Validation
---


ARISE generates and executes Python code at runtime. This page covers the built-in safety mechanisms and production recommendations.

:::warning[Generated code is untrusted]
All synthesized skills are untrusted third-party code until they pass the full validation pipeline. Apply the same security discipline you would to any user-submitted code.
:::
See [SECURITY.md](https://github.com/abekek/arise/blob/main/SECURITY.md) for the full threat model.

---

## Validation Pipeline

Every synthesized skill passes through multiple layers before promotion:

| Layer | What it does |
|-------|-------------|
| **Sandbox** | Runs tests in an isolated process or Docker container with a timeout |
| **Test suite** | LLM writes tests alongside the tool; all must pass |
| **Adversarial testing** | Separate LLM call tries to break the tool (edge cases, type boundaries, security) |
| **Import restrictions** | `allowed_imports` whitelist blocks dangerous modules |
| **Promotion gate** | Only skills passing all layers become `ACTIVE` |
| **Version control** | SQLite checkpoint before every promotion; rollback anytime |

---

## Sandbox

Generated code runs in an isolated environment. Configure it in `ARISEConfig`:

```python
from arise import ARISEConfig

config = ARISEConfig(
    sandbox_backend="docker",    # "subprocess" (default) or "docker"
    sandbox_timeout=30,          # seconds before the sandbox kills the process
)
```

### subprocess (default)

Runs generated code in a separate Python process. Provides process isolation and timeout enforcement, but **no network or filesystem isolation**. Suitable for development and trusted environments.

### Docker (recommended for production)

Runs generated code in an isolated container:
- No network access
- Read-only filesystem
- Resource limits (CPU, memory)
- Hard process timeout

```bash
pip install arise-ai[docker]
```

```python
config = ARISEConfig(
    sandbox_backend="docker",
    sandbox_timeout=30,
)
```

:::tip[Use Docker in production]
The subprocess backend is convenient but does not prevent a synthesized skill from reading environment variables, writing to disk, or making network calls. Use Docker for any workload where the agent processes untrusted input.
:::
---

## Import Restrictions

Use `allowed_imports` to whitelist which modules synthesized skills can use. When set, ARISE performs both static and dynamic analysis:

- Static `import` / `from ... import` statements
- Dynamic `__import__("module")` calls
- `importlib.import_module("module")` calls
- `exec()` / `eval()` containing import statements

```python
config = ARISEConfig(
    allowed_imports=[
        "json", "re", "hashlib", "csv", "math",
        "base64", "datetime", "collections", "itertools",
    ],
)
```

Skills with disallowed imports are rejected and refined. If `allowed_imports` is `None` (the default), no restriction is applied.

:::warning[Always set `allowed_imports` in production]
Start with standard library modules only. Add third-party packages only as needed and after reviewing the risk. Never include `subprocess`, `socket`, `os.system`, or `requests` unless your use case specifically requires it.
:::
---

## Adversarial Testing

After the sandbox test suite passes, ARISE runs a second LLM call specifically designed to find weaknesses. The adversarial model generates inputs that target:

- Edge cases (empty inputs, extreme values, boundary conditions)
- Type boundary violations (passing strings where ints are expected)
- Security-probing inputs (path traversal attempts, injection strings)
- Unexpected data shapes

If adversarial tests find a problem, ARISE refines the skill and re-tests before promotion. Skills that still fail after `max_refinement_attempts` are kept in `TESTING` status rather than promoted.

---

## Version Control & Rollback

Every skill promotion is checkpointed with an integer version number. You can inspect and roll back at any time:

```bash
# Check current library state
arise status ./arise_skills

# List skills with their origins
arise skills ./arise_skills

# View a specific skill's implementation and tests
arise inspect ./arise_skills <skill_id>

# Roll back to a previous version
arise rollback ./arise_skills 3
```

From Python:

```python
arise.rollback(version=3)
```

Rolling back restores the exact set of active skills from that checkpoint. The rolled-back versions are not deleted — you can roll forward again.

---

## Skill Registry Security

The `SkillRegistry` distributes executable Python code via S3. Treat registry entries with the same care as any code distribution system.

**When pulling from a registry:**

```python
from arise import SkillRegistry
from arise.skills.sandbox import Sandbox

registry = SkillRegistry(bucket="my-registry")
sandbox = Sandbox(backend="docker")

# Always validate pulled skills
skill = registry.pull("parse_csv", validate=True, sandbox=sandbox)

# Pin a specific version — don't always pull latest
skill = registry.pull("parse_csv", version=3)
```

**IAM permissions:**

- Agent processes should have **read-only** S3 access (`s3:GetObject`, `s3:ListBucket`)
- Only the worker process (or a dedicated publisher role) should have write access (`s3:PutObject`)
- Enable S3 versioning on the registry bucket for rollback capability

---

## Rate Limiting

Cap LLM spend for evolution with `max_evolutions_per_hour`:

```python
config = ARISEConfig(
    max_evolutions_per_hour=3,   # default
    max_library_size=50,         # cap total active skills
)
```

When the rate limit is hit, ARISE skips the evolution cycle and logs a message. Failures continue to accumulate and evolution resumes in the next hour window.

---

## Production Recommendations

1. **Set `allowed_imports`** — start with standard library only, add packages explicitly.
2. **Use Docker sandbox** for any workload that processes untrusted input.
3. **Review promoted skills** before deploying — use `arise inspect <id>` to read the implementation.
4. **Restrict IAM permissions** — read-only S3 for agent processes; write access only for the worker.
5. **Monitor evolution costs** — set `max_evolutions_per_hour` and watch cost_tracker output.
6. **Set `max_library_size`** — prevents unbounded skill accumulation.
7. **Enable OTel tracing** with `arise-ai[otel]` to observe evolution steps in your existing observability stack.
