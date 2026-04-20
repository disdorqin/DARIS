---
title: Skill Registry
---


The skill registry lets you share evolved tools across projects — like a package index for agent skills. Skills are stored in S3 and can be published, searched, and pulled by any project with access to the bucket.

## Overview

```python
from arise import SkillRegistry
from arise.skills.sandbox import Sandbox

registry = SkillRegistry(
    bucket="my-registry",
    prefix="arise-registry",   # S3 key prefix (default)
    region="us-east-1",
)
sandbox = Sandbox(backend="subprocess")
```

## Publishing Skills

Publish a `Skill` object (typically from your active library) to the registry:

```python
# Get a skill from your active library
for skill in arise.skills:
    if skill.name == "parse_csv":
        registry.publish(skill, tags=["csv", "parsing", "data"])
        break
```

Publishing increments the version automatically. The registry stores:

- Implementation source code
- Test suite
- Tags
- Download count
- Average success rate (updated on pull)

## Searching

```python
results = registry.search(
    query="csv parsing",
    tags=["data"],       # optional tag filter
    sort_by="success_rate",  # or "relevance"
    limit=10,
)

for entry in results:
    print(f"{entry.name} v{entry.version} — {entry.avg_success_rate:.0%} success — {entry.downloads} downloads")
    print(f"  {entry.description}")
    print(f"  tags: {', '.join(entry.tags)}")
```

Search matches on name, description, and tags. Results are sorted by `avg_success_rate` by default.

From the CLI:

```bash
arise registry search "csv parsing" --tags data json
```

## Pulling Skills

Pull a skill by name (latest version by default):

```python
skill = registry.pull("parse_csv")
```

Pull a specific version:

```python
skill = registry.pull("parse_csv", version=3)
```

Pull with sandbox validation (recommended):

```python
skill = registry.pull(
    "parse_csv",
    validate=True,
    sandbox=sandbox,
)
```

If validation fails, `SkillValidationError` is raised. The skill is not added to your library.

After pulling, add the skill to your library:

```python
arise.skill_library.add(skill)
arise.skill_library.promote(skill.id)
```

## Automatic Registry Check Before Synthesis

Set `registry_check_before_synthesis=True` in `ARISEConfig` (the default) and ARISE will check the registry before calling the LLM during evolution. If a skill matching the detected gap already exists in the registry with a good success rate, it pulls and promotes that skill instead of synthesizing a new one.

```python
config = ARISEConfig(
    registry_bucket="my-registry",
    registry_prefix="arise-registry",
    registry_check_before_synthesis=True,  # default
)
```

## File-Based Import/Export

Transfer skills as JSON files without requiring an S3 registry:

```bash
# Export all active skills to a JSON file
arise registry export ./arise_skills -o skills.json

# Import skills from JSON (with sandbox validation)
arise registry import skills.json ./arise_skills
```

From Python:

```python
from arise.registry.client import export_skills, import_skills
from arise.skills.library import SkillLibrary
from arise.skills.sandbox import Sandbox

lib = SkillLibrary("./arise_skills")
sandbox = Sandbox()

# Export
count = export_skills(lib, "skills.json")
print(f"Exported {count} skills")

# Import (sandbox validation skipped if sandbox=None)
imported = import_skills("skills.json", lib, sandbox=sandbox)
print(f"Imported {len(imported)} skills")
```

The JSON format is a list of records:

```json
[
  {
    "name": "parse_csv",
    "description": "Parse a CSV string into a list of dicts",
    "implementation": "def parse_csv(text: str) -> list:\n    ...",
    "test_suite": "def test_parse_csv():\n    ...",
    "tags": ["csv", "parsing"],
    "version": 1
  }
]
```

## Tags

Tags are free-form strings attached at publish time. Use them to organize skills by domain, data format, or integration:

```python
registry.publish(skill, tags=["json", "api", "pagination"])
registry.publish(skill, tags=["csv", "data-engineering"])
registry.publish(skill, tags=["sre", "log-parsing", "acmecorp"])
```

## Security

Skills in the registry are executable Python code. Before using a pulled skill in production:

1. **Always validate with the sandbox** — pass `validate=True` and a `sandbox` instance.
2. **Review the implementation** — use `arise inspect <id>` after adding to your library.
3. **Pin versions** — pull a specific `version=` rather than always pulling latest.
4. **Restrict IAM** — only your worker should have `s3:PutObject` on the registry bucket.

See [Safety & Validation](/guide/safety/) for full security recommendations.
