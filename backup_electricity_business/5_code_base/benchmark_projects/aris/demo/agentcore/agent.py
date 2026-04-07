"""Self-evolving DevOps agent served as an A2A server on AgentCore.

The A2A server handles protocol/discovery. Each incoming message is routed
through arise.run() so that:
  - Active skills from S3 are injected as tools
  - Trajectories are reported to SQS after each run
  - The evolution loop is active
"""

import logging
import os
from functools import lru_cache

from strands import Agent, tool
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from fastapi import FastAPI
import uvicorn

from arise import ARISEConfig, create_distributed_arise, ARISE
from arise.adapters.strands import strands_adapter
from arise.rewards.builtin import task_success

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arise-devops")

REGION = os.getenv("AWS_REGION", "us-west-2")
PORT = 9000
runtime_url = os.environ.get("AGENTCORE_RUNTIME_URL", f"http://127.0.0.1:{PORT}/")

# ---------------------------------------------------------------------------
# ARISE config
# ---------------------------------------------------------------------------

config = ARISEConfig(
    model="gpt-4o-mini",
    s3_bucket=os.environ.get("ARISE_SKILL_BUCKET", ""),
    sqs_queue_url=os.environ.get("ARISE_QUEUE_URL", ""),
    aws_region=REGION,
    max_evolutions_per_hour=5,
    verbose=True,
    allowed_imports=[
        "json", "csv", "re", "hashlib", "base64", "datetime",
        "math", "collections", "itertools", "functools",
        "pathlib", "os", "tempfile", "urllib",
    ],
)

# ---------------------------------------------------------------------------
# Strands Agent — used by both A2A server and ARISE
# ---------------------------------------------------------------------------

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name=REGION,
)

strands_agent = Agent(
    name="arise_devops",
    description="Self-evolving DevOps assistant that learns new tools over time.",
    model=bedrock_model,
    system_prompt=(
        "You are a DevOps assistant. Use available tools to complete tasks. "
        "If no tool exists for a task, respond with: "
        "TOOL_MISSING: <describe what capability you need>. "
        "Always produce clear, actionable output."
    ),
    callback_handler=None,
)

# ---------------------------------------------------------------------------
# ARISE — wraps the agent for self-evolution
# ---------------------------------------------------------------------------

agent_fn = strands_adapter(strands_agent)

if config.s3_bucket and config.sqs_queue_url:
    logger.info(f"ARISE distributed mode: S3={config.s3_bucket}, SQS={config.sqs_queue_url}")
    arise = create_distributed_arise(
        agent_fn=agent_fn,
        reward_fn=task_success,
        config=config,
    )
else:
    logger.info("ARISE local mode (no S3/SQS configured)")
    arise = ARISE(
        agent_fn=agent_fn,
        reward_fn=task_success,
        config=config,
    )

# ---------------------------------------------------------------------------
# Create a wrapper agent that routes through arise.run()
# This is what A2AServer will use — every message goes through the ARISE loop
# ---------------------------------------------------------------------------


@tool
def arise_proxy(task: str) -> str:
    """Route the user's task through the ARISE self-evolution loop."""
    return arise.run(task)


# The proxy agent uses arise_proxy as its only tool, so every request
# goes through arise.run() which loads S3 skills and reports trajectories
proxy_agent = Agent(
    name="arise_devops",
    description="Self-evolving DevOps assistant that learns new tools over time.",
    model=bedrock_model,
    system_prompt=(
        "You are a proxy. For EVERY user message, call the arise_proxy tool with "
        "the user's full message as the 'task' parameter. Return the tool's output "
        "verbatim. Do NOT answer directly — always use the tool."
    ),
    tools=[arise_proxy],
    callback_handler=None,
)

# ---------------------------------------------------------------------------
# A2A Server — uses the proxy agent so all requests flow through ARISE
# ---------------------------------------------------------------------------

a2a_server = A2AServer(
    agent=proxy_agent,
    http_url=runtime_url,
    serve_at_root=True,
)

app = FastAPI()


@app.get("/ping")
def ping():
    return {"status": "healthy"}


app.mount("/", a2a_server.to_fastapi_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
