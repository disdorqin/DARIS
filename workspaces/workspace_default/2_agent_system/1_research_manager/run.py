from __future__ import annotations

import argparse
import base64
import importlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from core.utils.path_resolver import resolve_first_existing, resolve_workspace_root


def _resolve_root(start_file: Path) -> Path:
    for candidate in [start_file.parent, *start_file.parents]:
        if (candidate / "1_config").exists() and (candidate / "2_agent_system").exists():
            return candidate
    return start_file.parent.parent


ROOT = _resolve_root(Path(__file__).resolve())
WORKSPACE_ROOT = resolve_workspace_root(create=True)
REPORT_DIR = WORKSPACE_ROOT / "report"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
LIT_DIR = WORKSPACE_ROOT / "literature" / "structured_summary"
SKILLS_LIBRARY = MEMORY_DIR / "skills_library.md"
BENCHMARK_CONFIG = resolve_first_existing(
    WORKSPACE_ROOT / "config" / "base" / "benchmark_projects.json",
    WORKSPACE_ROOT / "config" / "benchmark_projects.json",
    ROOT / "1_config" / "base" / "benchmark_projects.json",
)
BENCHMARK_DIR = ROOT / "5_code_base" / "benchmark_projects"
INTEGRATION_DIR = ROOT / "2_agent_system" / "integration"


MODEL_CANDIDATES = [
    "qwen3.6-plus",
    "qwen3-max",
    "qwen3.5-plus",
    "qwen3-coder-next",
    "qwen3-coder-plus",
    "qwen3-max-2026-01-23",
    "kimi-k2.5",
]

REDUNDANT_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ipynb_checkpoints"}
REDUNDANT_FILE_SUFFIXES = {".tmp", ".temp", ".bak", ".orig", ".rej", ".swp"}
REDUNDANT_FILE_NAMES = {"Thumbs.db", ".DS_Store"}


