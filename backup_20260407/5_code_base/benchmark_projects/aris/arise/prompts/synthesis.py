SYNTHESIS_PROMPT = """\
You are creating a Python tool for an AI agent.

REQUIRED CAPABILITY:
{description}

FUNCTION SIGNATURE (suggested):
{signature}

EXISTING TOOLS (for reference — you can call these):
{existing_tools}

EXAMPLES OF TASKS WHERE THIS TOOL WAS NEEDED:
{evidence}

REQUIREMENTS:
1. Write a single Python function
2. Include type hints for all parameters and return value
3. Include a docstring explaining what it does, parameters, and return value
4. Handle errors gracefully — return error info, don't crash
5. Use only standard library + common packages (pandas, numpy, scipy, sklearn)
6. The function must be FULLY SELF-CONTAINED: all imports must be INSIDE the function body, not at module level. This is critical because the function will be loaded via exec().
7. Keep it focused — one tool, one job

CRITICAL — self-contained imports example:
```python
def compute_sha256(file_path: str) -> str:
    \"\"\"Compute the SHA-256 hash of a file.\"\"\"
    import hashlib  # <-- INSIDE the function, not at the top
    import os
    ...
```

TEST REQUIREMENTS:
- Each test function must be named test_<descriptive_name>
- Tests can import modules at the top level (unlike the implementation)
- Use tempfile for any file I/O in tests — never hardcode paths
- Tests must be self-contained and clean up after themselves
- NEVER hardcode expected values you can't compute yourself (like hashes, encoded data, etc.). Instead, compute the expected value in the test using the same standard library, or test structural properties (e.g., "result is 64 hex chars" for SHA-256)

Return ONLY a JSON object with these fields:
{{
    "name": "function_name",
    "description": "One-line description for the agent to understand when to use this",
    "implementation": "full Python function source code",
    "test_suite": "test code with functions named test_* that use assert statements"
}}
"""
