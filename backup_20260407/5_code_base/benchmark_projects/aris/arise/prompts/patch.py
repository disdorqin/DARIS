PATCH_PROMPT = """\
An existing Python tool is failing on specific inputs. Apply a minimal, targeted fix.

FUNCTION NAME: {name}
DESCRIPTION: {description}

CURRENT IMPLEMENTATION (working for most inputs):
```python
{implementation}
```

SPECIFIC FAILURES:
{failures}

Apply the MINIMUM change needed to fix these specific failures WITHOUT breaking existing behavior.
Do NOT rewrite the function. Only modify the specific code paths that cause these failures.

CRITICAL RULES:
- All imports must be INSIDE the function body, not at module level.
- NEVER hardcode expected values you can't compute.
- Keep the same function name and signature.

Return ONLY a JSON object:
{{
    "implementation": "patched Python function source code",
    "patch_description": "one-line summary of what was changed"
}}
"""
