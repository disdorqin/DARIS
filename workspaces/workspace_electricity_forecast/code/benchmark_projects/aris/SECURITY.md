# Security

ARISE generates and executes Python code at runtime. This document describes the threat model and built-in mitigations.

## Threat Model

| Threat | Description | Mitigation |
|--------|-------------|------------|
| Malicious generated code | LLM synthesizes code that reads env vars, makes network calls, or accesses the filesystem | Sandbox isolation (subprocess/Docker), `allowed_imports` whitelist |
| Import restriction bypass | Generated code uses `__import__()`, `importlib`, or `exec("import ...")` to circumvent import checks | AST-based static analysis + dynamic import pattern detection |
| Prompt injection via trajectories | Attacker crafts task inputs that manipulate the synthesis prompt | Trajectory data is truncated and sanitized before inclusion in prompts |
| Poisoned skill promotion | A skill passes tests but contains hidden malicious behavior | Adversarial validation, multi-stage testing pipeline, manual review before production |
| S3 manifest tampering | Attacker modifies the shared skill manifest | Use IAM policies to restrict write access to worker process only |
| SQS message injection | Attacker sends crafted messages to the trajectory queue | Use IAM policies + VPC endpoints; messages are validated before processing |

## Sandbox

Generated code runs in an isolated environment:

- **subprocess** (default): Separate Python process with timeout. No network or filesystem isolation.
- **Docker** (recommended for production): Isolated container with no network access, read-only filesystem, and resource limits.

Configure the sandbox backend:

```python
config = ARISEConfig(
    sandbox_backend="docker",  # or "subprocess"
    sandbox_timeout=30,
)
```

## Import Restrictions

Use `allowed_imports` to whitelist which modules generated skills can use:

```python
config = ARISEConfig(
    allowed_imports=["hashlib", "json", "csv", "re", "math", "base64", "datetime"],
)
```

When set, ARISE checks generated code for:
- Static `import` / `from ... import` statements
- Dynamic `__import__("module")` calls
- `importlib.import_module("module")` calls
- `exec()` / `eval()` containing import statements

Skills with disallowed imports are rejected and refined.

**If `allowed_imports` is `None` (default), no restriction is applied.** Set this explicitly in production.

## Recommendations

1. **Always set `allowed_imports`** in production. Start with standard library modules only.
2. **Use Docker sandbox** for untrusted workloads.
3. **Review promoted skills** before deploying to production. Use `arise skills` and `arise inspect` CLI commands.
4. **Restrict S3/SQS IAM permissions**: agent process should have read-only S3 access; only the worker should write.
5. **Monitor evolution costs**: set `max_evolutions_per_hour` to limit LLM spend.
6. **Set `max_library_size`** to prevent unbounded skill accumulation.

## Skill Registry Security

The `SkillRegistry` stores and distributes executable Python code via S3. Treat it with the same care as any code distribution system.

**S3 bucket permissions:**

- The registry bucket should have a strict bucket policy: only your worker process (or a dedicated publisher role) should have `s3:PutObject`. All other principals — including agent processes — should have read-only access (`s3:GetObject`, `s3:ListBucket`).
- Enable S3 versioning on the registry bucket so you can roll back a malicious publish.
- Consider enabling S3 Object Lock (Compliance mode) for entries that have been widely deployed.

**Validating pulled skills:**

Skills pulled from the registry are third-party code. Before using a pulled skill in production:

1. **Run in sandbox** — always pass a pulled skill through `sandbox.test_skill(skill)` before promoting it, even if the registry entry reports a high `avg_success_rate`. The registry trust score reflects historical usage, not a security audit.
2. **Adversarial validation** — run `forge.adversarial_test(skill)` against pulled skills, just as you would for synthesized ones.
3. **Review before production** — use `arise inspect <id>` to read the implementation. Do not rely solely on automated checks for sensitive workloads.
4. **Pin versions** — pull a specific version (`registry.pull(name, version=3)`) rather than always pulling latest, to prevent supply-chain updates from silently changing behavior.

**Org-private registries:**

For teams that want sharing within an org but not with the public, deploy a private registry bucket with an IAM resource-based policy that restricts access to your AWS organization (`aws:PrincipalOrgID` condition). Do not expose the bucket publicly.

## Reporting Vulnerabilities

If you find a security issue, please open a GitHub issue or email the maintainer directly. Do not include exploit code in public issues.
