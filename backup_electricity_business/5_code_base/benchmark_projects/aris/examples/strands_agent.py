"""
ARISE + Strands Agents — Self-Evolving Tool Demo

Demonstrates ARISE evolving an agent's tool library at runtime. The agent
starts with only 3 basic tools (write_file, read_file, list_dir) defined as
native Strands @tool functions. When the agent fails repeatedly, ARISE detects
the gap, synthesizes a new tool, tests it in a sandbox, and promotes it to the
active library.

Requirements:
    pip install strands-agents boto3
    # AWS credentials configured for Bedrock (default profile, or set AWS_PROFILE)
    export OPENAI_API_KEY=sk-...  # for ARISE's tool synthesis (cheap model)

Usage:
    python examples/strands_agent.py
"""

import json
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import Agent, tool
from strands.models import BedrockModel

from arise import ARISE, Sandbox
from arise.config import ARISEConfig
from arise.rewards.builtin import llm_judge_reward
from arise.rewards.composite import CompositeReward
from arise.types import SkillOrigin, Trajectory


# ---------------------------------------------------------------------------
# Work directory
# ---------------------------------------------------------------------------

WORK_DIR = os.path.join(tempfile.gettempdir(), "arise_strands_test")


# ---------------------------------------------------------------------------
# Seed tools — native Strands @tool functions
# ---------------------------------------------------------------------------

