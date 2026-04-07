---
title: Installation
---


## Requirements

- Python 3.11+
- An LLM API key (OpenAI, Anthropic, or any [LiteLLM](https://github.com/BerriAI/litellm)-supported provider)

## Install

```bash
pip install arise-ai
```

The core package depends only on `pydantic`. Everything else is optional.

## Optional Extras

Install extras based on your use case:

```bash
pip install arise-ai[aws]        # boto3 — for distributed mode (S3 + SQS)
pip install arise-ai[litellm]    # litellm — multi-provider LLM routing
pip install arise-ai[docker]     # docker SDK — Docker sandbox backend
pip install arise-ai[dashboard]  # rich + fastapi — TUI and web dashboard
pip install arise-ai[otel]       # opentelemetry — evolution step tracing
pip install arise-ai[all]        # everything
```

| Extra | Adds | Use when |
|-------|------|----------|
| `[aws]` | boto3 | Running distributed mode with S3/SQS, or using SkillRegistry |
| `[litellm]` | litellm | Using Anthropic, Google, Ollama, or any non-OpenAI model |
| `[docker]` | docker | Using `sandbox_backend="docker"` in production |
| `[dashboard]` | rich, fastapi | Running `arise dashboard` or `arise dashboard --web` |
| `[otel]` | opentelemetry-sdk | Sending evolution spans to your observability stack |
| `[all]` | all of the above | Development or full-featured deployments |

## Framework Dependencies

ARISE integrates with agent frameworks but does not depend on them. Install the framework separately:

```bash
pip install strands-agents          # Strands Agents (Bedrock)
pip install langgraph langchain-core  # LangGraph
pip install crewai                  # CrewAI
```

See [Framework Adapters](/guide/adapters/) for integration details.

## Verify

```python
import arise
print(arise.__version__)  # 0.1.4
```

## Environment Variables

Set your LLM provider API key before running:

```bash
export OPENAI_API_KEY=sk-...          # OpenAI
export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic (via litellm)
export AWS_DEFAULT_REGION=us-east-1   # AWS (distributed mode)
```

:::tip[Using non-OpenAI models]
Install `arise-ai[litellm]` and prefix your model string with the provider:

```python
arise = ARISE(model="anthropic/claude-3-haiku-20240307", ...)
arise = ARISE(model="gemini/gemini-1.5-flash", ...)
arise = ARISE(model="ollama/llama3", ...)
```
:::
