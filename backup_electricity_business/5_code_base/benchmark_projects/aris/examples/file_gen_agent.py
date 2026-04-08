"""
ARISE Example — File Generation Agent (Function Calling)

Demonstrates a realistic agent architecture using OpenAI function calling
(not code generation). The agent decides which tools to call, ARISE evolves
the tool library when tools are missing.

Flow:
  1. User asks to create a DOCX/HTML/YAML/etc. file
  2. Agent looks at available tools via function calling
  3. If no suitable tool exists, agent fails gracefully
  4. ARISE detects the gap and synthesizes a new tool (e.g., generate_docx)
  5. Next time, the agent calls the new tool directly

Reward model: 40% structural validity + 40% LLM judge + 20% tool usage.
This shows how ARISE handles non-binary quality assessment.

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/file_gen_agent.py
"""

import json
import os
import shutil
import sys
import inspect
import tempfile
import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arise import ARISE, Sandbox, SkillLibrary
from arise.config import ARISEConfig
from arise.rewards.builtin import llm_judge_reward
from arise.rewards.composite import CompositeReward
from arise.types import Skill, SkillOrigin, SkillStatus, ToolSpec, Trajectory


# ---------------------------------------------------------------------------
# Work directory — all file operations happen here
# ---------------------------------------------------------------------------

WORK_DIR = os.path.join(tempfile.gettempdir(), "arise_filegen_test")


# ---------------------------------------------------------------------------
# Seed tools — bare minimum file operations
# ---------------------------------------------------------------------------

def write_file(path: str, content: str) -> str:
    """Write text content to a file. Creates parent directories if needed. Use this for plain text, JSON, YAML, CSV, HTML, Markdown, Dockerfiles, .env files, and other text-based formats."""
    import os
    if not os.path.isabs(path):
        path = os.path.join(os.environ.get("ARISE_WORK_DIR", "."), path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"


def read_file(path: str) -> str:
    """Read a file and return its text contents (max 5000 chars). Use this to inspect existing files before transforming them."""
    import os
    if not os.path.isabs(path):
        path = os.path.join(os.environ.get("ARISE_WORK_DIR", "."), path)
    try:
        with open(path) as f:
            return f.read()[:5000]
    except FileNotFoundError:
        return f"Error: file not found: {path}"


def list_dir(path: str = ".") -> str:
    """List files in a directory. Returns one filename per line."""
    import os
    if not os.path.isabs(path):
        path = os.path.join(os.environ.get("ARISE_WORK_DIR", "."), path)
    try:
        entries = os.listdir(path)
        return "\n".join(entries) if entries else "(empty directory)"
    except FileNotFoundError:
        return f"Error: directory not found: {path}"


# ---------------------------------------------------------------------------
# Function-calling agent using OpenAI API
# ---------------------------------------------------------------------------

def _openai_chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Raw OpenAI chat completion with optional tool definitions."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

    payload: dict = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 4096,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _toolspec_to_openai_tool(ts: ToolSpec) -> dict:
    """Convert an ARISE ToolSpec to an OpenAI function-calling tool definition."""
    return {
        "type": "function",
        "function": {
            "name": ts.name,
            "description": ts.description,
            "parameters": ts.parameters,
        },
    }


def file_gen_agent(task: str, tools: list[ToolSpec]) -> str:
    """Agent that uses OpenAI function calling to complete file generation tasks.

    This is a realistic agent loop:
    1. Send task + tool definitions to the LLM
    2. If LLM returns tool_calls, execute them and send results back
    3. Repeat until LLM returns a final text response
    4. If the agent can't find a suitable tool, it says so (triggering ARISE evolution)
    """
    tool_map = {t.name: t.fn for t in tools}
    openai_tools = [_toolspec_to_openai_tool(t) for t in tools]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a file generation agent. You create, read, and transform files "
                "using the tools provided to you.\n\n"
                "RULES:\n"
                "- Use the provided tools for ALL file operations.\n"
                "- If no tool can accomplish the task, respond with: "
                "TOOL_MISSING: <describe what tool you need>\n"
                "- After completing the task, summarize what you did.\n"
                "- For format conversions, read the source file first, then write the result."
            ),
        },
        {"role": "user", "content": task},
    ]

    # Agent loop: up to 10 turns of tool calling
    for _ in range(10):
        response = _openai_chat(messages, openai_tools)
        choice = response["choices"][0]
        msg = choice["message"]

        # If the LLM wants to call tools
        if msg.get("tool_calls"):
            messages.append(msg)

            for tool_call in msg["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                fn_args = json.loads(tool_call["function"]["arguments"])

                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**fn_args)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Error: tool '{fn_name}' not found"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result)[:2000],
                })
            continue

        # Final text response
        return msg.get("content", "No response")

    return "Error: agent exceeded maximum turns"


