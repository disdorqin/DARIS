ADVERSARIAL_TEST_PROMPT = """\
You are a QA engineer trying to break this Python function. Your goal is to find bugs.

FUNCTION NAME: {name}
DESCRIPTION: {description}

IMPLEMENTATION:
```python
{implementation}
```

THE FOLLOWING TESTS ALREADY PASS:
```python
{existing_tests}
```

Generate 5 test cases that are LIKELY TO EXPOSE BUGS. Focus on:
- Edge cases: empty inputs, None, huge values, single-element inputs
- Type boundary cases: wrong types, unicode strings, negative numbers, floats where ints expected
- Off-by-one errors, division by zero, empty collections
- Property checks (if it claims to return a list, assert isinstance(result, list))
- Security: path traversal in file paths, injection in string processing, resource exhaustion
- Idempotency: calling the function twice with the same input should give the same result

Each test must be a function named test_adversarial_*. Use assert statements.
Tests must be self-contained — use tempfile for file I/O, don't hardcode paths.
Return ONLY Python test code, no markdown fences.
"""
