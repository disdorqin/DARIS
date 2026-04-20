from __future__ import annotations

import hashlib
import json
import os
import shutil
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(r"d:\computer learning\science_workflow")
BACKUP_ROOT = ROOT / "backup_20260407"
WORKSPACE_ROOT = ROOT / "workspaces" / "workspace_default"

DIR_MAPPINGS = [
    (ROOT / "1_config", WORKSPACE_ROOT / "1_config"),
    (ROOT / "2_agent_system", WORKSPACE_ROOT / "2_agent_system"),
    (ROOT / "3_literature_workflow", WORKSPACE_ROOT / "3_literature_workflow"),
    (ROOT / "4_research_hypothesis", WORKSPACE_ROOT / "hypothesis"),
    (ROOT / "5_code_base", WORKSPACE_ROOT / "code"),
    (ROOT / "6_experiment_execution", WORKSPACE_ROOT / "experiment"),
    (ROOT / "7_monitor_system", WORKSPACE_ROOT / "7_monitor_system"),
    (ROOT / "8_knowledge_asset", WORKSPACE_ROOT / "knowledge_base"),
]

FILE_MAPPINGS = [
    (ROOT / "aliyun_connector.py", WORKSPACE_ROOT / "code" / "utils" / "aliyun_connector.py"),
    (ROOT / "dingtalk_callback.py", WORKSPACE_ROOT / "code" / "utils" / "dingtalk_callback.py"),
    (ROOT / "workspace_context.py", WORKSPACE_ROOT / "code" / "utils" / "workspace_context.py"),
    (ROOT / "openclaw_main.py", WORKSPACE_ROOT / "code" / "openclaw_main.py"),
    (ROOT / "openclaw_requirements.txt", WORKSPACE_ROOT / "code" / "openclaw_requirements.txt"),
    (ROOT / "工程化工作流.md", WORKSPACE_ROOT / "report" / "工程化工作流.md"),
    (ROOT / "DARIS_V31.md", WORKSPACE_ROOT / "report" / "DARIS_V31.md"),
]

LEGACY_PATH_REPLACEMENTS = [
    ("8_knowledge_asset/iteration_memory", "knowledge_base/iteration_memory"),
    ("8_knowledge_asset/final_report", "knowledge_base/final_report"),
    ("8_knowledge_asset/git_version", "knowledge_base/git_version"),
    ("8_knowledge_asset/", "knowledge_base/"),
    ("5_code_base/", "code/"),
    ("6_experiment_execution/", "experiment/"),
    ("4_research_hypothesis/", "hypothesis/"),
    ("8_knowledge_asset\\iteration_memory", "knowledge_base/iteration_memory"),
    ("8_knowledge_asset\\final_report", "knowledge_base/final_report"),
    ("8_knowledge_asset\\git_version", "knowledge_base/git_version"),
    ("8_knowledge_asset\\", "knowledge_base\\"),
    ("5_code_base\\", "code\\"),
    ("6_experiment_execution\\", "experiment\\"),
    ("4_research_hypothesis\\", "hypothesis\\"),
]

TEXT_SUFFIXES = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".ini", ".cfg", ".toml"}
TEXT_ENCODINGS = ("utf-8", "utf-8-sig", "cp936", "gbk", "latin-1")
LOG_FILE = ROOT / ".migrate_default_workspace.log"
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
}
IGNORED_FILE_NAMES = {
    "._migrate_default_workspace.py",
    ".migrate_default_workspace.py",
    ".migrate_default_workspace.log",
}


@dataclass
class PathStats:
    files: int
    bytes: int


def ensure_workspace_structure() -> None:
    for relative in ["config", "code", "hypothesis", "experiment", "knowledge_base", "report", "logs", "data", "literature", "memory"]:
        (WORKSPACE_ROOT / relative).mkdir(parents=True, exist_ok=True)
    (WORKSPACE_ROOT / "code" / "utils").mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def collect_stats(path: Path) -> PathStats:
    if path.is_file():
        return PathStats(1, path.stat().st_size)
    if not path.exists():
        return PathStats(0, 0)
    file_count = 0
    total_bytes = 0
    for item in path.rglob("*"):
        rel_parts = item.relative_to(path).parts
        if any(part in IGNORED_DIR_NAMES for part in rel_parts):
            continue
        if item.name in IGNORED_FILE_NAMES or item.suffix == ".pyc":
            continue
        if item.is_file():
            file_count += 1
            total_bytes += item.stat().st_size
    return PathStats(file_count, total_bytes)


def copy_directory(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)

    def _ignore(directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in IGNORED_DIR_NAMES or name in IGNORED_FILE_NAMES or name.endswith(".pyc")
        }

    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=_ignore)


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def force_remove(path: Path) -> None:
    if not path.exists():
        return

    def _onerror(func, failed_path, exc_info):
        try:
            os.chmod(failed_path, 0o777)
            func(failed_path)
        except Exception:
            raise exc_info[1]

    if path.is_dir():
        shutil.rmtree(path, onerror=_onerror)
    else:
        try:
            path.unlink()
        except PermissionError:
            os.chmod(path, 0o666)
            path.unlink()


