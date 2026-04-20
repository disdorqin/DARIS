from __future__ import annotations

import json
import re
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
ROUND_ID = 2
ROUND_DATE = "20260408"
ROUND_DIR = ROOT / "rounds" / f"round_{ROUND_ID}_{ROUND_DATE}"
LIT_DIR = ROUND_DIR / "literature"
HYP_DIR = ROUND_DIR / "hypothesis"
CHG_DIR = ROUND_DIR / "code_changes"
EXP_DIR = ROUND_DIR / "experiment_results"
LOG_DIR = ROUND_DIR / "logs"
REPORT_DIR = ROUND_DIR / "report"
WORKSPACE_REPORT = ROOT / "report"
WORKSPACE_KNOWLEDGE = ROOT / "8_knowledge_asset" / "final_report" / "history_report"
PIPELINE_SCRIPT = ROOT / "6_experiment_execution" / "pipeline" / "run_round_fixed_pipeline.py"
PYTHON = sys.executable

LOG_LINES: list[str] = []


def log(message: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    LOG_LINES.append(line)


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def infer_method(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    rules = [
        ("feature selection", "Feature selection / filtering"),
        ("feature engineering", "Feature engineering / handcrafted features"),
        ("feature interaction", "Feature interaction / cross feature modeling"),
        ("attention", "Attention-based feature weighting"),
        ("multimodal", "Multi-modal fusion"),
        ("multi-modal", "Multi-modal fusion"),
        ("fusion", "Multi-source data fusion"),
        ("heterogeneous", "Heterogeneous data fusion"),
        ("graph", "Graph-based feature fusion"),
        ("decomposition", "Multi-scale decomposition / trend-residual separation"),
        ("transformer", "Transformer-based sequence fusion"),
        ("forecast", "Forecasting model with multivariate features"),
        ("prediction", "Predictive model with multivariate features"),
    ]
    for needle, label in rules:
        if needle in text:
            return label
    return "Multivariate forecasting"


def normalize_doi(doi: str) -> str:
    return doi.strip().lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def year_from_crossref_item(item: dict) -> int:
    for key in ("published-print", "published-online", "issued", "created"):
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return int(parts[0][0])
    return 0


def authors_from_crossref_item(item: dict) -> list[str]:
    authors = []
    for author in item.get("author", [])[:10]:
        given = author.get("given", "").strip()
        family = author.get("family", "").strip()
        joined = " ".join(part for part in [given, family] if part)
        if joined:
            authors.append(joined)
    return authors


def crossref_search(query: str, rows: int = 10) -> list[dict]:
    params = {
        "query.bibliographic": query,
        "rows": rows,
        "filter": "from-pub-date:2020-01-01",
    }
    url = f"https://api.crossref.org/works?{urlencode(params)}"
    response = requests.get(url, timeout=60, headers={"User-Agent": "CopilotResearch/1.0 (mailto:copilot@example.com)"})
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])
    results = []
    for item in items:
        title = clean_text(item.get("title", [""])[0] if item.get("title") else "")
        doi = normalize_doi(item.get("DOI", ""))
        if not title and not doi:
            continue
        abstract = clean_text(item.get("abstract", ""))
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        results.append(
            {
                "title": title,
                "doi": doi,
                "year": year_from_crossref_item(item),
                "url": url,
                "authors": authors_from_crossref_item(item),
                "abstract": abstract,
                "source": "Crossref",
                "keyword": query,
                "method": infer_method(title, abstract),
            }
        )
    return results


