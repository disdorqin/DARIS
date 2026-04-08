from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    manager = repo_root / "workspaces" / "workspace_electricity_forecast" / "2_agent_system" / "1_research_manager" / "run.py"
    log_path = repo_root / "workspaces" / "workspace_electricity_forecast" / "report" / "final_workflow_run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(manager), "--request", "尖峰电价预测", "--rounds", "1"]
    env = os.environ.copy()
    env["PYUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"LAUNCHED: {' '.join(cmd)}\n")
        log_file.flush()
        assert proc.stdout is not None
        for line in proc.stdout:
            log_file.write(line)
            log_file.flush()

    return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
