from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "utils"))
from path_resolver import (  # type: ignore
    CURRENT_WORKSPACE_FILE,
    CURRENT_WORKSPACE_BAK_FILE,
    WORKSPACE_INDEX_FILE,
    backup_current_workspace_anchor,
    get_workspace_config,
    load_workspace_index,
    normalize_workspace_name,
    resolve_workspace_root,
    restore_current_workspace_anchor,
    save_workspace_index,
    update_current_workspace,
)


def _validate_workspace(workspace_root: Path) -> list[str]:
    required_files = [
        workspace_root / "config" / "research_definition.md",
        workspace_root / "config" / "search_rules.yaml",
        workspace_root / "workspace_meta.json",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing workspace files: {missing}")
    return [str(path) for path in required_files]


def _update_index(workspace_name: str) -> None:
    index_data = load_workspace_index()
    current_active = index_data.get("current_active", "")
    target_id = workspace_name.removeprefix("workspace_")
    workspaces = []
    for item in index_data.get("workspaces", []):
        if item.get("workspace_name") == workspace_name or item.get("workspace_id") == target_id:
            item["status"] = "active"
            item["updated_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
        else:
            item["status"] = "inactive"
        workspaces.append(item)
    index_data["workspaces"] = workspaces
    index_data["current_active"] = workspace_name
    save_workspace_index(index_data)


def main() -> int:
    parser = argparse.ArgumentParser(description="切换当前激活的工作区")
    parser.add_argument("workspace_id", help="目标主题ID")
    parser.add_argument("--force", action="store_true", help="强制切换，忽略配置完整性校验")
    args = parser.parse_args()

    workspace_name = normalize_workspace_name(args.workspace_id)
    workspace_root = resolve_workspace_root(workspace_name, create=False)
    if not workspace_root.exists():
        raise FileNotFoundError(f"workspace not found: {workspace_root}")

    if not args.force:
        verified_files = _validate_workspace(workspace_root)
    else:
        verified_files = []

    previous_workspace = CURRENT_WORKSPACE_FILE.read_text(encoding="utf-8").strip() if CURRENT_WORKSPACE_FILE.exists() else ""
    backup_current_workspace_anchor()
    try:
        update_current_workspace(workspace_name)
        _update_index(workspace_name)
        reloaded = CURRENT_WORKSPACE_FILE.read_text(encoding="utf-8").strip()
        if reloaded != workspace_name:
            raise RuntimeError("current workspace anchor verification failed")
        config_sample = get_workspace_config("research_definition.md")
        print(f"previous_workspace={previous_workspace}")
        print(f"current_workspace={reloaded}")
        print(f"workspace_root={workspace_root}")
        print(f"core_config_path={workspace_root / 'config' / 'research_definition.md'}")
        print(f"verified_files={json.dumps(verified_files, ensure_ascii=False)}")
        if isinstance(config_sample, str):
            print(f"config_preview={config_sample[:80]}")
        else:
            print("config_preview=parsed")
        print("status=switched")
        return 0
    except Exception:
        restore_current_workspace_anchor()
        raise


if __name__ == "__main__":
    raise SystemExit(main())