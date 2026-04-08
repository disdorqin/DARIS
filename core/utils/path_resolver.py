from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parents[2]
CURRENT_WORKSPACE_FILE = ROOT / ".current_workspace"
CURRENT_WORKSPACE_BAK_FILE = ROOT / ".current_workspace.bak"
WORKSPACES_ROOT = ROOT / "workspaces"
CORE_ROOT = ROOT / "core"
WORKSPACE_INDEX_FILE = WORKSPACES_ROOT / "workspace_index.json"
DEFAULT_WORKSPACE_NAME = "workspace_default"


def _normalize_workspace_name(workspace_name: str | None) -> str:
    name = (workspace_name or "").strip()
    if not name:
        return DEFAULT_WORKSPACE_NAME
    if name.startswith("workspace_"):
        return name
    return f"workspace_{name}"


def _read_current_workspace_name() -> str:
    if not CURRENT_WORKSPACE_FILE.exists():
        raise FileNotFoundError(f"missing workspace anchor: {CURRENT_WORKSPACE_FILE}")
    workspace_name = CURRENT_WORKSPACE_FILE.read_text(encoding="utf-8").strip()
    normalized = _normalize_workspace_name(workspace_name)
    workspace_root = WORKSPACES_ROOT / normalized
    if not workspace_root.exists():
        raise FileNotFoundError(f"workspace root not found: {workspace_root}")
    return normalized


CURRENT_WORKSPACE_NAME = _read_current_workspace_name()
CURRENT_WORKSPACE_ROOT = WORKSPACES_ROOT / CURRENT_WORKSPACE_NAME


def get_core_path(*relative_parts: str) -> Path:
    """返回 core/ 下的路径，只读使用。"""
    return CORE_ROOT.joinpath(*relative_parts)


def get_workspace_path(sub_dir: str = "") -> Path:
    """返回当前激活主题目录下的路径。"""
    if not sub_dir:
        return CURRENT_WORKSPACE_ROOT
    return CURRENT_WORKSPACE_ROOT.joinpath(sub_dir)


def validate_write_path(path: str | Path) -> Path:
    """确保写入路径位于当前工作区内。"""
    candidate = Path(path).resolve()
    workspace_root = CURRENT_WORKSPACE_ROOT.resolve()
    try:
        candidate.relative_to(workspace_root)
    except ValueError as exc:
        raise PermissionError(f"write path خارج current workspace: {candidate}") from exc
    return candidate


def _parse_content(path: Path, content: str) -> Any:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"} and yaml is not None:
        return yaml.safe_load(content) or {}
    if suffix == ".json":
        return json.loads(content)
    return content


def get_workspace_config(config_name: str) -> Any:
    """读取当前主题 config/ 下的配置文件。"""
    config_name = config_name.strip().lstrip("/").replace("\\", "/")
    candidate_paths = [
        CURRENT_WORKSPACE_ROOT / "config" / config_name,
        CURRENT_WORKSPACE_ROOT / "config" / "base" / config_name,
        CURRENT_WORKSPACE_ROOT / "config" / "research" / config_name,
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return _parse_content(candidate, candidate.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"workspace config not found: {config_name}")


def get_memory_path(memory_type: str = "") -> Path:
    """返回当前主题 memory/ 目录下的路径。"""
    memory_type = memory_type.strip().lstrip("/").replace("\\", "/")
    if not memory_type:
        return CURRENT_WORKSPACE_ROOT / "memory"
    return CURRENT_WORKSPACE_ROOT / "memory" / memory_type


def load_workspace_index() -> dict[str, Any]:
    """读取全局主题索引。"""
    if not WORKSPACE_INDEX_FILE.exists():
        return {"version": "1.0", "workspaces": [], "current_active": ""}
    return json.loads(WORKSPACE_INDEX_FILE.read_text(encoding="utf-8"))


def save_workspace_index(index_data: dict[str, Any]) -> None:
    WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
    WORKSPACE_INDEX_FILE.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_workspace_index(workspace_meta: dict[str, Any]) -> None:
    index_data = load_workspace_index()
    items = [item for item in index_data.get("workspaces", []) if item.get("workspace_id") != workspace_meta.get("workspace_id")]
    items.append(workspace_meta)
    index_data["workspaces"] = items
    save_workspace_index(index_data)


def update_current_workspace(workspace_name: str) -> None:
    normalized = _normalize_workspace_name(workspace_name)
    CURRENT_WORKSPACE_FILE.write_text(f"{normalized}\n", encoding="utf-8")


def backup_current_workspace_anchor() -> None:
    if CURRENT_WORKSPACE_FILE.exists():
        CURRENT_WORKSPACE_BAK_FILE.write_text(CURRENT_WORKSPACE_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def restore_current_workspace_anchor() -> None:
    if CURRENT_WORKSPACE_BAK_FILE.exists():
        CURRENT_WORKSPACE_FILE.write_text(CURRENT_WORKSPACE_BAK_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_current_workspace() -> Path:
    """兼容旧接口，返回当前工作区根目录。"""
    return CURRENT_WORKSPACE_ROOT


def resolve_workspace_root(workspace_name: str | None = None, create: bool = False) -> Path:
    normalized = _normalize_workspace_name(workspace_name or CURRENT_WORKSPACE_NAME)
    candidate = WORKSPACES_ROOT / normalized
    if candidate.exists():
        return candidate
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    return candidate


def normalize_workspace_name(workspace_name: str | None) -> str:
    return _normalize_workspace_name(workspace_name)


def read_current_workspace_name(default: str = DEFAULT_WORKSPACE_NAME) -> str:
    try:
        return _read_current_workspace_name()
    except FileNotFoundError:
        return default


def write_current_workspace_name(workspace_name: str) -> Path:
    update_current_workspace(workspace_name)
    return CURRENT_WORKSPACE_FILE


def ensure_workspace_structure(workspace_root: Path) -> None:
    for subdir in ["config", "data", "literature", "hypothesis", "code", "experiment", "memory", "knowledge_base", "logs", "report"]:
        (workspace_root / subdir).mkdir(parents=True, exist_ok=True)


def resolve_first_existing(*paths: Path, create: bool = False) -> Path:
    for candidate in paths:
        if candidate.exists():
            return candidate
    if create:
        target = paths[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    return paths[0]


def resolve_active_path(*relative_parts: str, create: bool = False) -> Path:
    workspace_path = CURRENT_WORKSPACE_ROOT.joinpath(*relative_parts)
    legacy_path = ROOT.joinpath(*relative_parts)
    return resolve_first_existing(workspace_path, legacy_path, create=create)


def bootstrap_default_workspace() -> Path:
    update_current_workspace(DEFAULT_WORKSPACE_NAME)
    workspace_root = resolve_workspace_root(DEFAULT_WORKSPACE_NAME, create=True)
    ensure_workspace_structure(workspace_root)
    return workspace_root