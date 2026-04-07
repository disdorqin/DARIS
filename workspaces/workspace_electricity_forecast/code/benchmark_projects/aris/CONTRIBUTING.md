# Contributing to ARISE

Thank you for your interest in contributing to ARISE (self-evolving agent framework).

## Running Tests

Install the project with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run the full test suite (excluding tests that require AWS credentials):

```bash
python -m pytest tests/ -v \
  --ignore=tests/test_distributed_e2e.py \
  --ignore=tests/test_distributed_llm.py
```

To run a specific test file:

```bash
python -m pytest tests/test_library.py -v
```

The two excluded test files (`test_distributed_e2e.py`, `test_distributed_llm.py`) require live AWS credentials and are not run in CI.

## Code Style

- Follow standard Python conventions (PEP 8).
- Use type hints for function signatures.
- Keep public APIs documented with docstrings.
- Run tests before submitting a PR — CI will also run them automatically.

## Pull Request Process

1. Fork the repository and create a branch from `main`.
2. Make your changes and add tests where appropriate.
3. Ensure all tests pass locally.
4. Open a pull request against `main` with a clear description of the change.
5. A maintainer will review and merge.

## Reporting Issues

Please use [GitHub Issues](https://github.com/abekek/arise/issues) to report bugs or request features. Include a minimal reproducible example when reporting bugs.
