from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


@dataclass
class MoveLog:
    source: str
    target: str
    status: str
    detail: str = ""


ROOT = Path(__file__).resolve().parents[2]

MOVE_RULES: List[Tuple[str, str]] = [
    ("config/agent_config.yaml", "1_config/base/agent_config.yaml"),
    ("config/alert_config.yaml", "1_config/alert/alert_config.yaml"),
    ("config/cost_config.yaml", "1_config/research/cost_config.yaml"),
    ("config/data_feature.yaml", "1_config/research/data_feature.yaml"),
    ("config/fuse_config.yaml", "1_config/research/fuse_config.yaml"),
    ("config/innovation_prompt.md", "hypothesis/innovation_prompt.md"),
    ("config/program.md", "experiment/pipeline/program.md"),
    ("config/search_rules.yaml", "3_literature_workflow/search_rules.yaml"),
    ("config/zotero_sync.yaml", "3_literature_workflow/zotero_sync/zotero_sync.yaml"),
    ("config/prompts", "2_agent_system/prompts"),
    ("code/crawler", "3_literature_workflow/crawler"),
    ("code/utils", "3_literature_workflow/downloaders"),
    ("code/run_crawler.py", "3_literature_workflow/run_crawler.py"),
    ("code/install_chromedriver.py", "3_literature_workflow/install_chromedriver.py"),
    ("code/power_models", "code/optimized/power_models"),
    ("code/test_model.py", "code/demo/test_model.py"),
    ("code/prepare_mtg_data.py", "experiment/pipeline/prepare_mtg_data.py"),
    ("code/run_stage3_local.ps1", "experiment/pipeline/run_stage3_local.ps1"),
    ("code/run_round_fixed_pipeline.py", "experiment/pipeline/run_round_fixed_pipeline.py"),
    ("code/check_round2_deps.py", "experiment/pipeline/check_round2_deps.py"),
    ("code/check_torch.py", "experiment/pipeline/check_torch.py"),
    ("code/get_num_nodes.py", "experiment/pipeline/get_num_nodes.py"),
    ("code/dynamic_mtg nn_model.py", "code/optimized/dynamic_mtg_nn_model.py"),
    ("code/chromedriver-win32.zip", "3_literature_workflow/crawler/chromedriver-win32.zip"),
    ("code/SERVER_DEPLOY.md", "knowledge_base/docs/SERVER_DEPLOY.md"),
    ("code/SSH_SETUP.md", "knowledge_base/docs/SSH_SETUP.md"),
    ("code/SSH_PUBKEY.txt", "knowledge_base/docs/SSH_PUBKEY.txt"),
    ("code/SKILLS.md", "knowledge_base/docs/SKILLS.md"),
    ("code/program.md", "knowledge_base/docs/program.md"),
    ("data", "experiment/data"),
    ("experiment", "experiment/tuning_log/raw_runs"),
    ("literature", "3_literature_workflow/literature_asset"),
    ("hypothesis", "hypothesis/history"),
    ("knowledge_base", "knowledge_base/knowledge_base"),
    ("memory", "knowledge_base/iteration_memory/legacy_memory"),
    ("docs", "knowledge_base/docs"),
    ("report", "knowledge_base/final_report/history_report"),
    ("MTGNN", "code/baseline/MTGNN_root"),
    ("TimesNet", "code/baseline/TimesNet_root"),
    ("research_definition.md", "1_config/research/research_definition.md"),
    ("DARIS v3.docx", "knowledge_base/docs/DARIS_v3.docx"),
    ("~$RIS v3.docx", "knowledge_base/docs/~$RIS v3.docx"),
    ("README.md", "knowledge_base/docs/README_legacy.md"),
]

CLEANUP_DIRS = [
    "code",
    "config",
    "data",
    "docs",
    "experiment",
    "hypothesis",
    "knowledge_base",
    "literature",
    "memory",
    "report",
    "code/__pycache__",
]


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if path.suffix:
        return path.with_name(f"{path.stem}_migrated_{stamp}{path.suffix}")
    return path.with_name(f"{path.name}_migrated_{stamp}")


def _safe_move_file(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    final_dst = _unique_path(dst)
    shutil.move(str(src), str(final_dst))
    return final_dst


def _merge_dir(src: Path, dst: Path, logs: List[MoveLog]) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        child_dst = dst / child.name
        _safe_move(child, child_dst, logs)
    if src.exists() and not any(src.iterdir()):
        src.rmdir()


def _safe_move(src: Path, dst: Path, logs: List[MoveLog]) -> None:
    if not src.exists():
        logs.append(MoveLog(str(src.relative_to(ROOT)), str(dst.relative_to(ROOT)), "skipped", "source_missing"))
        return

    try:
        if src.is_dir():
            if dst.exists() and dst.is_dir():
                _merge_dir(src, dst, logs)
                logs.append(MoveLog(str(src.relative_to(ROOT)), str(dst.relative_to(ROOT)), "merged"))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                final_dst = _unique_path(dst)
                shutil.move(str(src), str(final_dst))
                logs.append(MoveLog(str(src.relative_to(ROOT)), str(final_dst.relative_to(ROOT)), "moved"))
        else:
            final_dst = _safe_move_file(src, dst)
            logs.append(MoveLog(str(src.relative_to(ROOT)), str(final_dst.relative_to(ROOT)), "moved"))
    except Exception as exc:  # pylint: disable=broad-except
        logs.append(MoveLog(str(src), str(dst), "error", str(exc)))


def run_reorganization() -> dict:
    logs: List[MoveLog] = []

    for src_rel, dst_rel in MOVE_RULES:
        src = ROOT / src_rel
        dst = ROOT / dst_rel
        _safe_move(src, dst, logs)

    removed_dirs = []
    for d in CLEANUP_DIRS:
        path = ROOT / d
        if path.exists() and path.is_dir() and not any(path.iterdir()):
            path.rmdir()
            removed_dirs.append(d)

    report_dir = ROOT / "8_knowledge_asset" / "final_report"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = report_dir / f"workspace_reorg_{stamp}.json"
    md_path = report_dir / f"workspace_reorg_{stamp}.md"

    payload = {
        "timestamp": datetime.now().isoformat(),
        "moved": [l.__dict__ for l in logs],
        "removed_empty_dirs": removed_dirs,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Workspace Reorganization Report",
        "",
        f"- Time: {payload['timestamp']}",
        f"- Total rules: {len(MOVE_RULES)}",
        f"- Empty dirs removed: {', '.join(removed_dirs) if removed_dirs else 'none'}",
        "",
        "## Move Logs",
        "| Source | Target | Status | Detail |",
        "|---|---|---|---|",
    ]
    for item in payload["moved"]:
        lines.append(
            f"| {item['source']} | {item['target']} | {item['status']} | {item.get('detail', '')} |"
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "json_report": str(json_path),
        "md_report": str(md_path),
        "removed_empty_dirs": removed_dirs,
    }


if __name__ == "__main__":
    result = run_reorganization()
    print(json.dumps(result, ensure_ascii=False, indent=2))