# ---------------------------------------------------------------------------
# Reward — composite: structural checks + LLM judge + tool usage
# ---------------------------------------------------------------------------

def structural_reward(trajectory: Trajectory) -> float:
    """Check if the agent produced a valid file."""
    outcome = trajectory.outcome or ""
    if outcome.startswith("Error"):
        return 0.0

    score = 0.0
    try:
        all_files = []
        for root, _, files in os.walk(WORK_DIR):
            for f in files:
                all_files.append(os.path.join(root, f))
    except Exception:
        return 0.0

    if not all_files:
        return 0.0

    latest = max(all_files, key=os.path.getmtime)
    size = os.path.getsize(latest)

    if size > 0:
        score += 0.3
    if size > 50:
        score += 0.2

    ext = os.path.splitext(latest)[1].lower()
    try:
        content = open(latest).read()
        if ext == ".json":
            json.loads(content)
            score += 0.3
        elif ext in (".yaml", ".yml"):
            if ":" in content and not content.strip().startswith("{"):
                score += 0.3
        elif ext in (".py", ".sh", ".bash"):
            if content.count("\n") >= 3:
                score += 0.3
        elif ext in (".html", ".xml"):
            if "<" in content and ">" in content:
                score += 0.3
        elif ext in (".env", ".ini", ".cfg", ".toml"):
            if "=" in content or "[" in content:
                score += 0.3
        else:
            if content.count("\n") >= 2:
                score += 0.2
    except Exception:
        pass

    return min(score, 1.0)


def tool_usage_reward(trajectory: Trajectory) -> float:
    """Reward for actually using tools vs just responding."""
    tool_calls = [s for s in trajectory.steps if s.action not in ("respond", "error")]
    if not tool_calls:
        return 0.2
    has_errors = any(s.error for s in trajectory.steps)
    return 0.7 if has_errors else 1.0


file_gen_reward = CompositeReward([
    (structural_reward, 0.4),    # 40%: did it produce a valid file?
    (llm_judge_reward, 0.4),     # 40%: LLM rates overall quality
    (tool_usage_reward, 0.2),    # 20%: did it use tools?
])


# ---------------------------------------------------------------------------
# Setup reference files
# ---------------------------------------------------------------------------