def write_text_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text_with_encoding(path: Path) -> tuple[str, str] | None:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    return None


def patch_text_file(path: Path) -> None:
    if not path.exists() or path.suffix.lower() not in TEXT_SUFFIXES:
        return
    decoded = read_text_with_encoding(path)
    if decoded is None:
        return
    original, encoding = decoded
    updated = original
    for old, new in LEGACY_PATH_REPLACEMENTS:
        updated = updated.replace(old, new)
    if path.name == "openclaw_main.py":
        updated = updated.replace(
            "from core.utils.path_resolver import resolve_first_existing, resolve_workspace_root",
            "sys.path.insert(0, str(Path(__file__).resolve().parents[3]))\nsys.path.insert(0, str(Path(__file__).resolve().parent / \"utils\"))\nfrom core.utils.path_resolver import resolve_first_existing, resolve_workspace_root",
            1,
        )
        updated = updated.replace(
            "ROOT = Path(__file__).resolve().parent",
            "ROOT = resolve_workspace_root(create=True)",
            1,
        )
    if path.name == "workspace_context.py" and path.parent.name == "utils":
        updated = (
            "from __future__ import annotations\n\n"
            "from pathlib import Path\n"
            "import sys\n\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[4]))\n"
            "from core.utils.path_resolver import *  # noqa: F401,F403\n"
        )
    if path.name in {"aliyun_connector.py", "dingtalk_callback.py"} and path.parent.name == "utils":
        updated = updated.replace(
            "Path(__file__).resolve().parent / \"2_agent_system\"",
            "Path(__file__).resolve().parents[2] / \"2_agent_system\"",
            1,
        )
    if path.name == "run.py" and "1_research_manager" in str(path):
        updated = updated.replace(
            "sys.path.insert(0, str(Path(__file__).resolve().parents[2]))",
            "sys.path.insert(0, str(Path(__file__).resolve().parents[4]))",
            1,
        )
    if updated != original:
        path.write_text(updated, encoding=encoding)


def tree_lines(root: Path, exclude_names: set[str] | None = None) -> list[str]:
    exclude_names = exclude_names or set()
    lines: list[str] = []

    def walk(current: Path, prefix: str = "") -> None:
        children = sorted(
            [item for item in current.iterdir() if item.name not in exclude_names],
            key=lambda item: (not item.is_dir(), item.name.lower()),
        )
        for index, child in enumerate(children):
            is_last = index == len(children) - 1
            connector = "└── " if is_last else "├── "
            name = child.name + ("/" if child.is_dir() else "")
            lines.append(prefix + connector + name)
            if child.is_dir():
                extension = "    " if is_last else "│   "
                walk(child, prefix + extension)

    lines.append(root.name)
    walk(root)
    return lines


def compare_entries(source: Path, destination: Path) -> dict[str, object]:
    source_stats = collect_stats(source)
    destination_stats = collect_stats(destination)
    return {
        "source": str(source),
        "destination": str(destination),
        "source_files": source_stats.files,
        "source_bytes": source_stats.bytes,
        "destination_files": destination_stats.files,
        "destination_bytes": destination_stats.bytes,
        "files_match": source_stats.files == destination_stats.files,
        "bytes_match": source_stats.bytes == destination_stats.bytes,
        "destination_exists": destination.exists(),
    }


def copy_and_patch_all() -> None:
    log("copy_and_patch_all:start")
    for source, destination in DIR_MAPPINGS:
        if not source.exists():
            raise FileNotFoundError(f"missing source directory: {source}")
        copy_directory(source, destination)
        log(f"copied_dir:{source}->{destination}")
    for source, destination in FILE_MAPPINGS:
        if not source.exists():
            raise FileNotFoundError(f"missing source file: {source}")
        copy_file(source, destination)
        log(f"copied_file:{source}->{destination}")

    for target in [destination for _, destination in FILE_MAPPINGS]:
        patch_text_file(target)
        log(f"patched_file:{target}")

    for root_dir in [WORKSPACE_ROOT / "code", WORKSPACE_ROOT / "2_agent_system", WORKSPACE_ROOT / "report", WORKSPACE_ROOT / "knowledge_base", WORKSPACE_ROOT / "experiment", WORKSPACE_ROOT / "hypothesis", WORKSPACE_ROOT / "3_literature_workflow", WORKSPACE_ROOT / "1_config", WORKSPACE_ROOT / "7_monitor_system"]:
        if root_dir.exists():
            for path in root_dir.rglob("*"):
                if path.is_file():
                    patch_text_file(path)

    write_text_if_changed(
        WORKSPACE_ROOT / "code" / "path_adaptation.md",
        "# 路径适配说明\n\n"
        "- 迁移后的业务入口统一通过 core/utils/path_resolver.py 获取当前工作区路径。\n"
        "- workspace_default/code/openclaw_main.py 会把仓库根目录加入 sys.path，再加载 core 与 code/utils 下的本地包装模块。\n"
        "- workspace_default/2_agent_system/1_research_manager/run.py 会把仓库根目录加入 sys.path，确保 core.utils.path_resolver 可导入。\n"
        "- workspace_default/code/utils/aliyun_connector.py、dingtalk_callback.py、workspace_context.py 已按工作区路径重写。\n"
    )
    log("copy_and_patch_all:done")


