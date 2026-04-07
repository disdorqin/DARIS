"""Email Action Items agent on AgentCore with ARISE distributed mode."""

import logging
import os

from strands import Agent
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
import uvicorn

from arise import ARISEConfig, create_distributed_arise, ARISE
from arise.adapters.strands import strands_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arise-email")

REGION = os.getenv("AWS_REGION", "us-west-2")
PORT = 9000
runtime_url = os.environ.get("AGENTCORE_RUNTIME_URL", f"http://127.0.0.1:{PORT}/")

ICLOUD_EMAIL = os.environ.get("ICLOUD_EMAIL", "")
ICLOUD_PASSWORD = os.environ.get("ICLOUD_APP_PASSWORD", "")

# ---------------------------------------------------------------------------
# ARISE config
# ---------------------------------------------------------------------------

config = ARISEConfig(
    model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
    s3_bucket=os.environ.get("ARISE_SKILL_BUCKET", ""),
    sqs_queue_url=os.environ.get("ARISE_QUEUE_URL", ""),
    aws_region=REGION,
    skill_cache_ttl_seconds=30,
    max_evolutions_per_hour=5,
    verbose=True,
    allowed_imports=[
        "imaplib", "ssl",
        "email", "email.header", "email.utils", "email.message",
        "email.policy", "email.parser",
        "json", "re", "datetime", "html", "base64",
        "collections", "os",
    ],
)

# ---------------------------------------------------------------------------
# Strands Agent — the actual email agent with ARISE tools
# ---------------------------------------------------------------------------

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name=REGION,
)

strands_agent = Agent(
    name="arise_email",
    description="Email assistant that reads iCloud emails and extracts action items.",
    model=bedrock_model,
    system_prompt=(
        "You are a READ-ONLY email assistant. Read emails and extract action items.\n\n"
        f"iCloud credentials: email={ICLOUD_EMAIL}, password={ICLOUD_PASSWORD}\n"
        "IMAP server: imap.mail.me.com, port 993 (SSL)\n\n"
        "CRITICAL: NEVER send, reply, forward, or delete emails. READ-ONLY.\n\n"
        "When using read_emails_imap, pass: server='imap.mail.me.com', port=993, "
        f"email_addr='{ICLOUD_EMAIL}', password='{ICLOUD_PASSWORD}'\n\n"
        "Return a clear summary with action items."
    ),
)

# ---------------------------------------------------------------------------
# ARISE — inject evolved tools into the strands agent
# ---------------------------------------------------------------------------

agent_fn = strands_adapter(strands_agent)


def reward_fn(trajectory):
    outcome = trajectory.outcome.lower()
    if trajectory.metadata.get("success") is not None:
        return 1.0 if trajectory.metadata["success"] else 0.0
    if len(outcome) < 50:
        return 0.0
    fail_signals = ["i don't have", "i cannot", "no tool", "not available", "unable to"]
    if any(s in outcome for s in fail_signals):
        return 0.0
    action_signals = ["action item", "todo", "follow up", "deadline",
                      "respond", "review", "schedule", "send", "complete",
                      "submit", "prepare", "meeting", "reply"]
    if any(s in outcome for s in action_signals):
        return 1.0
    return 0.3


if config.s3_bucket and config.sqs_queue_url:
    logger.info(f"ARISE distributed: S3={config.s3_bucket}")
    arise = create_distributed_arise(agent_fn=agent_fn, reward_fn=reward_fn, config=config)
else:
    logger.info("ARISE local mode")
    arise = ARISE(agent_fn=agent_fn, reward_fn=reward_fn, config=config)

# ---------------------------------------------------------------------------
# Load ARISE skills into the Strands agent as @tool functions
# ---------------------------------------------------------------------------

from strands import tool as strands_tool

for spec in arise._skill_store.get_tool_specs():
    # Wrap the ARISE tool as a Strands tool
    wrapped = strands_tool(spec.fn, name=spec.name, description=spec.description)
    strands_agent.tool_registry.register_tool(wrapped)
    logger.info(f"Registered ARISE tool: {spec.name}")

# ---------------------------------------------------------------------------
# A2A Server — uses the Strands agent directly (no proxy)
# ---------------------------------------------------------------------------

a2a_server = A2AServer(
    agent=strands_agent,
    http_url=runtime_url,
    serve_at_root=True,
    enable_a2a_compliant_streaming=True,
)

app = a2a_server.to_fastapi_app()


@app.get("/ping")
def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