@tool
def write_file(path: str, content: str) -> str:
    """Write text content to a file. Creates parent directories if needed. Use this for plain text, JSON, YAML, CSV, HTML, Markdown, Dockerfiles, .env files, and other text-based formats."""
    if not os.path.isabs(path):
        path = os.path.join(os.environ.get("ARISE_WORK_DIR", "."), path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"


@tool
def read_file(path: str) -> str:
    """Read a file and return its text contents (max 5000 chars). Use this to inspect existing files before transforming them."""
    if not os.path.isabs(path):
        path = os.path.join(os.environ.get("ARISE_WORK_DIR", "."), path)
    try:
        with open(path) as f:
            return f.read()[:5000]
    except FileNotFoundError:
        return f"Error: file not found: {path}"


@tool
def list_dir(path: str = ".") -> str:
    """List files in a directory. Returns one filename per line."""
    if not os.path.isabs(path):
        path = os.path.join(os.environ.get("ARISE_WORK_DIR", "."), path)
    try:
        entries = os.listdir(path)
        return "\n".join(entries) if entries else "(empty directory)"
    except FileNotFoundError:
        return f"Error: directory not found: {path}"


# ---------------------------------------------------------------------------
# Reward — composite: structural checks + LLM judge + tool usage
# ---------------------------------------------------------------------------

# Track when each episode starts so we only credit NEW output files
_episode_start_time = 0.0


def structural_reward(trajectory: Trajectory) -> float:
    """Check if the agent produced a NEW output file during this episode."""
    outcome = trajectory.outcome or ""

    # Agent explicitly says it can't do the task
    if "TOOL_MISSING" in outcome:
        return 0.0
    if outcome.startswith("Error"):
        return 0.0

    # Check the output directory for files created AFTER the episode started
    output_dir = os.path.join(WORK_DIR, "output")
    if not os.path.exists(output_dir):
        return 0.0

    try:
        new_files = []
        for root, _, files in os.walk(output_dir):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.getmtime(fp) > _episode_start_time:
                    new_files.append(fp)
    except Exception:
        return 0.0

    if not new_files:
        return 0.0

    latest = max(new_files, key=os.path.getmtime)
    size = os.path.getsize(latest)

    if size == 0:
        return 0.0

    score = 0.3  # new file exists and non-empty

    ext = os.path.splitext(latest)[1].lower()
    try:
        # Binary formats — check magic bytes
        if ext == ".zip":
            with open(latest, "rb") as f:
                magic = f.read(4)
            if magic[:2] == b"PK":
                score += 0.5
        # Text formats — validate content
        else:
            content = open(latest).read()
            if ext == ".json":
                json.loads(content)
                score += 0.5
            elif ext in (".yaml", ".yml"):
                if ":" in content and not content.strip().startswith("{"):
                    score += 0.5
            elif ext == ".csv":
                lines = content.strip().split("\n")
                if len(lines) >= 2 and "," in lines[0]:
                    score += 0.5
            elif ext in (".html", ".xml"):
                if "<" in content and ">" in content:
                    score += 0.5
            elif ext in (".env", ".ini", ".cfg", ".toml"):
                if "=" in content or "[" in content:
                    score += 0.5
            else:
                if len(content) > 20:
                    score += 0.3
    except Exception:
        pass

    return min(score, 1.0)


def tool_usage_reward(trajectory: Trajectory) -> float:
    """Reward for actually using tools (0 if none called)."""
    tool_calls = [s for s in trajectory.steps if s.action not in ("respond", "error")]
    if not tool_calls:
        return 0.0  # no tools used = clear failure
    has_errors = any(s.error for s in trajectory.steps)
    return 0.7 if has_errors else 1.0


reward_fn = CompositeReward([
    (structural_reward, 0.5),
    (llm_judge_reward, 0.3),
    (tool_usage_reward, 0.2),
])


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def setup_fixtures():
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(os.path.join(WORK_DIR, "output"), exist_ok=True)

    # Config file
    with open(os.path.join(WORK_DIR, "app_config.json"), "w") as f:
        json.dump({
            "app_name": "myservice",
            "version": "1.4.2",
            "port": 8080,
            "database": {
                "host": "db.internal.example.com",
                "port": 5432,
                "name": "production",
                "pool_size": 20,
            },
            "cache": {
                "host": "redis.internal.example.com",
                "port": 6379,
                "ttl": 300,
            },
            "features": {
                "rate_limiting": True,
                "analytics": True,
                "beta_features": False,
            },
        }, f, indent=2)

    # User data (CSV)
    with open(os.path.join(WORK_DIR, "users.csv"), "w") as f:
        f.write("id,name,email,role,salary,active\n")
        f.write("1,Alice,alice@example.com,admin,95000,true\n")
        f.write("2,Bob,bob@example.com,developer,82000,true\n")
        f.write("3,Charlie,charlie@example.com,developer,78000,false\n")
        f.write("4,Diana,diana@example.com,designer,71000,true\n")
        f.write("5,Eve,eve@example.com,admin,92000,true\n")
        f.write("6,Frank,frank@example.com,developer,85000,true\n")
        f.write("7,Grace,grace@example.com,manager,105000,true\n")
        f.write("8,Hank,hank@example.com,developer,79000,false\n")

    # Multiple log files for aggregation
    logs_dir = os.path.join(WORK_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    for day, entries in [
        ("2024-01-15", [
            "2024-01-15 08:12:33 ERROR Database connection timeout",
            "2024-01-15 08:12:35 INFO Retrying connection...",
            "2024-01-15 08:12:36 INFO Connected to database",
            "2024-01-15 09:45:12 WARN High memory usage: 87%",
            "2024-01-15 10:00:00 INFO Health check passed",
            "2024-01-15 14:22:18 ERROR Failed to process request: timeout",
            "2024-01-15 14:22:19 INFO Request retried successfully",
        ]),
        ("2024-01-16", [
            "2024-01-16 07:00:00 INFO Service started",
            "2024-01-16 07:00:01 INFO Health check passed",
            "2024-01-16 11:33:45 ERROR Disk space low: 92% used",
            "2024-01-16 11:34:00 WARN Cleaning temp files",
            "2024-01-16 15:00:00 INFO Backup completed",
            "2024-01-16 18:45:22 ERROR Connection refused: redis",
            "2024-01-16 18:45:25 ERROR Connection refused: redis",
            "2024-01-16 18:46:00 INFO Redis reconnected",
        ]),
        ("2024-01-17", [
            "2024-01-17 06:00:00 INFO Service started",
            "2024-01-17 09:15:33 WARN Slow query detected: 2.3s",
            "2024-01-17 09:15:34 WARN Slow query detected: 3.1s",
            "2024-01-17 12:00:00 INFO Health check passed",
            "2024-01-17 16:44:11 ERROR Out of memory",
            "2024-01-17 16:44:12 INFO Service restarting...",
            "2024-01-17 16:44:30 INFO Service started",
        ]),
    ]:
        with open(os.path.join(logs_dir, f"app_{day}.log"), "w") as f:
            f.write("\n".join(entries) + "\n")

    # Source code files for archiving
    src_dir = os.path.join(WORK_DIR, "src")
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, "main.py"), "w") as f:
        f.write("from app import create_app\n\napp = create_app()\n\nif __name__ == '__main__':\n    app.run()\n")
    with open(os.path.join(src_dir, "app.py"), "w") as f:
        f.write("def create_app():\n    return App()\n\nclass App:\n    def run(self): pass\n")
    with open(os.path.join(src_dir, "utils.py"), "w") as f:
        f.write("import hashlib\n\ndef hash_string(s):\n    return hashlib.sha256(s.encode()).hexdigest()\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    for d in ["./arise_skills", "./arise_trajectories"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)

    os.environ["ARISE_WORK_DIR"] = WORK_DIR
    setup_fixtures()

    # --- Strands agent with native @tool functions ---
    strands_agent = Agent(
        model=BedrockModel(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
        ),
        tools=[write_file, read_file, list_dir],
        system_prompt=(
            "You are a file generation agent. You create, read, and transform files "
            "using the tools provided to you.\n\n"
            "RULES:\n"
            "- Use the provided tools for ALL file operations.\n"
            "- If no tool can accomplish the task, respond with: "
            "TOOL_MISSING: <describe what tool you need>\n"
            "- After completing the task, summarize what you did.\n"
            "- For format conversions, read the source file first, then write the result."
        ),
        callback_handler=None,
    )

    # --- ARISE wraps the Strands agent directly ---
    arise = ARISE(
        agent=strands_agent,       # Pass the Strands Agent directly!
        reward_fn=reward_fn,
        model="gpt-4o-mini",       # cheap model for tool synthesis (not the agent's model)
        sandbox=Sandbox(backend="subprocess"),
        config=ARISEConfig(
            model="gpt-4o-mini",
            failure_threshold=2,
            max_evolutions_per_hour=10,
            verbose=True,
        ),
    )

    tasks = [
        # Phase 1: Warm-up — seed tools handle these
        f"Create a JSON config file at {WORK_DIR}/output/db_config.json with host=localhost, port=5432, name=mydb, pool_size=10",
        f"Read {WORK_DIR}/app_config.json and list all the feature flags and their values",

        # Phase 2: Tasks that REQUIRE new tools — can't be done with read/write/list
        # These need a tool that computes SHA-256 hashes
        f"Compute the SHA-256 hash of {WORK_DIR}/app_config.json and write the result to {WORK_DIR}/output/config_hash.txt in the format: <hash>  app_config.json",
        f"Compute the SHA-256 hash of {WORK_DIR}/app_config.json and write the result to {WORK_DIR}/output/config_hash2.txt",
        f"Compute the SHA-256 hash of {WORK_DIR}/users.csv and write only the hex digest to {WORK_DIR}/output/users_hash.txt",

        # These need a tool that creates ZIP archives
        f"Create a ZIP archive at {WORK_DIR}/output/src_backup.zip containing all files from {WORK_DIR}/src/",
        f"Create a ZIP archive at {WORK_DIR}/output/logs_backup.zip containing all .log files from {WORK_DIR}/logs/",
        f"Create a ZIP archive at {WORK_DIR}/output/project.zip containing all files from {WORK_DIR}/src/ and {WORK_DIR}/app_config.json",

        # These need a tool that parses/sorts CSV data programmatically
        f"Read {WORK_DIR}/users.csv, sort the rows by salary (highest first), and write the sorted CSV to {WORK_DIR}/output/users_by_salary.csv",
        f"Read {WORK_DIR}/users.csv, filter only active users, and write the result as CSV to {WORK_DIR}/output/active_users.csv",
        f"Read {WORK_DIR}/users.csv, compute the average salary per role, and write the result as JSON to {WORK_DIR}/output/salary_by_role.json",

        # These need a tool that aggregates/searches across log files
        f"Read all .log files in {WORK_DIR}/logs/, count ERROR/WARN/INFO lines across all files, and write a summary JSON to {WORK_DIR}/output/log_summary.json",
        f"Read all .log files in {WORK_DIR}/logs/, extract all ERROR lines, and write them sorted by timestamp to {WORK_DIR}/output/errors.log",

        # Phase 3: Re-run tasks — should use evolved tools
        f"Compute the SHA-256 hash of {WORK_DIR}/users.csv and write the result to {WORK_DIR}/output/users_hash2.txt",
        f"Read {WORK_DIR}/users.csv, sort by name alphabetically, and write to {WORK_DIR}/output/users_sorted.csv",
        f"Create a ZIP archive at {WORK_DIR}/output/full_backup.zip containing everything in {WORK_DIR}/src/ and {WORK_DIR}/logs/",
    ]

    print("=" * 70)
    print("ARISE + Strands Agents — Self-Evolving Tool Demo")
    print(f"Work directory: {WORK_DIR}")
    print("=" * 70)
    print()
    print("Agent: Strands + Claude Haiku (Bedrock)")
    print("Tool synthesis: GPT-4o-mini")
    print("Seed tools: write_file, read_file, list_dir (native @tool)")
    print("Reward: 40% structural + 40% LLM judge + 20% tool usage")
    print()
    print("Tasks escalate from simple file I/O to SHA-256 hashing, ZIP archiving,")
    print("CSV sorting/filtering, and log aggregation — forcing ARISE to evolve.")
    print()

    for i, task in enumerate(tasks):
        global _episode_start_time
        _episode_start_time = time.time()

        print(f"\n{'=' * 70}")
        print(f"Task {i + 1}/{len(tasks)}")
        print(f"  {task[:90]}{'...' if len(task) > 90 else ''}")
        print("-" * 70)
        result = arise.run(task)
        result_str = str(result)
        if len(result_str) > 500:
            print(f"Result:\n{result_str[:500]}\n... ({len(result_str)} chars total)")
        else:
            print(f"Result:\n{result_str}")

    # Summary
    print(f"\n{'=' * 70}")
    print("FINAL REPORT")
    print("=" * 70)
    stats = arise.stats
    print(f"Episodes:             {stats['episodes_run']}")
    print(f"Active skills:        {stats['active']}")
    print(f"Total skills created: {stats['total_skills']}")
    print(f"Success rate:         {stats['recent_success_rate']:.0%}")

    print("\nActive Skills:")
    for skill in arise.skills:
        origin = skill.origin.value
        rate = f"{skill.success_rate:.0%}" if skill.invocation_count > 0 else "n/a"
        print(f"  [{origin:>11}] {skill.name:<35} success={rate}")

    synthesized = [s for s in arise.skills if s.origin in (SkillOrigin.SYNTHESIZED, SkillOrigin.REFINED)]
    if synthesized:
        print(f"\nTools the agent created itself:")
        for s in synthesized:
            print(f"\n  --- {s.name} ---")
            print(f"  {s.description}")
            impl_lines = s.implementation.strip().split("\n")
            preview = "\n".join(f"    {l}" for l in impl_lines[:8])
            if len(impl_lines) > 8:
                preview += f"\n    ... ({len(impl_lines)} lines total)"
            print(preview)

    # Show generated files
    output_dir = os.path.join(WORK_DIR, "output")
    if os.path.exists(output_dir):
        print(f"\nGenerated files in {output_dir}:")
        for f in sorted(os.listdir(output_dir)):
            size = os.path.getsize(os.path.join(output_dir, f))
            print(f"  {f:<30} {size:>6} bytes")

    shutil.rmtree(WORK_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