def setup_fixtures():
    os.makedirs(WORK_DIR, exist_ok=True)

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

    with open(os.path.join(WORK_DIR, "users.csv"), "w") as f:
        f.write("id,name,email,role,active\n")
        f.write("1,Alice,alice@example.com,admin,true\n")
        f.write("2,Bob,bob@example.com,developer,true\n")
        f.write("3,Charlie,charlie@example.com,developer,false\n")
        f.write("4,Diana,diana@example.com,designer,true\n")
        f.write("5,Eve,eve@example.com,admin,true\n")

    with open(os.path.join(WORK_DIR, "sample.env"), "w") as f:
        f.write("DATABASE_URL=postgresql://user:pass@db.internal:5432/prod\n")
        f.write("REDIS_URL=redis://redis.internal:6379\n")
        f.write("API_KEY=sk-placeholder-key\n")
        f.write("LOG_LEVEL=info\n")
        f.write("PORT=8080\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    for d in ["./arise_skills_filegen", "./arise_trajectories_filegen"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)

    os.environ["ARISE_WORK_DIR"] = WORK_DIR
    setup_fixtures()

    library = SkillLibrary("./arise_skills_filegen")

    for fn, desc in [
        (write_file, "Write text content to a file. Creates parent directories if needed."),
        (read_file, "Read a file and return its text contents (max 5000 chars)."),
        (list_dir, "List files in a directory. Returns one filename per line."),
    ]:
        skill = Skill(
            name=fn.__name__,
            description=desc,
            implementation=inspect.getsource(fn),
            origin=SkillOrigin.MANUAL,
            status=SkillStatus.ACTIVE,
        )
        library.add(skill)
        library.promote(skill.id)

    agent = ARISE(
        agent_fn=file_gen_agent,
        reward_fn=file_gen_reward,
        model="gpt-4o-mini",
        sandbox=Sandbox(backend="subprocess"),
        skill_library=library,
        config=ARISEConfig(
            model="gpt-4o-mini",
            skill_store_path="./arise_skills_filegen",
            trajectory_store_path="./arise_trajectories_filegen",
            failure_threshold=3,
            max_evolutions_per_hour=10,
            verbose=True,
        ),
    )

    tasks = [
        # Phase 1: Simple file creation (seed tools handle this)
        f"Create a JSON config file at output/db_config.json with host=localhost, port=5432, name=mydb, pool_size=10",
        f"Read {WORK_DIR}/app_config.json and list all the feature flags",

        # Phase 2: Format conversion
        f"Read {WORK_DIR}/app_config.json and convert it to a .env file at output/app.env with flattened keys like APP_NAME=myservice, DATABASE_HOST=db.internal.example.com, etc.",
        f"Read {WORK_DIR}/users.csv and convert it to a JSON array at output/users.json",
        f"Read {WORK_DIR}/app_config.json and generate a YAML version at output/app_config.yaml",

        # Phase 3: Templated generation
        f"Generate a Dockerfile at output/Dockerfile for a Python 3.11 Flask app that reads config from {WORK_DIR}/app_config.json (use the port and app_name from it)",
        f"Read {WORK_DIR}/users.csv and generate an HTML table at output/users.html with all users, highlighting inactive users in red",
        f"Generate a docker-compose.yaml at output/docker-compose.yaml with services for the app (port from {WORK_DIR}/app_config.json), postgres (port 5432), and redis (port 6379)",

        # Phase 4: Validation and analysis
        f"Read {WORK_DIR}/sample.env and generate a JSON schema at output/env_schema.json that documents each variable with its type and description",
        f"Read {WORK_DIR}/users.csv and generate a summary report at output/user_report.txt with: total users, active/inactive counts, role distribution",

        # Phase 5: Re-run to see if evolved tools help
        f"Read {WORK_DIR}/app_config.json and create a flattened .env file at output/app_flat.env",
        f"Read {WORK_DIR}/users.csv and generate a markdown table at output/users.md",
    ]

    print("=" * 70)
    print("ARISE Example — File Generation Agent (Function Calling)")
    print(f"Work directory: {WORK_DIR}")
    print("=" * 70)
    print()
    print("This agent uses OpenAI function calling (not code generation).")
    print("The LLM decides which tools to call. ARISE evolves the tool library.")
    print("Reward: 40% structural validity + 40% LLM judge + 20% tool usage")
    print()

    for i, task in enumerate(tasks):
        print(f"\n{'=' * 70}")
        print(f"Task {i + 1}/{len(tasks)}")
        print(f"  {task[:90]}{'...' if len(task) > 90 else ''}")
        print("-" * 70)
        result = agent.run(task)
        if len(result) > 500:
            print(f"Result:\n{result[:500]}\n... ({len(result)} chars total)")
        else:
            print(f"Result:\n{result}")

    # Summary
    print(f"\n{'=' * 70}")
    print("FINAL REPORT")
    print("=" * 70)
    stats = agent.stats
    print(f"Episodes:             {stats['episodes_run']}")
    print(f"Active skills:        {stats['active']}")
    print(f"Total skills created: {stats['total_skills']}")
    print(f"Success rate:         {stats['recent_success_rate']:.0%}")

    print("\nActive Skills:")
    for skill in agent.skills:
        origin = skill.origin.value
        rate = f"{skill.success_rate:.0%}" if skill.invocation_count > 0 else "n/a"
        print(f"  [{origin:>11}] {skill.name:<35} success={rate}")

    synthesized = [s for s in agent.skills if s.origin in (SkillOrigin.SYNTHESIZED, SkillOrigin.REFINED)]
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
