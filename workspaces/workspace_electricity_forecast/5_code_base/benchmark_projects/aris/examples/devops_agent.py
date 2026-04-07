"""
ARISE Real-World Test — DevOps Agent

Starts with basic tools (run_command, read_file, write_file).
Given real sysadmin tasks that require specialized tools it doesn't have yet.

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/devops_agent.py
"""

import os
import shutil
import sys
import inspect
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arise import ARISE, Sandbox, SkillLibrary, ToolSpec
from arise.config import ARISEConfig
from arise.types import Skill, SkillOrigin, SkillStatus, Trajectory


# --- Seed tools (bare minimum) ---

def run_command(command: str) -> str:
    """Run a shell command and return stdout. Max 10s timeout."""
    import subprocess
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        out = r.stdout.strip()
        if r.stderr.strip():
            out += "\nSTDERR: " + r.stderr.strip()
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read a file and return its contents. Returns error string on failure."""
    try:
        with open(path) as f:
            content = f.read()
        return content[:5000]  # cap at 5k chars
    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent dirs if needed."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


# --- Reward: check if the agent actually used tools and got a result ---

def devops_reward(trajectory: Trajectory) -> float:
    outcome = trajectory.outcome
    if not outcome:
        return 0.0
    if outcome.startswith("Error:"):
        return 0.0
    if "TOOL_MISSING" in outcome:
        return 0.0

    tool_calls = [s for s in trajectory.steps if s.action not in ("respond", "error")]
    has_errors = any(s.error for s in trajectory.steps)

    if has_errors:
        return 0.2
    if not tool_calls:
        return 0.3  # solved without tools — low reward
    return 1.0


# --- Agent ---

def devops_agent(task: str, tools: list[ToolSpec]) -> str:
    from arise.llm import llm_call

    tool_descs = []
    tool_map = {}
    for t in tools:
        params = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in t.parameters.get("properties", {}).items())
        tool_descs.append(f"- {t.name}({params}): {t.description}")
        tool_map[t.name] = t.fn

    prompt = f"""\
You are a DevOps agent running on macOS. Solve the task using ONLY the provided tools.

AVAILABLE TOOLS:
{chr(10).join(tool_descs)}

TASK: {task}

RULES:
- You MUST call the provided tool functions. Do NOT use Python builtins for I/O.
- If you need a capability that no tool provides, print("TOOL_MISSING: <what you need>")
- For shell commands, use run_command("your command here")
- Print the final answer clearly with print()

Write Python code. Return ONLY code, no markdown."""

    code = llm_call([{"role": "user", "content": prompt}], model="gpt-4o-mini")
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(l for l in lines[1:] if l.strip() != "```")

    namespace = dict(tool_map)
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, namespace)  # noqa: S102
        output = buf.getvalue().strip()
        return output if output else "No output"
    except Exception as e:
        return f"Error: {e}"


# --- Setup test fixtures ---

def setup_test_fixtures(base_dir: str):
    """Create realistic test files for the agent to work with."""

    # Fake log file with errors
    os.makedirs(base_dir, exist_ok=True)

    with open(os.path.join(base_dir, "app.log"), "w") as f:
        f.write("""2024-03-14 10:00:01 INFO  Server started on port 8080
2024-03-14 10:00:15 INFO  Connected to database
2024-03-14 10:01:22 WARN  High memory usage: 85%
2024-03-14 10:02:33 ERROR Failed to process request: timeout after 30s
2024-03-14 10:02:33 ERROR Stack trace: ConnectionPool.acquire() line 142
2024-03-14 10:03:01 INFO  Request processed in 250ms
2024-03-14 10:04:15 ERROR Database connection lost
2024-03-14 10:04:16 ERROR Retry 1/3: reconnecting...
2024-03-14 10:04:17 INFO  Database reconnected
2024-03-14 10:05:30 WARN  Disk usage at 90%
2024-03-14 10:06:00 ERROR Out of memory: killed process worker-3
2024-03-14 10:06:01 INFO  Restarting worker-3
2024-03-14 10:07:00 INFO  Health check OK
2024-03-14 10:08:22 ERROR SSL certificate expires in 5 days
2024-03-14 10:09:00 INFO  Request processed in 180ms
2024-03-14 10:10:00 WARN  CPU usage at 92%
""")

    # Config file (JSON)
    with open(os.path.join(base_dir, "config.json"), "w") as f:
        json.dump({
            "app": {
                "name": "myservice",
                "version": "2.3.1",
                "port": 8080,
                "workers": 4,
                "max_memory_mb": 512,
            },
            "database": {
                "host": "db.internal.example.com",
                "port": 5432,
                "name": "production",
                "pool_size": 20,
                "timeout_ms": 5000,
            },
            "cache": {
                "host": "redis.internal.example.com",
                "port": 6379,
                "ttl_seconds": 300,
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/myservice/app.log",
            },
        }, f, indent=2)

    # CSV data
    with open(os.path.join(base_dir, "metrics.csv"), "w") as f:
        f.write("timestamp,cpu_pct,mem_pct,disk_pct,req_per_sec,error_rate\n")
        f.write("2024-03-14T10:00,45,62,78,120,0.01\n")
        f.write("2024-03-14T10:05,78,71,78,150,0.03\n")
        f.write("2024-03-14T10:10,92,85,80,180,0.08\n")
        f.write("2024-03-14T10:15,88,89,82,160,0.12\n")
        f.write("2024-03-14T10:20,65,75,82,140,0.02\n")
        f.write("2024-03-14T10:25,52,68,83,130,0.01\n")
        f.write("2024-03-14T10:30,95,92,85,200,0.15\n")
        f.write("2024-03-14T10:35,48,60,85,110,0.01\n")

    # Nginx-style access log
    with open(os.path.join(base_dir, "access.log"), "w") as f:
        f.write("""192.168.1.10 - - [14/Mar/2024:10:00:01] "GET /api/users HTTP/1.1" 200 1234
