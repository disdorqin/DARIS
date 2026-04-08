from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "utils"))
from path_resolver import (  # type: ignore
    CURRENT_WORKSPACE_FILE,
    get_workspace_path,
    load_workspace_index,
    normalize_workspace_name,
    resolve_workspace_root,
    save_workspace_index,
)


def _is_current_active(workspace_name: str) -> bool:
    current = CURRENT_WORKSPACE_FILE.read_text(encoding="utf-8").strip() if CURRENT_WORKSPACE_FILE.exists() else ""
    return current == workspace_name


def _remove_from_index(workspace_name: str) -> None:
    index_data = load_workspace_index()
    workspace_id = workspace_name.removeprefix("workspace_")
    index_data["workspaces"] = [
        item for item in index_data.get("workspaces", [])
        if item.get("workspace_name") != workspace_name and item.get("workspace_id") != workspace_id
    ]
    if index_data.get("current_active") == workspace_name:
        index_data["current_active"] = ""
    save_workspace_index(index_data)


def _remove_archives(workspace_name: str) -> list[str]:
    archives_root = ROOT / "archives"
    if not archives_root.exists():
        return []
    removed = []
    pattern = f"{workspace_name}_*.zip"
    for archive_path in archives_root.glob(pattern):
        archive_path.unlink(missing_ok=True)
        removed.append(str(archive_path))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="删除无效主题")
    parser.add_argument("workspace_id", help="要删除的主题ID")
    parser.add_argument("--force", action="store_true", help="强制删除无需二次确认")
    parser.add_argument("--include-archive", action="store_true", help="同时删除对应归档包")
    args = parser.parse_args()

    workspace_name = normalize_workspace_name(args.workspace_id)
    workspace_root = resolve_workspace_root(workspace_name, create=False)
    if _is_current_active(workspace_name):
        raise RuntimeError("cannot delete current active workspace")

    if not args.force:
        confirm = input(f"确认删除工作区 {workspace_name}? (y/N): ").strip().lower()
        if confirm != "y":
            print("status=cancelled")
            return 0

    removed_archives: list[str] = []
    try:
        if workspace_root.exists():
            shutil.rmtree(workspace_root, ignore_errors=False)
        if args.include_archive:
            removed_archives = _remove_archives(workspace_name)
        _remove_from_index(workspace_name)
        print(f"workspace_id={args.workspace_id}")
        print(f"workspace_root={workspace_root}")
        print(f"archives_removed={removed_archives}")
        print("status=deleted")
        return 0
    except Exception:
        raise


if __name__ == "__main__":
    raise SystemExit(main())