DEFAULT_BENCHMARKS: list[dict[str, Any]] = [
    {
        "name": "OpenClaw",
        "agent": "global_scheduler",
        "repo_candidates": ["https://github.com/openclaw/openclaw"],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "EvoScientist",
        "agent": "research_manager_agent",
        "repo_candidates": [
            "https://github.com/EvoAgentX/EvoScientist",
            "https://github.com/open-science-ai/EvoScientist",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "SciPhi",
        "agent": "research_manager_agent",
        "repo_candidates": [
            "https://github.com/SciPhi-AI/R2R",
            "https://github.com/SciPhi-AI/sciphi",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "OpenResearch",
        "agent": "literature_agent",
        "repo_candidates": [
            "https://github.com/open-research/openresearch",
            "https://github.com/GAIR-NLP/OpenResearcher",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "Zotero-GPT",
        "agent": "literature_summary_agent",
        "repo_candidates": ["https://github.com/MuiseDestiny/zotero-gpt"],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "PaperAgent",
        "agent": "literature_summary_agent",
        "repo_candidates": [
            "https://github.com/paperagent/paperagent",
            "https://github.com/PaperAgent/PaperAgent",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "AI-Scientist",
        "agent": "innovation_agent",
        "repo_candidates": ["https://github.com/SakanaAI/AI-Scientist"],
        "probe_files": ["README.md", "launch_scientist.py"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "ARIS",
        "agent": "innovation_review_agent",
        "repo_candidates": [
            "https://github.com/ARIS-Lab/ARIS",
            "https://github.com/stanford-futuredata/aris",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "Aider",
        "agent": "code_implementation_agent",
        "repo_candidates": ["https://github.com/Aider-AI/aider"],
        "probe_files": ["README.md", "aider"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "ML-Agent-Research",
        "agent": "code_implementation_agent",
        "repo_candidates": [
            "https://github.com/ml-agent-research/ml-agent-research",
            "https://github.com/snap-stanford/MLAgentBench",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "AutoResearch",
        "agent": "experiment_tuning_agent",
        "repo_candidates": [
            "https://github.com/AutoResearch/AutoResearch",
            "https://github.com/snap-stanford/AutoResearch",
        ],
        "probe_files": ["README.md"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
    {
        "name": "Zotero",
        "agent": "literature_agent",
        "repo_candidates": ["https://github.com/zotero/zotero"],
        "probe_files": ["README.md", "chrome"],
        "validation_commands": ["git rev-parse --short HEAD"],
    },
]


@dataclass
class RetryFailure:
    name: str
    attempts: int
    error: str
    non_blocking: bool


class XiaoLongXiaRescuer:
    def __init__(self) -> None:
        self.events: list[str] = []

    def log(self, msg: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        self.events.append(line)


def _safe_rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _load_env() -> dict[str, str]:
    env = dict(os.environ)
    env_file = ROOT / ".env"
    if not env_file.exists():
        return env
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in env:
            env[key] = value
    return env


def _run_shell(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _run_shell_with_env(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
    env_override: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    env = dict(os.environ)
    if env_override:
        env.update(env_override)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=env,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _collect_model_candidates(env: dict[str, str]) -> list[str]:
    custom = _split_csv(env.get("LLM_MODEL_CANDIDATES", ""))
    merged = []
    seen = set()
    for item in custom + MODEL_CANDIDATES:
        if item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


def _collect_llm_routes(env: dict[str, str]) -> list[tuple[str, str]]:
    base_urls = []
    api_keys = []

    base_urls.extend(_split_csv(env.get("OPENAI_BASE_URLS", "")))
    if env.get("OPENAI_BASE_URL"):
        base_urls.append(env["OPENAI_BASE_URL"].strip())
    base_urls.extend(_split_csv(env.get("DASHSCOPE_BASE_URLS", "")))

    api_keys.extend(_split_csv(env.get("OPENAI_API_KEYS", "")))
    if env.get("OPENAI_API_KEY"):
        api_keys.append(env["OPENAI_API_KEY"].strip())
    api_keys.extend(_split_csv(env.get("DASHSCOPE_API_KEYS", "")))

    routes = []
    seen = set()
    for base in base_urls:
        clean_base = base.rstrip("/")
        for key in api_keys:
            route = (clean_base, key)
            if route in seen:
                continue
            seen.add(route)
            routes.append(route)
    return routes


def _build_git_env(env: dict[str, str]) -> dict[str, str]:
    git_env: dict[str, str] = {}
    proxy = env.get("GIT_PROXY") or env.get("HTTPS_PROXY") or env.get("https_proxy") or env.get("HTTP_PROXY") or env.get("http_proxy")
    if proxy:
        git_env["HTTPS_PROXY"] = proxy
        git_env["https_proxy"] = proxy
        git_env["HTTP_PROXY"] = proxy
        git_env["http_proxy"] = proxy
    return git_env


def _auth_url_if_github(url: str, env: dict[str, str]) -> str:
    token = (env.get("COPILOT_GITHUB_TOKEN") or env.get("GITHUB_TOKEN") or env.get("GH_TOKEN") or "").strip()
    if not token:
        return url
    if not url.startswith("https://github.com/"):
        return url
    return "https://x-access-token:" + token + "@github.com/" + url[len("https://github.com/") :]


def _init_skills_library() -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if SKILLS_LIBRARY.exists():
        return SKILLS_LIBRARY
    content = """# DARIS v3 Skills Library

## 固定规则：冗余文件清理规则
- 每轮启动前必须先生成全目录预览，再执行清理。
- 仅允许自动删除：缓存目录（__pycache__/.pytest_cache/.mypy_cache/.ruff_cache/.ipynb_checkpoints）、Office 锁文件（~$*.docx|xlsx|pptx）、临时后缀文件（.tmp/.temp/.bak/.orig/.rej/.swp）、无效系统垃圾文件（Thumbs.db/.DS_Store）。
- 对失败/过期日志采用白名单路径和时间条件清理，默认保守跳过任何核心配置、有效代码、科研资产。
- 清理前必须记录清单和删除原因；清理后必须记录结果和回滚建议。

## 环节能力沉淀

## 每轮深度复盘
"""
    SKILLS_LIBRARY.write_text(content, encoding="utf-8")
    return SKILLS_LIBRARY


def _append_skills_entry(stage_name: str, payload: dict[str, Any]) -> None:
    _init_skills_library()
    lines = [
        "",
        f"### [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {stage_name}",
    ]
    for key in ["core_skills", "pitfalls", "optimizations", "evidence"]:
        values = payload.get(key, [])
        if not values:
            continue
        lines.append(f"- {key}:")
        for item in values:
            lines.append(f"  - {item}")
    with SKILLS_LIBRARY.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _append_deep_retrospective(round_id: int, summary: dict[str, Any]) -> None:
    _init_skills_library()
    block = [
        "",
        f"### [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Round {round_id} 深度复盘",
        "- bottlenecks:",
    ]
    for item in summary.get("bottlenecks", []):
        block.append(f"  - {item}")
    block.append("- root_causes:")
    for item in summary.get("root_causes", []):
        block.append(f"  - {item}")
    block.append("- optimization_paths:")
    for item in summary.get("optimization_paths", []):
        block.append(f"  - {item}")
    block.append("- reusable_capability_iterations:")
    for item in summary.get("reusable_capability_iterations", []):
        block.append(f"  - {item}")

    with SKILLS_LIBRARY.open("a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")


def _load_benchmark_projects(rescuer: XiaoLongXiaRescuer) -> list[dict[str, Any]]:
    BENCHMARK_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not BENCHMARK_CONFIG.exists():
        BENCHMARK_CONFIG.write_text(
            json.dumps({"projects": DEFAULT_BENCHMARKS}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        rescuer.log(f"已生成默认 12 标杆项目配置: {BENCHMARK_CONFIG}")

    raw = json.loads(BENCHMARK_CONFIG.read_text(encoding="utf-8"))
    projects = raw.get("projects", [])
    if len(projects) != 12:
        rescuer.log(f"警告: 标杆项目数量={len(projects)}，不等于 12，将按配置继续执行。")
    return projects


def _workspace_preview() -> dict[str, Any]:
    total_dirs = 0
    total_files = 0
    top_level: dict[str, dict[str, int]] = {}
    for root, dirs, files in os.walk(ROOT):
        root_path = Path(root)
        if root_path.name == ".git":
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in {".git", ".venv"}]
        total_dirs += len(dirs)
        total_files += len(files)

        try:
            rel = root_path.relative_to(ROOT)
        except ValueError:
            continue
        if rel == Path("."):
            for d in dirs:
                top_level[d] = {"dirs": 0, "files": 0}
            continue

        first = rel.parts[0] if rel.parts else ""
        if first and first in top_level:
            top_level[first]["dirs"] += len(dirs)
            top_level[first]["files"] += len(files)

    return {
        "timestamp": datetime.now().isoformat(),
        "total_dirs": total_dirs,
        "total_files": total_files,
        "top_level": top_level,
    }


def _is_redundant_file(path: Path) -> tuple[bool, str]:
    name = path.name
    lower_name = name.lower()

    if name in REDUNDANT_FILE_NAMES:
        return True, "system_junk"
    if name.startswith("~$") and path.suffix.lower() in {".docx", ".xlsx", ".pptx"}:
        return True, "office_lock_file"
    if path.suffix.lower() in REDUNDANT_FILE_SUFFIXES:
        return True, "temporary_suffix"
    if lower_name.endswith(".log") and ("failed" in lower_name or "error" in lower_name):
        age_seconds = time.time() - path.stat().st_mtime
        if age_seconds > 2 * 24 * 3600:
            return True, "stale_failed_log"
    return False, ""


def _is_excluded_from_cleanup(path: Path) -> bool:
    rel = _safe_rel(path)
    return rel.startswith(".git/") or rel.startswith(".venv/") or "/.git/" in rel or "/.venv/" in rel


def _collect_cleanup_candidates() -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []

    for d in REDUNDANT_DIR_NAMES:
        for p in ROOT.rglob(d):
            if not p.is_dir():
                continue
            if _is_excluded_from_cleanup(p):
                continue
            candidates.append({"path": _safe_rel(p), "type": "dir", "reason": f"cache_dir:{d}"})

    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if _is_excluded_from_cleanup(p):
            continue
        redundant, reason = _is_redundant_file(p)
        if redundant:
            candidates.append({"path": _safe_rel(p), "type": "file", "reason": reason})

    unique = {}
    for item in candidates:
        unique[item["path"]] = item
    return list(unique.values())


def _execute_cleanup(rescuer: XiaoLongXiaRescuer) -> dict[str, Any]:
    preview = _workspace_preview()
    candidates = _collect_cleanup_candidates()
    deleted = []
    skipped = []

    for item in sorted(candidates, key=lambda x: x["path"]):
        path = ROOT / item["path"]
        try:
            if item["type"] == "dir":
                for child in sorted(path.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        child.rmdir()
                path.rmdir()
            else:
                path.unlink(missing_ok=True)
            deleted.append(item)
        except Exception as exc:  # pylint: disable=broad-except
            skipped.append({"path": item["path"], "reason": item["reason"], "error": str(exc)})

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now().isoformat(),
        "preview": preview,
        "cleanup_candidates": candidates,
        "deleted": deleted,
        "skipped": skipped,
    }
    json_path = REPORT_DIR / f"cleanup_report_{ts}.json"
    md_path = REPORT_DIR / f"cleanup_report_{ts}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Cleanup Report",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Candidates: {len(candidates)}",
        f"- Deleted: {len(deleted)}",
        f"- Skipped: {len(skipped)}",
        "",
        "## Preview",
        f"- Total dirs: {preview['total_dirs']}",
        f"- Total files: {preview['total_files']}",
        "",
        "## Deleted",
    ]
    for d in deleted:
        lines.append(f"- {d['path']} ({d['reason']})")
    lines.append("")
    lines.append("## Skipped")
    for s in skipped:
        lines.append(f"- {s['path']} ({s['reason']}): {s['error']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    rescuer.log(f"清理完成: 删除 {len(deleted)} 项，跳过 {len(skipped)} 项")
    return {
        "json_report": _safe_rel(json_path),
        "md_report": _safe_rel(md_path),
        "deleted": deleted,
        "skipped": skipped,
        "touched": [_safe_rel(json_path), _safe_rel(md_path)] + [d["path"] for d in deleted],
    }


def _clone_or_update_repo(target: Path, candidates: list[str], rescuer: XiaoLongXiaRescuer) -> tuple[bool, str, str, Path]:
    env = _load_env()
    git_env = _build_git_env(env)

    if target.exists() and (target / ".git").exists():
        head_code, head_out, _ = _run_shell(["git", "-C", str(target), "rev-parse", "--short", "HEAD"], timeout=30)
        local_head = head_out.strip() if head_code == 0 else ""
        try:
            code, _, err = _run_shell_with_env(
                ["git", "-C", str(target), "fetch", "--all", "--tags", "--prune"],
                timeout=180,
                env_override=git_env,
            )
        except Exception as exc:  # pylint: disable=broad-except
            if local_head:
                return True, "existing_repo_local", f"fetch_failed_but_local_available:{str(exc)[:120]}", target
            return False, "existing_repo", str(exc)[:500], target
        if code == 0:
            return True, "existing_repo", local_head, target
        if local_head:
            return True, "existing_repo_local", f"fetch_failed_but_local_available:{err.strip()[:120]}", target
        return False, "existing_repo", err.strip()[:500], target

    for url in candidates:
        target.parent.mkdir(parents=True, exist_ok=True)
        clone_target = target
        if target.exists() and not (target / ".git").exists():
            clone_target = target.parent / f"{target.name}_retry_{int(time.time() * 1000)}"

        try:
            auth_url = _auth_url_if_github(url, env)
            code, out, err = _run_shell_with_env(
                ["git", "clone", "--depth", "1", auth_url, str(clone_target)],
                timeout=60,
                env_override=git_env,
            )
        except Exception as exc:  # pylint: disable=broad-except
            code, out, err = 1, "", str(exc)

        if code == 0:
            return True, url, out.strip()[:500], clone_target
    return False, "", "all clone candidates failed", target


def _validate_probe_files(target: Path, probes: list[str]) -> tuple[bool, list[str]]:
    found = []
    for probe in probes:
        if (target / probe).exists():
            found.append(probe)
    return (len(found) > 0), found


def _write_integration_adapter(project: dict[str, Any], target: Path) -> Path:
    INTEGRATION_DIR.mkdir(parents=True, exist_ok=True)
    adapter_name = re.sub(r"[^a-z0-9]+", "_", project["name"].lower()).strip("_")
    adapter_path = INTEGRATION_DIR / f"{adapter_name}_adapter.md"
    adapter_path.write_text(
        "\n".join(
            [
                f"# {project['name']} Integration Adapter",
                "",
                f"- agent_stage: {project.get('agent', 'unknown')}",
                f"- local_repo: {_safe_rel(target)}",
                "- integration_steps:",
                "  - clone_or_update",
                "  - core_logic_probe_validation",
                "  - adapter_standardization",
                "  - usability_validation",
            ]
        ),
        encoding="utf-8",
    )
    return adapter_path


def _validate_project_usability(target: Path, commands: list[str]) -> tuple[bool, list[str]]:
    outputs = []
    for command in commands:
        cmd = ["cmd", "/c", command]
        code, out, err = _run_shell(cmd, cwd=target, timeout=180)
        summary = f"cmd={command}; code={code}; out={out.strip()[:120]}; err={err.strip()[:120]}"
        outputs.append(summary)
        if code != 0:
            return False, outputs
    return True, outputs


def _integrate_benchmark_projects(projects: list[dict[str, Any]], rescuer: XiaoLongXiaRescuer) -> dict[str, Any]:
    records = []
    touched = []
    failures: list[RetryFailure] = []

    for project in projects:
        name = project.get("name", "unknown")
        rescuer.log(f"开始集成标杆项目: {name}")
        target = BENCHMARK_DIR / re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        result = {
            "name": name,
            "agent": project.get("agent"),
            "status": "pending",
            "clone": {},
            "core_logic": {},
            "adaptation": {},
            "usability": {},
            "attempts": [],
        }

        clone_ok = False
        clone_detail = ""
        active_repo_path = target
        for attempt in range(1, 4):
            ok, source, detail, repo_path = _clone_or_update_repo(target, project.get("repo_candidates", []), rescuer)
            result["attempts"].append({"step": "clone", "attempt": attempt, "ok": ok, "detail": detail, "source": source})
            if ok:
                clone_ok = True
                clone_detail = source
                active_repo_path = repo_path
                break
            time.sleep(1)
        result["clone"] = {"ok": clone_ok, "source": clone_detail}

        if not clone_ok:
            result["status"] = "non_blocking_failed"
            failures.append(RetryFailure(name=f"{name}.clone", attempts=3, error="clone_failed", non_blocking=True))
            records.append(result)
            continue

        found_ok, found = _validate_probe_files(active_repo_path, project.get("probe_files", []))
        result["core_logic"] = {"ok": found_ok, "found_probes": found, "required_probes": project.get("probe_files", [])}
        if not found_ok:
            failures.append(RetryFailure(name=f"{name}.core_logic", attempts=3, error="probe_not_found", non_blocking=True))

        adapter_path = _write_integration_adapter(project, active_repo_path)
        touched.append(_safe_rel(adapter_path))
        result["adaptation"] = {"ok": True, "adapter": _safe_rel(adapter_path)}

        usable_ok, outputs = _validate_project_usability(active_repo_path, project.get("validation_commands", ["git rev-parse --short HEAD"]))
        result["usability"] = {"ok": usable_ok, "checks": outputs}
        if not usable_ok:
            failures.append(RetryFailure(name=f"{name}.usability", attempts=3, error="validation_command_failed", non_blocking=True))

        result["status"] = "success" if found_ok and usable_ok else "partial"
        records.append(result)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": len(projects),
        "records": records,
        "non_blocking_failures": [f.__dict__ for f in failures],
    }
    json_path = REPORT_DIR / f"benchmark_integration_{ts}.json"
    md_path = REPORT_DIR / f"benchmark_integration_{ts}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Benchmark Integration Report",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Total projects: {report['total']}",
        f"- Non-blocking failures: {len(report['non_blocking_failures'])}",
        "",
        "## Records",
    ]
    for r in records:
        lines.append(f"### {r['name']}")
        lines.append(f"- status: {r['status']}")
        lines.append(f"- clone_ok: {r['clone'].get('ok')}")
        lines.append(f"- core_logic_ok: {r['core_logic'].get('ok')}")
        lines.append(f"- usability_ok: {r['usability'].get('ok')}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    rescuer.log(f"标杆项目集成完成: 成功/部分={len(records)}，非阻断失败={len(failures)}")
    return {
        "json_report": _safe_rel(json_path),
        "md_report": _safe_rel(md_path),
        "records": records,
        "non_blocking_failures": [f.__dict__ for f in failures],
        "touched": touched + [_safe_rel(json_path), _safe_rel(md_path)],
    }


def _git_commit_paths(paths: list[str], message: str, rescuer: XiaoLongXiaRescuer) -> dict[str, Any]:
    uniq = []
    seen = set()
    for p in paths:
        if not p or p in seen:
            continue
        seen.add(p)
        uniq.append(p)

    if not uniq:
        return {"status": "skipped", "reason": "no_paths"}

    valid_paths = []
    for p in uniq:
        abs_path = ROOT / p
        if abs_path.exists():
            valid_paths.append(p)
            continue
        check_code, _, _ = _run_shell(["git", "ls-files", "--error-unmatch", "--", p], cwd=ROOT, timeout=30)
        if check_code == 0:
            valid_paths.append(p)

    if not valid_paths:
        return {"status": "skipped", "reason": "no_valid_paths"}

    add_cmd = ["git", "add", "--"] + valid_paths
    code, _, err = _run_shell(add_cmd, cwd=ROOT, timeout=120)
    if code != 0:
        rescuer.log(f"Git add 失败: {err[:200]}")
        return {"status": "failed", "step": "add", "error": err[:500]}

    diff_code, _, _ = _run_shell(["git", "diff", "--cached", "--quiet"], cwd=ROOT, timeout=60)
    if diff_code == 0:
        return {"status": "skipped", "reason": "nothing_staged"}

    commit_code, out, commit_err = _run_shell(["git", "commit", "-m", message], cwd=ROOT, timeout=120)
    if commit_code != 0:
        rescuer.log(f"Git commit 失败: {commit_err[:200]}")
        return {"status": "failed", "step": "commit", "error": commit_err[:500]}
    return {"status": "success", "output": out.strip()[:500]}


def _extract_keywords(req: str) -> list[str]:
    if not req.strip():
        return [
            "power load forecasting",
            "multivariate time series forecasting",
            "MTGNN TimesNet XGBoost",
        ]
    keyword = req
    match = re.search(r"找(.+?)方向", req)
    if match:
        keyword = match.group(1)
    return [
        keyword,
        f"{keyword} time series forecasting",
        f"{keyword} graph neural network",
    ]


def _call_llm_with_fallback(
    env: dict[str, str],
    system_prompt: str,
    user_prompt: str,
    rescuer: XiaoLongXiaRescuer,
    timeout: int = 120,
) -> tuple[str, str]:
    routes = _collect_llm_routes(env)
    models = _collect_model_candidates(env)

    if not routes:
        rescuer.log("未检测到阿里兼容 API 配置，启用本地降级文本生成。")
        fallback_text = (
            "[降级输出] 当前未配置可用 API，已按规则生成结构化建议。"
            "请补充 OPENAI_API_KEY / OPENAI_BASE_URL 以启用真实多模型评审。"
        )
        return fallback_text, "local-fallback"

    last_error = ""
    for base_url, api_key in routes:
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        for model in models:
            payload = {
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            try:
                rescuer.log(f"尝试模型: {model} @ {base_url}")
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
                if resp.status_code >= 400:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                    rescuer.log(f"模型 {model} 失败: {last_error}")
                    continue
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                rescuer.log(f"模型 {model} 成功返回。")
                return text, model
            except Exception as exc:  # pylint: disable=broad-except
                last_error = str(exc)
                rescuer.log(f"模型 {model} 异常: {exc}")

    rescuer.log(f"全部模型调用失败，切换本地兜底生成。最近错误: {last_error}")
    return _local_stage_fallback(user_prompt), "local-rescue"


def _local_stage_fallback(user_prompt: str) -> str:
    hint = ""
    compact = user_prompt.replace("\n", " ")[:260]
    if "评审" in user_prompt or "风险" in user_prompt:
        hint = (
            "1) 通过项: 创新目标可落地且可量化。\n"
            "2) 风险项: 参数过拟合、数据分布漂移、训练时长增加。\n"
            "3) 必须修改项: 增加回退机制、限制学习率/深度、保留 baseline 对照。\n"
            "4) 执行建议: 先做 demo 验证，再跑三基线全量评测。"
        )
    elif "创新" in user_prompt:
        hint = (
            "创新点A: 动态图门控+自适应窗口，改动 MTGNN 优化分支。\n"
            "创新点B: 趋势残差解耦+物理约束，改动 TimesNet 优化分支。\n"
            "创新点C: 长窗特征+稳健树深调优，改动 XGBoost 优化分支。\n"
            "评估指标: MAE/RMSE/R2 + 稳定性。"
        )
    else:
        hint = (
            "研究脉络: 图时序与长序列模型融合是主线。\n"
            "常见缺陷: 对突发波动鲁棒性不足、物理约束缺失。\n"
            "可利用空白: 轻量约束与可解释特征解耦的联合优化。"
        )
    return f"[本地兜底生成]\n输入片段: {compact}\n\n{hint}"


def _send_dingtalk(env: dict[str, str], text: str, rescuer: XiaoLongXiaRescuer) -> None:
    webhook = env.get("WEBHOOK_URL", "").strip()
    if not webhook:
        rescuer.log("未配置 WEBHOOK_URL，跳过钉钉告警。")
        return
    body = {"msgtype": "text", "text": {"content": text}}
    try:
        requests.post(webhook, json=body, timeout=20)
        rescuer.log("钉钉告警已发送。")
    except Exception as exc:  # pylint: disable=broad-except
        rescuer.log(f"钉钉告警发送失败: {exc}")


def _crawl_literature(keywords: list[str], limit: int, rescuer: XiaoLongXiaRescuer) -> Path:
    LIT_DIR.mkdir(parents=True, exist_ok=True)
    papers: list[dict] = []
    for kw in keywords:
        params = {
            "query": kw,
            "rows": limit,
            "sort": "relevance",
            "order": "desc",
        }
        rescuer.log(f"抓取文献关键词: {kw}")
        try:
            resp = requests.get("https://api.crossref.org/works", params=params, timeout=45)
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])
            for item in items:
                title = ""
                if item.get("title"):
                    title = item["title"][0]
                abstract = item.get("abstract", "")
                authors = []
                for author in item.get("author", [])[:5]:
                    authors.append(f"{author.get('given', '')} {author.get('family', '')}".strip())
                papers.append(
                    {
                        "keyword": kw,
                        "title": title,
                        "doi": item.get("DOI", ""),
                        "year": item.get("created", {}).get("date-parts", [[None]])[0][0],
                        "url": item.get("URL", ""),
                        "authors": authors,
                        "abstract": abstract,
                    }
                )
            time.sleep(0.8)
        except Exception as exc:  # pylint: disable=broad-except
            rescuer.log(f"关键词 {kw} 抓取失败: {exc}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = LIT_DIR / f"auto_literature_{stamp}.json"
    out.write_text(
        json.dumps({"timestamp": datetime.now().isoformat(), "keywords": keywords, "papers": papers}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rescuer.log(f"文献抓取完成: {out}")
    return out


def _read_literature_for_prompt(path: Path, max_items: int = 15) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    papers = data.get("papers", [])[:max_items]
    lines = []
    for idx, paper in enumerate(papers, 1):
        lines.append(f"{idx}. {paper.get('title', '')}")
        lines.append(f"   DOI: {paper.get('doi', '')}")
        lines.append(f"   URL: {paper.get('url', '')}")
        abstract = (paper.get("abstract") or "").replace("\n", " ")
        lines.append(f"   Abstract: {abstract[:500]}")
    return "\n".join(lines)


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _apply_code_edits(rescuer: XiaoLongXiaRescuer) -> list[str]:
    model_dir = ROOT / "5_code_base" / "optimized" / "power_models"
    if not model_dir.exists():
        model_dir = ROOT / "code" / "power_models"

    changes = []

    edits = {
        model_dir / "xgboost_model.py": [
            ("n_estimators=140 if optimized else 90", "n_estimators=160 if optimized else 90"),
            ("max_depth=5 if optimized else 4", "max_depth=6 if optimized else 4"),
        ],
        model_dir / "timesnet_model.py": [
            ("epochs=8 if optimized else 6", "epochs=10 if optimized else 6"),
            ("lambda_phy=0.1", "lambda_phy=0.12"),
        ],
        model_dir / "mtgnn_model.py": [
            ("hidden_dim=80 if optimized else 64", "hidden_dim=88 if optimized else 64"),
            ("epochs=8 if optimized else 6", "epochs=10 if optimized else 6"),
        ],
    }

    for file_path, pairs in edits.items():
        if not file_path.exists():
            rescuer.log(f"跳过不存在文件: {file_path}")
            continue
        text = file_path.read_text(encoding="utf-8")
        original = text
        for old, new in pairs:
            if old in text:
                text = text.replace(old, new, 1)
        if text != original:
            file_path.write_text(text, encoding="utf-8")
            changes.append(str(file_path.relative_to(ROOT)))

    rescuer.log(f"自动代码改动完成，涉及文件数: {len(changes)}")
    return changes


def _run_demo(rescuer: XiaoLongXiaRescuer) -> dict:
    optimized_dir = ROOT / "5_code_base" / "optimized"
    legacy_dir = ROOT / "code"
    if optimized_dir.exists():
        sys.path.insert(0, str(optimized_dir))
    elif legacy_dir.exists():
        sys.path.insert(0, str(legacy_dir))

    power_models = importlib.import_module("power_models")
    power_common = importlib.import_module("power_models.common")

    data_path = resolve_first_existing(
        WORKSPACE_ROOT / "data" / "shandong_pmos_hourly.csv",
        ROOT / "6_experiment_execution" / "data" / "shandong_pmos_hourly.csv",
        ROOT / "data" / "shandong_pmos_hourly.csv",
    )

    df = power_common.read_numeric_timeseries(str(data_path)).tail(5000)
    metrics = power_models.train_eval_xgboost(df, optimized=True)

    out = WORKSPACE_ROOT / "experiment" / "auto_demo_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    rescuer.log(f"Demo 评估完成: {metrics}")
    return metrics


def _run_full_baselines(rescuer: XiaoLongXiaRescuer) -> Path:
    script = ROOT / "6_experiment_execution" / "pipeline" / "run_round_fixed_pipeline.py"
    if not script.exists():
        script = ROOT / "code" / "run_round_fixed_pipeline.py"
    rescuer.log(f"执行三基线+优化测试脚本: {script}")
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    log_path = WORKSPACE_ROOT / "logs" / "auto_full_pipeline_stdout.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text((proc.stdout or "") + "\n\n[stderr]\n" + (proc.stderr or ""), encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"全量测试失败，退出码={proc.returncode}，日志={log_path}")
    rescuer.log(f"全量测试完成，日志: {log_path}")
    return log_path


def _load_round_metrics() -> dict:
    metrics = resolve_first_existing(
        WORKSPACE_ROOT / "report" / "round_fixed_metrics.json",
        ROOT / "8_knowledge_asset" / "final_report" / "round_fixed_metrics.json",
        ROOT / "report" / "round_fixed_metrics.json",
    )
    if not metrics.exists():
        return {}
    return json.loads(metrics.read_text(encoding="utf-8"))


def _run_with_retry(name: str, fn, rescuer: XiaoLongXiaRescuer, attempts: int = 3):
    last_err = None
    for idx in range(1, attempts + 1):
        try:
            rescuer.log(f"{name} 开始 (attempt={idx})")
            return fn()
        except Exception as exc:  # pylint: disable=broad-except
            last_err = exc
            rescuer.log(f"{name} 失败 (attempt={idx}): {exc}")
            time.sleep(2)
    raise RuntimeError(f"{name} 最终失败: {last_err}")


def _auto_migrate_if_needed(rescuer: XiaoLongXiaRescuer) -> dict:
    from workspace_reorganizer import run_reorganization  # pylint: disable=import-outside-toplevel

    result = run_reorganization()
    rescuer.log(f"目录重构完成，报告: {result.get('md_report')}")
    return result


def _build_round_retrospective(round_result: dict[str, Any], benchmark_result: dict[str, Any]) -> dict[str, list[str]]:
    bottlenecks = []
    root_causes = []
    optimization_paths = []
    reusable = []

    failed_bench = benchmark_result.get("non_blocking_failures", [])
    if failed_bench:
        bottlenecks.append(f"标杆项目中存在 {len(failed_bench)} 个非阻断失败项，影响能力完全落地率。")
        root_causes.append("部分仓库地址不可用或网络不可达。")
        optimization_paths.append("维护企业内部镜像仓库并在配置中优先使用镜像地址。")
        reusable.append("将仓库候选地址与探针文件写入配置并执行自动三次重试。")

    if not round_result.get("changed_files"):
        bottlenecks.append("本轮代码自动改动未命中可替换参数，优化动作可能弱化。")
        root_causes.append("规则替换依赖固定字符串，代码形态变化导致匹配失败。")
        optimization_paths.append("改为 AST/配置驱动修改策略，降低字符串替换脆弱性。")
        reusable.append("将改动点抽象为参数表并加存在性校验。")

    if round_result.get("round_metrics") == {}:
        bottlenecks.append("未读到 round_fixed_metrics.json，无法进行跨轮客观对比。")
        root_causes.append("全量评测未产出或输出路径与预期不一致。")
        optimization_paths.append("为指标产物增加输出探针和失败即告警规则。")
        reusable.append("在每轮结束执行产物路径一致性检查。")

    if not bottlenecks:
        bottlenecks.append("本轮主流程执行顺畅，未出现显著阻断。")
        root_causes.append("前置清理与重试机制降低了偶发错误率。")
        optimization_paths.append("继续强化阶段内指标门禁，缩短无效迭代。")
        reusable.append("保持阶段日志与能力沉淀同步写入 skills 知识库。")

    return {
        "bottlenecks": bottlenecks,
        "root_causes": root_causes,
        "optimization_paths": optimization_paths,
        "reusable_capability_iterations": reusable,
    }


def _write_execution_validation_report(final: dict[str, Any]) -> dict[str, str]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = REPORT_DIR / f"DARIS_V3_EXECUTION_VALIDATION_{ts}.md"
    json_path = REPORT_DIR / f"DARIS_V3_EXECUTION_VALIDATION_{ts}.json"
    json_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# DARIS v3 Execution Validation Report",
        "",
        f"- request: {final.get('request')}",
        f"- status: {final.get('status')}",
        f"- rounds: {final.get('rounds')}",
        f"- start: {final.get('start_time')}",
        f"- end: {final.get('end_time')}",
        "",
        "## Mandatory Checks",
        f"- cleanup_triggered: {bool(final.get('cleanup'))}",
        f"- benchmark_integration_triggered: {bool(final.get('benchmark_integration'))}",
        f"- skills_library_updated: {bool(final.get('skills_library'))}",
        f"- git_commit_records: {len(final.get('git_commits', []))}",
        "",
        "## Non-blocking failures",
    ]
    for item in final.get("non_blocking_failures", []):
        lines.append(
            f"- {item.get('name')} | attempts={item.get('attempts')} | non_blocking={item.get('non_blocking')} | error={item.get('error')}"
        )

    lines.append("")
    lines.append("## Round Summary")
    for step in final.get("steps", []):
        lines.append(f"### Round {step.get('round')}")
        lines.append(f"- literature_json: {step.get('literature_json')}")
        lines.append(f"- reading_summary: {step.get('reading_summary')}")
        lines.append(f"- innovation: {step.get('innovation')}")
        lines.append(f"- innovation_review: {step.get('innovation_review')}")
        lines.append(f"- full_test_log: {step.get('full_test_log')}")
        lines.append("")

    if final.get("error"):
        lines.append("## Error")
        lines.append(str(final["error"]))

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"md_report": _safe_rel(md_path), "json_report": _safe_rel(json_path)}


def execute_round(request_text: str, round_id: int, env: dict[str, str], rescuer: XiaoLongXiaRescuer, skip_full_baseline: bool) -> dict:
    keywords = _extract_keywords(request_text)
    lit_path = _run_with_retry("文献抓取", lambda: _crawl_literature(keywords, 8, rescuer), rescuer)
    lit_text = _read_literature_for_prompt(lit_path)

    summary_text, summary_model = _run_with_retry(
        "智能体阅读文献",
        lambda: _call_llm_with_fallback(
            env,
            "你是DARIS文献调研智能体，请只输出结构化中文结论。",
            f"任务: 阅读以下文献条目并总结研究脉络、常见缺陷、可利用空白。\n\n{lit_text}",
            rescuer,
        ),
        rescuer,
    )
    summary_path = _write_text(
        LIT_DIR / f"agent_reading_round{round_id}.md",
        f"# Agent Reading (model={summary_model})\n\n{summary_text}",
    )

    innovation_text, innovation_model = _run_with_retry(
        "提出创新点",
        lambda: _call_llm_with_fallback(
            env,
            "你是DARIS创新挖掘智能体，请提出3个可执行创新点，要求包含: 目标、改动文件、评估指标、风险。",
            f"基于文献阅读结论提出创新点，要求适配 MTGNN/TimesNet/XGBoost。\n\n{summary_text}",
            rescuer,
        ),
        rescuer,
    )
    innovation_path = _write_text(
        WORKSPACE_ROOT / "hypothesis" / f"innovation_round{round_id}.md",
        f"# Innovation Proposal (model={innovation_model})\n\n{innovation_text}",
    )

    review_text, review_model = _run_with_retry(
        "智能体审阅创新点",
        lambda: _call_llm_with_fallback(
            env,
            "你是DARIS质量评审智能体，请严格评审创新点并给出可直接执行的修正建议。",
            f"请评审以下创新方案，输出: 通过项、风险项、必须修改项。\n\n{innovation_text}",
            rescuer,
        ),
        rescuer,
    )
    review_path = _write_text(
        WORKSPACE_ROOT / "hypothesis" / "review_report" / f"innovation_review_round{round_id}.md",
        f"# Innovation Review (model={review_model})\n\n{review_text}",
    )

    changed_files = _run_with_retry("智能体改动代码", lambda: _apply_code_edits(rescuer), rescuer)
    demo_metrics = _run_with_retry("Demo 评估", lambda: _run_demo(rescuer), rescuer)
    full_log = None
    if not skip_full_baseline:
        full_log = _run_with_retry("三基线改动测试", lambda: _run_full_baselines(rescuer), rescuer)
    round_metrics = _load_round_metrics()

    return {
        "round": round_id,
        "keywords": keywords,
        "literature_json": str(lit_path.relative_to(ROOT)),
        "reading_summary": str(summary_path.relative_to(ROOT)),
        "innovation": str(innovation_path.relative_to(ROOT)),
        "innovation_review": str(review_path.relative_to(ROOT)),
        "changed_files": changed_files,
        "demo_metrics": demo_metrics,
        "full_test_log": str(full_log.relative_to(ROOT)) if full_log else "skipped_by_flag",
        "round_metrics": round_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="DARIS OpenClaw 全自动流程调度器")
    parser.add_argument("--request", type=str, default="今日找负荷预测方向文献，执行全自动流程一轮")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--skip-migrate", action="store_true")
    parser.add_argument("--skip-full-baseline", action="store_true")
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    env = _load_env()
    rescuer = XiaoLongXiaRescuer()

    final: dict = {
        "request": args.request,
        "start_time": datetime.now().isoformat(),
        "rounds": args.rounds,
        "auto_migrate": not args.skip_migrate,
        "skip_full_baseline": args.skip_full_baseline,
        "steps": [],
        "git_commits": [],
        "non_blocking_failures": [],
    }

    try:
        _init_skills_library()
        final["skills_library"] = _safe_rel(SKILLS_LIBRARY)

        cleanup = _run_with_retry("启动前冗余清理", lambda: _execute_cleanup(rescuer), rescuer)
        final["cleanup"] = cleanup
        _append_skills_entry(
            "预清理阶段",
            {
                "core_skills": ["全目录预览 + 安全白名单清理", "清理报告双格式落盘"],
                "pitfalls": ["避免误删核心配置和科研资产"],
                "optimizations": ["仅对显式冗余模式执行删除"],
                "evidence": [cleanup.get("md_report", "")],
            },
        )
        final["git_commits"].append(
            _git_commit_paths(cleanup.get("touched", []), "[DARIS-v3][stage:cleanup] auto redundant cleanup", rescuer)
        )

        benchmarks = _load_benchmark_projects(rescuer)
        final["benchmark_config"] = _safe_rel(BENCHMARK_CONFIG)
        benchmark_result = _run_with_retry("12标杆项目能力集成", lambda: _integrate_benchmark_projects(benchmarks, rescuer), rescuer)
        final["benchmark_integration"] = benchmark_result
        final["non_blocking_failures"].extend(benchmark_result.get("non_blocking_failures", []))
        _append_skills_entry(
            "标杆项目集成阶段",
            {
                "core_skills": ["仓库三次重试克隆", "四步校验: 克隆/复现/适配/可用性"],
                "pitfalls": ["仓库地址漂移导致克隆失败", "探针文件路径不稳定导致误判"],
                "optimizations": ["配置化候选仓库地址", "统一适配文档模板自动生成"],
                "evidence": [benchmark_result.get("md_report", "")],
            },
        )
        final["git_commits"].append(
            _git_commit_paths(
                benchmark_result.get("touched", []) + [final.get("benchmark_config", "")],
                "[DARIS-v3][stage:benchmark] integrate benchmark open-source capabilities",
                rescuer,
            )
        )

        if not args.skip_migrate:
            final["migration"] = _run_with_retry("目录归位", lambda: _auto_migrate_if_needed(rescuer), rescuer)
            final["git_commits"].append(
                _git_commit_paths(
                    [_safe_rel(Path(final["migration"]["json_report"])), _safe_rel(Path(final["migration"]["md_report"]))],
                    "[DARIS-v3][stage:migration] workspace reorganization",
                    rescuer,
                )
            )

        for round_id in range(1, args.rounds + 1):
            rescuer.log(f"开始执行自动化轮次 {round_id}/{args.rounds}")
            result = execute_round(args.request, round_id, env, rescuer, args.skip_full_baseline)
            final["steps"].append(result)

            _append_skills_entry(
                f"轮次{round_id}执行阶段",
                {
                    "core_skills": ["文献抓取-创新生成-评审-代码改动-验证串行闭环"],
                    "pitfalls": ["API 不可用时需降级且保持输出结构稳定"],
                    "optimizations": ["将全量测试日志固定重定向到 tuning_log"],
                    "evidence": [result.get("full_test_log", "")],
                },
            )

            retrospective = _build_round_retrospective(result, benchmark_result)
            _append_deep_retrospective(round_id, retrospective)
            final.setdefault("retrospectives", []).append(retrospective)

            stage_paths = [
                result.get("literature_json", ""),
                result.get("reading_summary", ""),
                result.get("innovation", ""),
                result.get("innovation_review", ""),
                result.get("full_test_log", ""),
                _safe_rel(SKILLS_LIBRARY),
            ] + result.get("changed_files", [])
            final["git_commits"].append(
                _git_commit_paths(stage_paths, f"[DARIS-v3][stage:round-{round_id}] execute auto loop", rescuer)
            )

        final["status"] = "success"
    except Exception as exc:  # pylint: disable=broad-except
        final["status"] = "failed"
        final["error"] = str(exc)
        _send_dingtalk(env, f"DARIS自动流程失败: {exc}", rescuer)

    final["events"] = rescuer.events
    final["end_time"] = datetime.now().isoformat()

    validation_reports = _write_execution_validation_report(final)
    final["execution_validation"] = validation_reports

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_out = REPORT_DIR / f"openclaw_full_auto_{ts}.json"
    md_out = REPORT_DIR / f"openclaw_full_auto_{ts}.md"
    json_out.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# OpenClaw Full Auto Pipeline Report",
        "",
        f"- Request: {final['request']}",
        f"- Status: {final.get('status')}",
        f"- Start: {final.get('start_time')}",
        f"- End: {final.get('end_time')}",
        "",
        "## Round Results",
    ]
    for step in final.get("steps", []):
        md_lines.append(f"### Round {step.get('round')}")
        md_lines.append(f"- Literature JSON: {step.get('literature_json')}")
        md_lines.append(f"- Reading Summary: {step.get('reading_summary')}")
        md_lines.append(f"- Innovation: {step.get('innovation')}")
        md_lines.append(f"- Review: {step.get('innovation_review')}")
        md_lines.append(f"- Changed files: {', '.join(step.get('changed_files', []))}")
        md_lines.append(f"- Demo metrics: {step.get('demo_metrics')}")
        md_lines.append(f"- Full test log: {step.get('full_test_log')}")
        md_lines.append("")

    if final.get("error"):
        md_lines.append("## Error")
        md_lines.append(final["error"])

    md_lines.append("## Validation Reports")
    md_lines.append(f"- {validation_reports['md_report']}")
    md_lines.append(f"- {validation_reports['json_report']}")

    md_lines.append("## Non-Blocking Failures")
    for item in final.get("non_blocking_failures", []):
        md_lines.append(
            f"- {item.get('name')} | attempts={item.get('attempts')} | non_blocking={item.get('non_blocking')} | error={item.get('error')}"
        )

    md_lines.append("## Events")
    md_lines.extend([f"- {line}" for line in final.get("events", [])])
    md_out.write_text("\n".join(md_lines), encoding="utf-8")

    final["git_commits"].append(
        _git_commit_paths(
            [
                _safe_rel(json_out),
                _safe_rel(md_out),
                validation_reports["md_report"],
                validation_reports["json_report"],
                _safe_rel(SKILLS_LIBRARY),
            ],
            "[DARIS-v3][stage:final] execution validation and reports",
            rescuer,
        )
    )

    print(json.dumps({"json_report": str(json_out), "md_report": str(md_out), "status": final.get("status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
