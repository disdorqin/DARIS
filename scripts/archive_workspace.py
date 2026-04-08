from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime
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


def _update_status(workspace_name: str, status: str) -> None:
    index_data = load_workspace_index()
    timestamp = datetime.now().isoformat(timespec="seconds")
    for item in index_data.get("workspaces", []):
        if item.get("workspace_name") == workspace_name or item.get("workspace_id") == workspace_name.removeprefix("workspace_"):
            item["status"] = status
            item["updated_at"] = timestamp
    if status == "archived" and index_data.get("current_active") == workspace_name:
        index_data["current_active"] = ""
    save_workspace_index(index_data)


def _update_meta(workspace_root: Path, status: str) -> None:
    meta_path = workspace_root / "workspace_meta.json"
    if not meta_path.exists():
        return
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["status"] = status
    meta["updated_at"] = datetime.now().isoformat(timespec="seconds")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _zip_workspace(source_root: Path, archive_path: Path, password: str | None) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if password:
        try:
            import pyzipper
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("password archive requires pyzipper") from exc

        with pyzipper.AESZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as archive:
            archive.setpassword(password.encode("utf-8"))
            for file_path in source_root.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(source_root))
        return archive_path

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in source_root.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(source_root))
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description="归档一个工作区到 archives/ 目录")
    parser.add_argument("workspace_id", help="要归档的主题ID")
    parser.add_argument("--keep-source", action="store_true", help="归档后保留原工作区目录")
    parser.add_argument("--output-path", default="archives", help="归档包输出路径")
    parser.add_argument("--password", default="", help="归档包密码")
    args = parser.parse_args()

    workspace_name = normalize_workspace_name(args.workspace_id)
    workspace_root = resolve_workspace_root(workspace_name, create=False)
    if not workspace_root.exists():
        raise FileNotFoundError(f"workspace not found: {workspace_root}")
    if _is_current_active(workspace_name):
        raise RuntimeError("cannot archive current active workspace")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_root = (ROOT / args.output_path).resolve()
    archive_path = archive_root / f"{workspace_name}_{timestamp}.zip"

    _update_status(workspace_name, "archiving")
    _update_meta(workspace_root, "archiving")
    try:
        created = _zip_workspace(workspace_root, archive_path, args.password or None)
        if not created.exists() or created.stat().st_size <= 0:
            raise RuntimeError("archive package validation failed")

        if not args.keep_source:
            shutil.rmtree(workspace_root, ignore_errors=True)
            source_state = "deleted"
        else:
            for path in workspace_root.rglob("*"):
                try:
                    os.chmod(path, 0o444 if path.is_file() else 0o555)
                except Exception:
                    pass
            source_state = "kept_readonly"

        _update_status(workspace_name, "archived")
        _update_meta(workspace_root, "archived")
        print(f"workspace_id={args.workspace_id}")
        print(f"archive_path={created}")
        print(f"archive_size={created.stat().st_size}")
        print(f"archived_at={timestamp}")
        print(f"source_state={source_state}")
        print("status=archived")
        return 0
    except Exception:
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
        _update_status(workspace_name, "active")
        _update_meta(workspace_root, "active")
        raise


if __name__ == "__main__":
    raise SystemExit(main())