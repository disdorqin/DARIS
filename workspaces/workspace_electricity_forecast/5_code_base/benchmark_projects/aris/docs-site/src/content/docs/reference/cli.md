---
title: CLI Reference
---


The `arise` CLI manages your skill library, trajectories, and infrastructure. All commands take an optional path argument pointing to your skill library directory (default: `./arise_skills`).

```bash
arise --help
```

---

## `arise status`

Show statistics for a skill library.

```bash
arise status [path]
arise status ./arise_skills
```

**Output:**

```
ARISE Skill Library — ./arise_skills
  Version:      8
  Active:       4
  Testing:      1
  Deprecated:   2
  Total:        7
  Avg Success:  84.7%

  Top Performers:
    compute_sha256: 100.0% (23 invocations)
    parse_json_response: 91.3% (46 invocations)
```

---

## `arise skills`

List all active skills with performance metrics.

```bash
arise skills [path]
arise skills ./arise_skills
```

**Output:**

```
Name                      Success    Invocations  Origin       ID
---------------------------------------------------------------------------
compute_sha256            100.0%     23           synthesized  a1b2c3d4
parse_json_response       91.3%      46           synthesized  e5f6g7h8
fetch_all_paginated       78.9%      19           synthesized  i9j0k1l2
read_file                 100.0%     52           manual       m3n4o5p6
```

---

## `arise inspect`

View the full implementation and test suite for a specific skill.

```bash
arise inspect <path> <skill_id>
arise inspect ./arise_skills a1b2c3d4
```

**Output:**

```
Name:        compute_sha256
ID:          a1b2c3d4
Status:      active
Origin:      synthesized
Version:     2
Success:     100.0% (23 invocations)
Description: Compute the SHA-256 hash of a file

--- Implementation ---
import hashlib

def compute_sha256(path: str) -> str:
    """Compute the SHA-256 hash of a file."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

--- Test Suite ---
def test_compute_sha256():
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"hello")
        name = f.name
    result = compute_sha256(name)
    assert len(result) == 64
    os.unlink(name)
```

---

## `arise rollback`

Roll back the skill library to a previous version checkpoint.

```bash
arise rollback <path> <version>
arise rollback ./arise_skills 3
```

Every skill promotion creates a new version. Rolling back restores the exact set of active skills from that checkpoint without deleting any data — you can roll forward again.

---

## `arise export`

Export all active skills as individual `.py` files.

```bash
arise export <path> <output_dir>
arise export ./arise_skills ./exported_skills
```

**Output:**

```
Exported: ./exported_skills/compute_sha256.py
Exported: ./exported_skills/parse_json_response.py
Exported: ./exported_skills/read_file.py

3 skills exported.
```

Each file contains the skill implementation with metadata in a comment header.

---

## `arise evolve`

Inspect or trigger evolution from the command line.

```bash
# Dry-run: detect gaps and show what would be synthesized (1 LLM call)
arise evolve --dry-run

# With custom paths
arise evolve \
  --skills-path ./arise_skills \
  --trajectories-path ./arise_trajectories \
  --dry-run
```

**Dry-run output:**

```
Should evolve: True
Recent failures: 6

[DRY RUN] Running gap detection (1 LLM call)...

Detected 2 capability gaps:
  - decode_base64_metrics: Decode proprietary base64-encoded metrics payload
    Signature: def decode_base64_metrics(payload: str) -> dict:
    Evidence: Agent said: I need to decode this base64 payload but I have no tool for it
    Evidence: Error: 'str' object has no attribute 'decode'

  - fetch_paginated_api: Fetch all pages from a paginated REST API
    Signature: def fetch_paginated_api(url: str, auth_token: str) -> list:
    Evidence: TOOL_MISSING: http client that handles auth headers

Run without --dry-run to synthesize these tools.
```

---

## `arise history`

Show recent trajectory history.

```bash
arise history [path] [-n N]
arise history ./arise_trajectories -n 20
```

**Output:**

```
Task                                               Reward   Steps   Time
-------------------------------------------------------------------------------------
Compute the SHA-256 hash of hello.txt              1.00     2       2026-03-21 10:15
Fetch all users from /api/users with pagination    0.00     1       2026-03-21 10:14
Parse the JSON response from the metrics API       0.00     1       2026-03-21 10:13
```

---

## `arise dashboard`

Launch the skill library dashboard.

```bash
# Terminal TUI (requires arise-ai[dashboard])
arise dashboard [path]
arise dashboard ./arise_skills
arise dashboard ./arise_skills --trajectories-path ./arise_trajectories

# Web UI on localhost:8501
arise dashboard ./arise_skills --web
arise dashboard ./arise_skills --web --port 9000
```

See [Dashboard](/guide/dashboard/) for details on what each view shows.

---

## `arise setup-distributed`

Provision or tear down AWS infrastructure for distributed mode.

```bash
# Provision S3 bucket + SQS queue + DLQ, save config to .arise.json
arise setup-distributed --region us-west-2

# With explicit names (auto-generated by default)
arise setup-distributed \
  --region us-west-2 \
  --bucket my-arise-skills \
  --queue my-arise-trajectories \
  --profile my-aws-profile

# Destroy resources from .arise.json
arise setup-distributed --destroy
```

Requires `arise-ai[aws]`.

**Output:**

```
Created S3 bucket: arn:aws:s3:::arise-skills-a1b2c3d4e5f6
Created SQS DLQ:   arn:aws:sqs:us-west-2:123456789:arise-trajectories-abc-dlq
Created SQS queue: arn:aws:sqs:us-west-2:123456789:arise-trajectories-abc
Config saved to .arise.json
```

---

## `arise registry`

Manage skill import/export and search.

### `arise registry export`

Export active skills to a JSON file:

```bash
arise registry export <path> [-o output.json]
arise registry export ./arise_skills -o skills.json
```

### `arise registry import`

Import skills from a JSON file (with sandbox validation):

```bash
arise registry import <input.json> <path>
arise registry import skills.json ./arise_skills
```

Skills that fail sandbox validation are skipped with a warning.

### `arise registry search`

Search skills in the local library by keyword:

```bash
arise registry search <query> [--tags tag1 tag2]
arise registry search "csv parsing" --tags data json
```

**Output:**

```
Name                      Success    Invocations  ID
------------------------------------------------------------
parse_csv                 91.3%      46           a1b2c3d4
read_csv_columns          87.5%      24           e5f6g7h8
```

:::note[registry search vs SkillRegistry.search()]
`arise registry search` searches your local skill library by name. To search an S3-backed registry, use `SkillRegistry.search()` from Python — see [Skill Registry](/guide/registry/).
:::