192.168.1.11 - - [14/Mar/2024:10:00:02] "POST /api/login HTTP/1.1" 200 89
192.168.1.10 - - [14/Mar/2024:10:00:03] "GET /api/users/123 HTTP/1.1" 200 456
10.0.0.5 - - [14/Mar/2024:10:00:04] "GET /api/products HTTP/1.1" 200 5678
192.168.1.12 - - [14/Mar/2024:10:00:05] "POST /api/orders HTTP/1.1" 201 234
10.0.0.5 - - [14/Mar/2024:10:00:06] "GET /api/products/456 HTTP/1.1" 404 45
192.168.1.10 - - [14/Mar/2024:10:00:07] "DELETE /api/users/789 HTTP/1.1" 403 67
192.168.1.13 - - [14/Mar/2024:10:00:08] "GET /api/users HTTP/1.1" 200 1234
10.0.0.5 - - [14/Mar/2024:10:00:09] "PUT /api/products/456 HTTP/1.1" 500 89
192.168.1.10 - - [14/Mar/2024:10:00:10] "GET /api/health HTTP/1.1" 200 12
10.0.0.5 - - [14/Mar/2024:10:00:11] "GET /api/products HTTP/1.1" 200 5678
192.168.1.14 - - [14/Mar/2024:10:00:12] "POST /api/login HTTP/1.1" 401 34
10.0.0.5 - - [14/Mar/2024:10:00:13] "GET /api/products/789 HTTP/1.1" 500 89
""")

    # Dockerfile
    with open(os.path.join(base_dir, "Dockerfile"), "w") as f:
        f.write("""FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "server.py"]
""")

    # requirements.txt with outdated versions
    with open(os.path.join(base_dir, "requirements.txt"), "w") as f:
        f.write("flask==2.0.1\nrequests==2.26.0\npsycopg2-binary==2.9.1\nredis==3.5.3\ngunicorn==20.1.0\n")


def main():
    # Clean previous runs
    for d in ["./arise_skills_devops", "./arise_trajectories_devops"]:
        if os.path.exists(d):
            shutil.rmtree(d)

    test_dir = "/tmp/arise_devops_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    setup_test_fixtures(test_dir)

    library = SkillLibrary("./arise_skills_devops")

    # Add seed tools
    for fn, desc in [
        (run_command, "Run a shell command and return output"),
        (read_file, "Read a file's contents"),
        (write_file, "Write content to a file"),
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
        agent_fn=devops_agent,
        reward_fn=devops_reward,
        model="gpt-4o-mini",
        sandbox=Sandbox(backend="subprocess"),
        skill_library=library,
        config=ARISEConfig(
            model="gpt-4o-mini",
            skill_store_path="./arise_skills_devops",
            trajectory_store_path="./arise_trajectories_devops",
            failure_threshold=3,
            max_evolutions_per_hour=10,
            verbose=True,
        ),
    )

    # Real-world DevOps tasks — progressively harder
    tasks = [
        # Phase 1: Basic tasks the agent can do with seed tools
        f"Count the number of ERROR lines in {test_dir}/app.log",
        f"What port is the app configured to run on? Read {test_dir}/config.json",

        # Phase 2: Log analysis — needs pattern extraction
        f"Parse {test_dir}/app.log and give me a summary: count of INFO, WARN, ERROR lines, and list the unique error messages",
        f"Find the top 3 IP addresses by request count in {test_dir}/access.log",
        f"List all HTTP 4xx and 5xx errors from {test_dir}/access.log with their URLs",

        # Phase 3: Metrics analysis — needs CSV/data tools
        f"Read {test_dir}/metrics.csv and find the time periods where CPU > 90% or error_rate > 0.10",
        f"Calculate the average CPU, memory, and disk usage from {test_dir}/metrics.csv",

        # Phase 4: Config management
        f"Read {test_dir}/config.json and check if any timeouts are above 3000ms. List them.",
        f"Generate a health report: combine info from {test_dir}/app.log (error count), {test_dir}/metrics.csv (avg cpu/mem), and {test_dir}/config.json (service name + version)",

        # Phase 5: Re-run earlier tasks to see if new tools help
        f"Parse {test_dir}/access.log and give me: total requests, requests per endpoint, error rate by endpoint",
        f"Find all WARN and ERROR entries in {test_dir}/app.log, group them by type, and suggest fixes",
    ]

    print("=" * 70)
    print("ARISE Real-World Test — DevOps Agent")
    print(f"Test fixtures in: {test_dir}")
    print("=" * 70)

    for i, task in enumerate(tasks):
        print(f"\n{'=' * 70}")
        print(f"Task {i + 1}/{len(tasks)}")
        print(f"  {task[:90]}{'...' if len(task) > 90 else ''}")
        print("-" * 70)
        result = agent.run(task)
        # Truncate long results for display
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
        print(f"  [{origin:>11}] {skill.name:<30} success={rate}, invocations={skill.invocation_count}")

    # Show what was created
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

    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