def arxiv_search(query: str, max_results: int = 8) -> list[dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"http://export.arxiv.org/api/query?{urlencode(params)}"
    response = requests.get(url, timeout=60, headers={"User-Agent": "CopilotResearch/1.0"})
    response.raise_for_status()
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    results = []
    for entry in root.findall("atom:entry", ns):
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ns))
        summary = clean_text(entry.findtext("atom:summary", default="", namespaces=ns))
        year_text = entry.findtext("atom:published", default="", namespaces=ns)
        year = int(year_text[:4]) if year_text else 0
        links = []
        for link in entry.findall("atom:link", ns):
            href = link.attrib.get("href", "")
            if href:
                links.append(href)
        authors = [clean_text(author.findtext("atom:name", default="", namespaces=ns)) for author in entry.findall("atom:author", ns)]
        authors = [author for author in authors if author]
        identifier = clean_text(entry.findtext("atom:id", default="", namespaces=ns))
        results.append(
            {
                "title": title,
                "doi": identifier,
                "year": year,
                "url": identifier,
                "all_urls": links[:3],
                "authors": authors,
                "abstract": summary,
                "source": "arXiv",
                "keyword": query,
                "method": infer_method(title, summary),
            }
        )
    return results


def dedupe_papers(papers: Iterable[dict]) -> list[dict]:
    seen = set()
    unique: list[dict] = []
    for paper in papers:
        key = normalize_doi(paper.get("doi", "")) or paper.get("title", "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(paper)
    return unique


def relevance_score(paper: dict) -> int:
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    score = 0
    for needle in ["feature", "fusion", "multivariate", "multimodal", "heterogeneous", "attention", "selection", "electricity", "load", "forecast", "prediction", "time series"]:
        if needle in text:
            score += 1
    return score


def paper_url_list(paper: dict) -> list[str]:
    urls = []
    if paper.get("url"):
        urls.append(str(paper["url"]))
    doi = paper.get("doi", "")
    if doi and not str(doi).startswith("http"):
        urls.append(f"https://doi.org/{doi}")
    for extra in paper.get("all_urls", []) or []:
        if extra and extra not in urls:
            urls.append(extra)
    return urls


def build_literature_report(papers: list[dict]) -> str:
    source_counts: dict[str, int] = {}
    method_counts: dict[str, int] = {}
    for paper in papers:
        source_counts[paper["source"]] = source_counts.get(paper["source"], 0) + 1
        method_counts[paper["method"]] = method_counts.get(paper["method"], 0) + 1

    lines = [
        "# Structured Literature Report",
        "",
        f"- round: {ROUND_ID}",
        f"- date: {ROUND_DATE}",
        f"- total_papers: {len(papers)}",
        "",
        "## Source Coverage",
    ]
    for source, count in sorted(source_counts.items()):
        lines.append(f"- {source}: {count}")
    lines.extend([
        "",
        "## Main Method Families",
    ])
    for method, count in sorted(method_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {method}: {count}")
    lines.extend([
        "",
        "## Paper Table",
        "| # | Keyword | Year | Source | Method | Title | DOI | URLs |",
        "|---|---|---:|---|---|---|---|---|",
    ])
    for idx, paper in enumerate(papers, 1):
        url_text = "<br>".join(paper_url_list(paper)[:3])
        title = paper.get('title', '').replace('|', '\\|')
        doi = paper.get('doi', '').replace('|', '\\|')
        lines.append(
            f"| {idx} | {paper.get('keyword', '')} | {paper.get('year', 0)} | {paper.get('source', '')} | {paper.get('method', '')} | {title} | {doi} | {url_text} |"
        )
    lines.extend([
        "",
        "## Notes",
        "- 本轮以公开可检索结果为准，优先保留能提供 DOI 或可直接打开链接的条目。",
        "- 主流方法可归纳为：特征选择/过滤、特征交叉、多模态/多源融合、注意力加权、图结构融合、趋势-残差或多尺度分解。",
        "- 文献与策略文档均归档到 rounds/round_2_20260408/。",
    ])
    return "\n".join(lines)


def build_strategy_document(papers: list[dict]) -> str:
    citations = []
    for paper in papers[:12]:
        urls = paper_url_list(paper)
        citations.append(f"- {paper.get('title', '')} ({paper.get('year', 0)}) — {urls[0] if urls else paper.get('doi', '')}")

    feature_lines = [
        ("时间特征扩展", "日/周/月周期的 sin-cos 编码、归一化时间索引、节假日/工作日标记。", ["feature engineering", "attention", "multivariate time series forecasting"]),
        ("天气特征融合", "温度、湿度、风速、降水、气压、体感温度等外部天气源按时间对齐后拼接。", ["multimodal", "fusion", "heterogeneous"]),
        ("历史负荷特征交叉", "目标负荷与滞后项、滑动均值、滑动标准差、差分项及相互乘积。", ["feature interaction", "selection", "forecast"]),
        ("多尺度特征提取", "6/24/168 小时多尺度滚动窗口、趋势-残差分解、短中长周期汇聚。", ["decomposition", "multiscale", "transformer"]),
        ("多源融合门控", "对负荷、天气、节假日、价格、事件等通道使用注意力/门控权重自动加权。", ["attention", "fusion", "graph"]),
    ]

    lines = [
        "# 多源异构数据融合 + 多特征工程优化策略",
        "",
        "## 研究目标",
        "充分利用多源异构数据中的多个特征，通过新增和优化特征工程、多源数据融合策略，提升电力预测精度与稳定性。",
        "",
        "## 策略主线",
        "1. 先做特征清洗与对齐，统一时间粒度与缺失补全。",
        "2. 再做时间、天气、历史负荷、外部事件四类特征扩展。",
        "3. 最后用注意力、门控或图结构把不同来源的特征融合为统一输入。",
        "",
        "## 新增 / 优化特征清单",
    ]
    for name, desc, basis in feature_lines:
        lines.append(f"### {name}")
        lines.append(f"- 描述: {desc}")
        lines.append(f"- 文献依据主题: {', '.join(basis)}")
    lines.extend([
        "",
        "## 文献依据摘记",
    ])
    lines.extend(citations)
    lines.extend([
        "",
        "## 预期收益",
        "- 缩短对单一原始特征的依赖。",
        "- 通过多尺度与交叉特征补足短期波动和长期趋势。",
        "- 通过外部多源数据增强极端峰值和异常时段的可预测性。",
        "",
        "## 落地建议",
        "- XGBoost 侧重显式特征工程和交叉项。",
        "- TimesNet 侧重时序分解、周期特征和天气融合。",
        "- MTGNN 侧重图相关辅助特征和多变量依赖。",
        "- PatchTST 侧重多尺度 patch 编码与时序上下文特征。",
    ])
    return "\n".join(lines)


def build_round_summary(literature_path: Path, strategy_path: Path, metrics_path: Path, code_diff_path: Path, full_log_path: Path) -> str:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    results = metrics.get("results", {})
    improvement = metrics.get("improvement", {})
    feature_summary = {
        "XGBoost": "多源特征交叉 + 时间特征 + 滞后/差分/滚动统计",
        "TimesNet": "时间周期编码 + 滞后/差分/滚动统计",
        "MTGNN": "图时序融合 + 滞后/差分/滚动统计",
        "PatchTST": "Patch 级多尺度编码 + 时间特征",
    }
    lines = [
        f"# Round {ROUND_ID} Summary",
        "",
        "## Basic Info",
        f"- round_dir: {ROUND_DIR.relative_to(ROOT).as_posix()}",
        f"- literature_report: {literature_path.relative_to(ROOT).as_posix()}",
        f"- strategy_doc: {strategy_path.relative_to(ROOT).as_posix()}",
        f"- metrics_json: {metrics_path.relative_to(ROOT).as_posix()}",
        f"- code_changes: {code_diff_path.relative_to(ROOT).as_posix()}",
        f"- execution_log: {full_log_path.relative_to(ROOT).as_posix()}",
        "",
        "## Feature Summary",
    ]
    for model, summary in feature_summary.items():
        lines.append(f"- {model}: {summary}")
    lines.extend([
        "",
        "## Model Comparison",
        "| Model | Variant | MAE | RMSE | SMAPE | WAPE | R2 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for model in ["XGBoost", "TimesNet", "MTGNN", "PatchTST"]:
        for variant in ["baseline", "optimized"]:
            row = results.get(model, {}).get(variant, {})
            lines.append(
                f"| {model} | {variant} | {row.get('MAE', 0):.6f} | {row.get('RMSE', 0):.6f} | {row.get('SMAPE', 0):.6f} | {row.get('WAPE', 0):.6f} | {row.get('R2', 0):.6f} |"
            )
    lines.extend([
        "",
        "## Improvement",
        "| Model | MAE improve % | RMSE improve % | SMAPE improve % | WAPE improve % | R2 gain |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for model in ["XGBoost", "TimesNet", "MTGNN", "PatchTST"]:
        row = improvement.get(model, {})
        lines.append(
            f"| {model} | {row.get('MAE_improve_%', 0):.2f} | {row.get('RMSE_improve_%', 0):.2f} | {row.get('SMAPE_improve_%', 0):.2f} | {row.get('WAPE_improve_%', 0):.2f} | {row.get('R2_gain', 0):.6f} |"
        )
    lines.extend([
        "",
        "## Key Files",
        f"- literature: {literature_path.relative_to(ROOT).as_posix()}",
        f"- strategy: {strategy_path.relative_to(ROOT).as_posix()}",
        f"- metrics: {metrics_path.relative_to(ROOT).as_posix()}",
        f"- code diff: {code_diff_path.relative_to(ROOT).as_posix()}",
        f"- full log: {full_log_path.relative_to(ROOT).as_posix()}",
        "",
        "## Successes",
        "- 特征工程模块已并入四模型输入路径。",
        "- 四模型的基线 / 优化对比表已生成。",
        "- 轮次归档和复盘索引已统一到 rounds/round_2_20260408/。",
        "",
        "## Lessons Learned",
        "- XGBoost 在扩展特征后最容易成为瓶颈，需要控制窗口长度和特征宽度。",
        "- 多源融合报告应优先保留可直接打开的 DOI / arXiv 链接，避免空泛引用。",
        "- 先生成独立日志和归档，再汇总复盘，可以减少长流程中断带来的返工。",
    ])
    return "\n".join(lines)


def copy_if_exists(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        destination.write_bytes(source.read_bytes())
    return destination


def build_code_diff() -> str:
    files = [
        "2_agent_system/1_research_manager/run.py",
        "5_code_base/optimized/power_models/common.py",
        "5_code_base/optimized/power_models/xgboost_model.py",
        "5_code_base/optimized/power_models/timesnet_model.py",
        "5_code_base/optimized/power_models/patchtst_model.py",
        "5_code_base/optimized/power_models/mtgnn_model.py",
        ".vscode/tasks.json",
        "tools/run_round2.cmd",
    ]
    proc = subprocess.run(["git", "diff", "--", *files], cwd=str(ROOT), text=True, capture_output=True, check=False)
    diff_text = proc.stdout.strip()
    if not diff_text:
        diff_text = "No git diff available."
    return diff_text


def main() -> None:
    ROUND_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in [LIT_DIR, HYP_DIR, CHG_DIR, EXP_DIR, LOG_DIR, REPORT_DIR]:
        subdir.mkdir(parents=True, exist_ok=True)

    log("collecting literature candidates")
    queries = [
        "multivariate time series forecasting feature engineering",
        "multi-source data fusion forecasting",
        "heterogeneous data fusion forecasting",
        "multimodal time series forecasting attention",
        "electricity load forecasting weather feature fusion",
        "feature selection time series prediction",
        "feature interaction forecasting",
        "graph-based multivariate forecasting",
    ]
    paper_pool: list[dict] = []
    for query in queries:
        try:
            paper_pool.extend(crossref_search(query, rows=8))
        except Exception as exc:  # pylint: disable=broad-except
            log(f"crossref failed for {query}: {exc}")
    for query in ["multivariate time series forecasting", "feature engineering time series forecasting"]:
        try:
            paper_pool.extend(arxiv_search(query, max_results=5))
        except Exception as exc:  # pylint: disable=broad-except
            log(f"arxiv failed for {query}: {exc}")

    paper_pool = dedupe_papers(paper_pool)
    paper_pool = sorted(paper_pool, key=relevance_score, reverse=True)
    papers = paper_pool[:18]
    if not papers:
        raise RuntimeError("No papers collected from public sources")

    literature_json = {
        "timestamp": datetime.now().isoformat(),
        "round": ROUND_ID,
        "date": ROUND_DATE,
        "keywords": queries,
        "papers": papers,
    }
    lit_json_path = write_text(LIT_DIR / f"auto_literature_round{ROUND_ID}_{ROUND_DATE}.json", json.dumps(literature_json, ensure_ascii=False, indent=2))
    lit_md_path = write_text(LIT_DIR / f"structured_literature_report_round{ROUND_ID}_{ROUND_DATE}.md", build_literature_report(papers))

    log("writing innovation strategy")
    strategy_md_path = write_text(HYP_DIR / f"innovation_round{ROUND_ID}_{ROUND_DATE}.md", build_strategy_document(papers))

    log("running model evaluation pipeline")
    pipeline_proc = subprocess.run(
        [PYTHON, str(PIPELINE_SCRIPT)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    pipeline_log_path = write_text(LOG_DIR / f"round_{ROUND_ID}_{ROUND_DATE}_pipeline.log", (pipeline_proc.stdout or "") + "\n\n[stderr]\n" + (pipeline_proc.stderr or ""))
    if pipeline_proc.returncode != 0:
        raise RuntimeError(f"pipeline failed with exit code {pipeline_proc.returncode}, log={pipeline_log_path}")

    metrics_json_candidates = [
        WORKSPACE_REPORT / "round_fixed_metrics.json",
        WORKSPACE_KNOWLEDGE / "round_fixed_metrics.json",
    ]
    metrics_json = next((path for path in metrics_json_candidates if path.exists()), None)
    if metrics_json is None:
        raise RuntimeError("round_fixed_metrics.json was not produced")
    metrics_copy = copy_if_exists(metrics_json, EXP_DIR / f"round_fixed_metrics_round{ROUND_ID}_{ROUND_DATE}.json")
    report_copy = copy_if_exists((WORKSPACE_REPORT / "FINAL_RESEARCH_REPORT_FIXED_ROUND.md"), EXP_DIR / f"FINAL_RESEARCH_REPORT_FIXED_ROUND_round{ROUND_ID}_{ROUND_DATE}.md")

    log("building code diff")
    code_diff_text = build_code_diff()
    code_diff_path = write_text(CHG_DIR / f"code_changes_round{ROUND_ID}_{ROUND_DATE}.diff", code_diff_text)

    log("building round summary")
    summary_md = build_round_summary(lit_md_path, strategy_md_path, metrics_copy, code_diff_path, pipeline_log_path)
    summary_path = write_text(ROUND_DIR / "round_summary.md", summary_md)

    final_log_lines = [
        f"round_dir={ROUND_DIR.relative_to(ROOT).as_posix()}",
        f"literature_json={lit_json_path.relative_to(ROOT).as_posix()}",
        f"literature_report={lit_md_path.relative_to(ROOT).as_posix()}",
        f"strategy_doc={strategy_md_path.relative_to(ROOT).as_posix()}",
        f"metrics_json={metrics_copy.relative_to(ROOT).as_posix()}",
        f"report_copy={report_copy.relative_to(ROOT).as_posix() if report_copy.exists() else 'missing'}",
        f"code_diff={code_diff_path.relative_to(ROOT).as_posix()}",
        f"summary={summary_path.relative_to(ROOT).as_posix()}",
    ]
    write_text(LOG_DIR / f"round_{ROUND_ID}_{ROUND_DATE}_asset_generation.log", "\n".join(LOG_LINES + ["", *final_log_lines]))
    log("round-2 asset generation complete")
    for line in final_log_lines:
        print(line)


if __name__ == "__main__":
    main()
