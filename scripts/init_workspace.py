from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "utils"))
from path_resolver import (  # type: ignore
    CURRENT_WORKSPACE_FILE,
    WORKSPACE_INDEX_FILE,
    backup_current_workspace_anchor,
    ensure_workspace_structure,
    get_workspace_path,
    load_workspace_index,
    normalize_workspace_name,
    resolve_workspace_root,
    save_workspace_index,
    update_current_workspace,
)


def _workspace_root_from_id(workspace_id: str) -> Path:
    return resolve_workspace_root(f"workspace_{workspace_id}", create=False)


def _copy_template(source_rel: str, target_rel: str, workspace_root: Path) -> str:
    target = workspace_root / target_rel
    if target.exists():
        return f"skip_existing:{target_rel}"

    template_candidates = [
        ROOT / "core" / "config_templates" / source_rel,
        ROOT / "1_config" / source_rel,
        ROOT / "1_config" / "base" / source_rel,
        ROOT / "1_config" / "research" / source_rel,
    ]
    if source_rel == "research/program.md":
        template_candidates = [
            ROOT / "core" / "config_templates" / source_rel,
            ROOT / "6_experiment_execution" / "pipeline" / "program.md",
            ROOT / "8_knowledge_asset" / "docs" / "program.md",
        ]
    elif source_rel == "research/zotero_sync.yaml":
        template_candidates = [
            ROOT / "core" / "config_templates" / source_rel,
            ROOT / "1_config" / "base" / "zotero_sync.yaml",
            ROOT / "3_literature_workflow" / "zotero_sync" / "zotero_sync.yaml",
        ]

    for source in template_candidates:
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return f"copied:{source_rel}"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")
    return f"created_empty:{target_rel}"


def _write_research_definition(workspace_root: Path, workspace_id: str, name: str, desc: str) -> None:
    content = f"""# 研究问题定义 - {name}

## workspace_id
workspace_{workspace_id}

## 主题名称
{name}

## 主题描述
{desc}

## 核心关键词
- 待填写

## 研究目标
- 待填写

## 指标约束
- 待填写
"""
    target = workspace_root / "config" / "research_definition.md"
    target.write_text(content, encoding="utf-8")


def _copy_config_templates(workspace_root: Path) -> list[str]:
    copies = [
        ("base/openclaw_config.yaml", "config/openclaw_config.yaml"),
        ("alert/dingtalk_config.yaml", "config/dingtalk_config.yaml"),
        ("base/agent_config.yaml", "config/agent_config.yaml"),
        ("base/benchmark_projects.json", "config/benchmark_projects.json"),
        ("research/search_rules.yaml", "config/search_rules.yaml"),
        ("research/data_feature.yaml", "config/data_feature.yaml"),
        ("research/fuse_config.yaml", "config/fuse_config.yaml"),
        ("research/cost_config.yaml", "config/cost_config.yaml"),
        ("research/innovation_prompt.md", "config/innovation_prompt.md"),
        ("research/program.md", "config/program.md"),
        ("research/zotero_sync.yaml", "config/zotero_sync.yaml"),
    ]
    return [_copy_template(source_rel, target_rel, workspace_root) for source_rel, target_rel in copies]


def _initialize_memory(workspace_root: Path) -> None:
    memory_root = workspace_root / "memory"
    (memory_root / "success").mkdir(parents=True, exist_ok=True)
    (memory_root / "failure").mkdir(parents=True, exist_ok=True)
    (memory_root / "skills_library.md").write_text("# skills_library\n", encoding="utf-8")
    (memory_root / "success" / "README.md").write_text("# success memory\n", encoding="utf-8")
    (memory_root / "failure" / "README.md").write_text("# failure memory\n", encoding="utf-8")


def _create_workspace_meta(workspace_id: str, name: str, desc: str, template: str, status: str) -> dict:
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "workspace_id": workspace_id,
        "workspace_name": f"workspace_{workspace_id}",
        "display_name": name,
        "description": desc,
        "template": template,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }


def _update_workspace_index(meta: dict, current_active: str | None = None) -> None:
    index_data = load_workspace_index()
    workspaces = [item for item in index_data.get("workspaces", []) if item.get("workspace_id") != meta["workspace_id"]]
    for item in workspaces:
        item["status"] = "inactive"
    workspaces.append(meta)
    index_data["workspaces"] = workspaces
    if current_active is not None:
        index_data["current_active"] = current_active
    save_workspace_index(index_data)


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化新的主题工作区")
    parser.add_argument("workspace_id", help="主题唯一ID，仅支持字母、数字、下划线")
    parser.add_argument("--name", default="默认研究主题", help="主题中文名称")
    parser.add_argument("--desc", default="项目原有研究内容迁移", help="主题详细描述")
    parser.add_argument("--template", default="default", help="配置模板名称")
    parser.add_argument("--no-switch", action="store_true", help="创建后不切换为当前激活主题")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_]+", args.workspace_id):
        raise ValueError("workspace_id 仅支持字母、数字、下划线")

    workspace_name = f"workspace_{args.workspace_id}"
    workspace_root = resolve_workspace_root(workspace_name, create=False)
    if workspace_root.exists():
        raise FileExistsError(f"workspace already exists: {workspace_name}")

    workspace_root.mkdir(parents=True, exist_ok=False)
    try:
        for relative_path in [
            "config",
            "data",
            "literature/pdf",
            "literature/structured",
            "hypothesis",
            "code",
            "experiment",
            "memory",
            "knowledge_base",
            "logs",
            "report",
        ]:
            (workspace_root / relative_path).mkdir(parents=True, exist_ok=True)

        _initialize_memory(workspace_root)
        _write_research_definition(workspace_root, args.workspace_id, args.name, args.desc)
        copy_logs = _copy_config_templates(workspace_root)

        meta = _create_workspace_meta(args.workspace_id, args.name, args.desc, args.template, "active")
        (workspace_root / "workspace_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        _update_workspace_index(meta, current_active=workspace_name if not args.no_switch else load_workspace_index().get("current_active", ""))

        if not args.no_switch:
            update_current_workspace(workspace_name)

        verify_paths = [
            workspace_root / "config" / "research_definition.md",
            workspace_root / "config" / "search_rules.yaml",
            workspace_root / "workspace_meta.json",
        ]
        missing = [str(path) for path in verify_paths if not path.exists()]
        if missing:
            raise FileNotFoundError(f"missing created files: {missing}")

        print(f"workspace_id={args.workspace_id}")
        print(f"workspace_name={workspace_name}")
        print(f"workspace_root={workspace_root}")
        print(f"template={args.template}")
        for item in copy_logs:
            print(item)
        print("status=created")
        return 0
    except Exception:
        shutil.rmtree(workspace_root, ignore_errors=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())