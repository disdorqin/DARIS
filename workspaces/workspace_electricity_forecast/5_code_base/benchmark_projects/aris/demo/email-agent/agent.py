"""
Email Action Items Agent — ARISE Demo

This agent starts with ZERO tools. When asked to read emails and extract
action items, it fails. ARISE detects the gap and evolves email-reading
tools automatically.

Usage:
    python agent.py              # run the evolution loop
    python agent.py --dashboard  # run with dashboard in background
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Add arise to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Ensure AWS profile is set for litellm bedrock calls
os.environ.setdefault("AWS_PROFILE", "abekek")

from arise import ARISE, ARISEConfig
from arise.rewards import task_success
import litellm


def agent_fn(task: str, tools: list) -> str:
    """Claude agent via Bedrock. Uses tool calling."""
    tool_map = {t.name: t.fn for t in tools}

    # Build tool definitions for Claude
    claude_tools = []
    for t in tools:
        claude_tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        })

    messages = [{"role": "user", "content": task}]

    system = (
        "You are a READ-ONLY email assistant. Your job is to read the user's "
        "emails and extract action items. Use the tools available to you. "
        "The user's iCloud email credentials are available as environment "
        "variables: ICLOUD_EMAIL and ICLOUD_APP_PASSWORD. "
        "The IMAP server is imap.mail.me.com on port 993 (SSL).\n\n"
        "CRITICAL SAFETY RULES:\n"
        "- You must NEVER send, reply to, forward, or delete emails\n"
        "- You must NEVER modify any email or mailbox state\n"
        "- You are READ-ONLY. Only fetch and read emails.\n"
        "- Do NOT use SMTP or any sending protocol\n\n"
        "If you don't have the right tools to complete the task, "
        "say exactly what tool you need and why."
    )

    for attempt in range(5):  # max 5 tool-call rounds
        response = litellm.completion(
            model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
            messages=messages,
            tools=claude_tools if claude_tools else None,
            system=system,
            max_tokens=4096,
        )

        msg = response.choices[0].message

        # No tool calls — return final answer
        if not msg.tool_calls:
            return msg.content or ""

        # Execute tool calls
        messages.append(msg)
        for tc in msg.tool_calls:
            fn = tool_map.get(tc.function.name)
            if fn is None:
                result = f"Error: tool '{tc.function.name}' not found"
            else:
                try:
                    args = json.loads(tc.function.arguments)
                    result = str(fn(**args))
                except Exception as e:
                    result = f"Error: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return msg.content or ""


def reward_fn(trajectory):
    """Reward: did the agent actually return action items?"""
    outcome = trajectory.outcome.lower()

    # Check explicit signals
    if trajectory.metadata.get("success") is not None:
        return 1.0 if trajectory.metadata["success"] else 0.0

    # Must have actual content
    if len(outcome) < 50:
        return 0.0

    # Should contain action-item-like content
    action_signals = ["action item", "todo", "follow up", "deadline",
                      "respond to", "review", "schedule", "send", "complete",
                      "submit", "prepare", "meeting", "reply"]
    has_actions = any(s in outcome for s in action_signals)

    # Should not be an error or refusal
    fail_signals = ["i don't have", "i cannot", "no tool", "not available",
                    "i need a tool", "unable to"]
    is_failure = any(s in outcome for s in fail_signals)

    if is_failure:
        return 0.0
    if has_actions:
        return 1.0
    return 0.3  # some output but unclear if action items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", action="store_true", help="Launch TUI dashboard")
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes")
    args = parser.parse_args()

    config = ARISEConfig(
        model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
        failure_threshold=3,
        max_evolutions_per_hour=5,
        sandbox_timeout=60,
        verbose=True,
        allowed_imports=[
            # IMAP read-only access
            "imaplib", "ssl",
            # Email parsing (NOT sending — no smtplib, no email.mime)
            "email", "email.header", "email.utils", "email.message",
            "email.policy", "email.parser",
            # Data processing
            "json", "re", "datetime", "html", "base64",
            "collections", "os",
            # Explicitly blocked (for clarity): smtplib, subprocess,
            # socket, requests, urllib, email.mime, shutil, pathlib
        ],
        skill_store_path="./arise_skills",
        trajectory_store_path="./arise_trajectories",
    )

    arise = ARISE(
        agent_fn=agent_fn,
        reward_fn=reward_fn,
        config=config,
    )

    # The tasks — what we want the agent to do
    tasks = [
        "Read my latest 5 emails and list any action items I need to take.",
        "Check my inbox for emails from today and summarize what needs my attention.",
        "Look through my recent emails and extract any deadlines or meetings mentioned.",
    ]

    print("\n=== ARISE Email Agent Demo ===")
    print(f"Starting with {len(arise.skills)} tools")
    print(f"Running {args.episodes} episodes\n")

    if args.dashboard:
        print("Dashboard: run 'arise dashboard ./arise_skills' in another terminal\n")

    arise.train(tasks, num_episodes=args.episodes)

    print(f"\n=== Done ===")
    print(f"Final tools: {len(arise.skills)}")
    for skill in arise.skills:
        print(f"  - {skill.name} (success: {skill.success_rate:.0%}, used {skill.invocation_count}x)")
    print(f"\nStats: {json.dumps(arise.stats, indent=2)}")


if __name__ == "__main__":
    main()