def backup_all() -> list[dict[str, object]]:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    report = []
    log("backup_all:start")
    for source, _ in DIR_MAPPINGS:
        backup_target = BACKUP_ROOT / source.name
        force_remove(backup_target)
        copy_directory(source, backup_target)
        report.append(compare_entries(source, backup_target))
        log(f"backed_up_dir:{source}->{backup_target}")
    for source, _ in FILE_MAPPINGS:
        backup_target = BACKUP_ROOT / source.name
        force_remove(backup_target)
        copy_file(source, backup_target)
        report.append(compare_entries(source, backup_target))
        log(f"backed_up_file:{source}->{backup_target}")
    log("backup_all:done")
    return report


def delete_root_business_content() -> list[str]:
    removed = []
    log("delete_root_business_content:start")
    for source, _ in FILE_MAPPINGS:
        if source.exists():
            source.unlink()
            removed.append(str(source))
            log(f"removed_file:{source}")
    for source, _ in DIR_MAPPINGS:
        if source.exists():
            shutil.rmtree(source)
            removed.append(str(source))
            log(f"removed_dir:{source}")
    log("delete_root_business_content:done")
    return removed


def build_report(backup_report: list[dict[str, object]], migration_report: list[dict[str, object]], removed_items: list[str]) -> str:
    lines = [
        "# DARIS 默认工作区完整迁移报告",
        "",
        "## 1. 备份完成情况",
        f"- 备份目录: {BACKUP_ROOT}",
        f"- 备份项数量: {len(backup_report)}",
        "",
        "### 备份校验",
    ]
    for item in backup_report:
        lines.append(
            f"- {item['source']} -> {item['destination']} | files={item['source_files']} bytes={item['source_bytes']} | 校验: files={item['files_match']} bytes={item['bytes_match']}"
        )
    lines.extend([
        "",
        "## 2. 迁移执行情况",
        f"- 默认工作区: {WORKSPACE_ROOT}",
        f"- 迁移项数量: {len(migration_report)}",
        "",
        "### 迁移校验",
    ])
    for item in migration_report:
        lines.append(
            f"- {item['source']} -> {item['destination']} | source_files={item['source_files']} target_files={item['destination_files']} | source_bytes={item['source_bytes']} target_bytes={item['destination_bytes']} | 校验: files={item['files_match']} bytes={item['bytes_match']}"
        )
    lines.extend([
        "",
        "## 3. 根目录清理情况",
        f"- 已移除业务项数量: {len(removed_items)}",
        "",
        "## 4. 路径适配说明",
        "- 迁移后的业务代码通过 core/utils/path_resolver.py 获取当前工作区路径。",
        "- 旧路径 5_code_base/、6_experiment_execution/、8_knowledge_asset/、4_research_hypothesis/ 已在工作区内映射为 code/、experiment/、knowledge_base/、hypothesis/。",
        "- 关键入口已补充工作区与仓库根路径注入，确保 workspace_default 下脚本可直接运行。",
        "",
        "## 5. 树文件位置",
        f"- 根目录树: {WORKSPACE_ROOT / 'report' / 'daris_root_tree_20260407.md'}",
        f"- workspace_default 树: {WORKSPACE_ROOT / 'report' / 'daris_workspace_default_tree_20260407.md'}",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        log("main:start")
        ensure_workspace_structure()
        log("ensure_workspace_structure:done")
        backup_report = backup_all()
        copy_and_patch_all()

        migration_report = [compare_entries(source, destination) for source, destination in DIR_MAPPINGS]
        migration_report.extend(compare_entries(source, destination) for source, destination in FILE_MAPPINGS)

        removed_items = delete_root_business_content()

        root_tree = "\n".join(tree_lines(ROOT, exclude_names={".git", ".venv", ".__pycache__"})) + "\n"
        workspace_tree = "\n".join(tree_lines(WORKSPACE_ROOT, exclude_names={"__pycache__"})) + "\n"
        write_text_if_changed(WORKSPACE_ROOT / "report" / "daris_root_tree_20260407.md", "```text\n" + root_tree + "```\n")
        write_text_if_changed(WORKSPACE_ROOT / "report" / "daris_workspace_default_tree_20260407.md", "```text\n" + workspace_tree + "```\n")

        report = build_report(backup_report, migration_report, removed_items)
        write_text_if_changed(WORKSPACE_ROOT / "report" / "daris_workspace_migration_20260407.md", report)

        print(report)
        print("ROOT_TREE_FILE=" + str(WORKSPACE_ROOT / "report" / "daris_root_tree_20260407.md"))
        print("WORKSPACE_TREE_FILE=" + str(WORKSPACE_ROOT / "report" / "daris_workspace_default_tree_20260407.md"))
        log("main:done")
        return 0
    except Exception as exc:
        log("main:error:" + repr(exc))
        log(traceback.format_exc())
        raise


if __name__ == "__main__":
    raise SystemExit(main())
