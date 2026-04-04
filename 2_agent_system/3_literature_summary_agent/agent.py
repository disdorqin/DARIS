from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from base_agent import BaseAgent, AgentIO


class LiteratureSummaryAgent(BaseAgent):
    """
    文献阅读与结构化解析智能体（环节 2）
    
    绑定开源项目:
    - PaperAgent: github.com/THUDM/PaperAgent
    - Zotero-GPT: github.com/MuiseDestiny/zotero-gpt
    
    复用核心模块:
    - 科研知识图谱构建模块
    - 文献全文结构化解析模块
    - 核心方法拆解模块
    - 研究脉络梳理模块
    
    指定执行大模型：kimi-k2.5（文本解析专用）
    兜底备用模型：qwen3.5-plus
    """
    
    name = "literature_summary_agent"
    description = "文献阅读与结构化解析智能体"
    
    # 绑定的开源项目仓库
    BOUND_REPOS = {
        "paperagent": "https://github.com/THUDM/PaperAgent",
        "zotero_gpt": "https://github.com/MuiseDestiny/zotero-gpt",
    }
    
    # PaperAgent 核心模块模拟
    PAPERAGENT_MODULES = {
        "knowledge_graph": "科研知识图谱构建",
        "structure_parse": "文献全文结构化解析",
        "method_extract": "核心方法拆解",
        "context_trace": "研究脉络梳理",
    }
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        super().__init__(env)
        self.summary_dir = Path(__file__).resolve().parents[2] / "3_literature_workflow" / "structured_summary"
        self.zotero_config = {
            "api_key": self.env.get("ZOTERO_API_KEY", ""),
            "user_id": self.env.get("ZOTERO_USER_ID", ""),
        }
    
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        """验证输入"""
        super().validate_inputs(payload)
        required_fields = ["papers"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
    
    def parse_paper_structure(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 PaperAgent 风格解析文献结构
        
        Args:
            paper: 文献元数据
        
        Returns:
            结构化解析结果
        """
        self.log(f"解析文献结构：{paper.get('title', '')[:50]}...")
        
        # 使用 kimi-k2.5 进行结构化解析
        system_prompt = """你是 PaperAgent 文献解析专家，请严格按照以下格式输出结构化分析结果：

1. 研究问题（Research Question）
2. 核心方法（Core Method）
3. 技术路线（Technical Approach）
4. 实验设计（Experimental Design）
5. 主要贡献（Main Contributions）
6. 局限性（Limitations）

请用中文输出，保持简洁专业。"""
        
        user_prompt = f"""请解析以下文献：

标题：{paper.get('title', '')}
作者：{', '.join(paper.get('authors', []))}
年份：{paper.get('year', 'N/A')}
摘要：{paper.get('abstract', 'N/A')}
DOI: {paper.get('doi', 'N/A')}
URL: {paper.get('url', 'N/A')}

请输出完整的结构化解析结果。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="literature",  # 使用 kimi-k2.5
        )
        
        self.log(f"文献解析完成，使用模型：{model_used}")
        
        return {
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "parsed_structure": response,
            "model_used": model_used,
            "parse_timestamp": datetime.now().isoformat(),
        }
    
    def extract_core_methods(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        从多篇文献中提取核心方法库
        
        Args:
            papers: 文献列表
        
        Returns:
            核心方法库
        """
        self.log(f"从 {len(papers)} 篇文献中提取核心方法")
        
        # 准备文献摘要
        paper_summaries = []
        for i, paper in enumerate(papers[:15], 1):  # 限制处理数量
            summary = f"""{i}. {paper.get('title', '')}
   作者：{', '.join(paper.get('authors', [])[:3])}
   年份：{paper.get('year', 'N/A')}
   摘要：{paper.get('abstract', 'N/A')[:300]}"""
            paper_summaries.append(summary)
        
        system_prompt = """你是科研方法分析专家，请从以下文献列表中提取核心方法，按以下格式输出：

## 核心方法库

### 方法名称
- 来源文献：[文献标题]
- 方法描述：[简要描述]
- 适用场景：[适用场景]
- 优缺点：[优缺点分析]

请聚焦于时序预测、图神经网络、特征工程等相关方法。"""
        
        user_prompt = "\n".join(paper_summaries)
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="literature",
        )
        
        self.log(f"核心方法提取完成，使用模型：{model_used}")
        
        return {
            "method_library": response,
            "paper_count": len(papers),
            "model_used": model_used,
            "extract_timestamp": datetime.now().isoformat(),
        }
    
    def build_research_context(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        构建研究脉络（知识图谱）
        
        Args:
            papers: 文献列表
        
        Returns:
            研究脉络分析
        """
        self.log("构建研究脉络图谱")
        
        # 准备文献数据
        paper_data = []
        for paper in papers[:15]:
            paper_data.append({
                "title": paper.get("title", ""),
                "year": paper.get("year", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", "")[:200],
            })
        
        system_prompt = """你是科研脉络分析专家，请分析以下文献并输出：

1. 研究演进脉络（按时间线梳理关键节点）
2. 主要研究流派（按方法/理论分类）
3. 研究热点与趋势
4. 可利用的研究空白

请用结构化格式输出，适合后续分析使用。"""
        
        user_prompt = "文献列表:\n" + "\n".join(
            f"- {p['title']} ({p['year']}) - {p['abstract'][:100]}..."
            for p in paper_data
        )
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="literature",
        )
        
        self.log(f"研究脉络构建完成，使用模型：{model_used}")
        
        return {
            "research_context": response,
            "paper_count": len(papers),
            "model_used": model_used,
            "build_timestamp": datetime.now().isoformat(),
        }
    
    def summarize_research_gap(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        总结研究空白与可利用方向
        
        Args:
            papers: 文献列表
        
        Returns:
            研究空白分析
        """
        self.log("分析研究空白")
        
        system_prompt = """你是科研创新方向分析专家，请基于以下文献分析：

1. 现有研究的共同缺陷
2. 尚未解决的问题
3. 可利用的研究空白
4. 建议的创新方向（针对 MTGNN/TimesNet/XGBoost 基线模型）

请输出具体、可执行的创新建议。"""
        
        # 准备文献摘要
        abstracts = [p.get("abstract", "")[:200] for p in papers[:10]]
        user_prompt = "文献摘要:\n" + "\n---\n".join(abstracts)
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="literature",
        )
        
        self.log(f"研究空白分析完成，使用模型：{model_used}")
        
        return {
            "research_gaps": response,
            "model_used": model_used,
            "analyze_timestamp": datetime.now().isoformat(),
        }
    
    def save_summary(self, results: Dict[str, Any]) -> Path:
        """保存解析结果"""
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存 JSON 格式
        json_path = self.summary_dir / f"summary_{timestamp}.json"
        json_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 保存 Markdown 格式
        md_path = self.summary_dir / f"summary_{timestamp}.md"
        md_content = f"""# 文献阅读与结构化解析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**处理文献数**: {results.get('paper_count', len(results.get('papers', [])))}
**使用模型**: {results.get('model_used', 'N/A')}

---

## 1. 单篇文献结构化解析

{results.get('parsed_papers', '暂无数据')}

---

## 2. 核心方法库

{results.get('core_methods', {}).get('method_library', '暂无数据')}

---

## 3. 研究脉络图谱

{results.get('research_context', {}).get('research_context', '暂无数据')}

---

## 4. 研究空白与利用方向

{results.get('research_gaps', {}).get('research_gaps', '暂无数据')}

---

## 执行日志

```
{chr(10).join(results.get('execution_log', []))}
```
"""
        md_path.write_text(md_content, encoding="utf-8")
        
        self.log(f"解析结果已保存：{md_path}")
        
        return md_path
    
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        """
        执行文献阅读与结构化解析
        
        Args:
            payload: 包含 papers 列表或 literature_path
        
        Returns:
            AgentIO 包含解析结果
        """
        self.validate_inputs(payload)
        
        papers = payload.get("papers", [])
        literature_path = payload.get("literature_path")
        
        # 如果提供了文献路径，从文件加载
        if literature_path and not papers:
            lit_path = Path(literature_path)
            if lit_path.exists():
                data = json.loads(lit_path.read_text(encoding="utf-8"))
                papers = data.get("papers", [])
                self.log(f"从 {literature_path} 加载了 {len(papers)} 篇文献")
        
        if not papers:
            return AgentIO(
                inputs=payload,
                outputs={
                    "status": "error",
                    "message": "No papers provided or loaded",
                }
            )
        
        self.log(f"开始文献解析，共 {len(papers)} 篇文献")
        
        results = {
            "paper_count": len(papers),
            "papers": papers,
            "parsed_papers": [],
            "core_methods": {},
            "research_context": {},
            "research_gaps": {},
            "execution_log": [],
        }
        
        # 1. 单篇文献结构化解析（限制数量）
        parsed_papers = []
        for paper in papers[:5]:  # 限制解析数量
            try:
                parsed = self.parse_paper_structure(paper)
                parsed_papers.append(parsed)
            except Exception as e:
                self.log(f"解析失败 {paper.get('title', '')}: {e}")
        
        results["parsed_papers"] = parsed_papers
        
        # 2. 核心方法提取
        results["core_methods"] = self.extract_core_methods(papers)
        
        # 3. 研究脉络构建
        results["research_context"] = self.build_research_context(papers)
        
        # 4. 研究空白分析
        results["research_gaps"] = self.summarize_research_gap(papers)
        
        results["execution_log"] = self.get_execution_log()
        
        # 保存结果
        summary_path = self.save_summary(results)
        
        # 保存调用日志
        log_dir = Path(__file__).resolve().parents[2] / "7_monitor_system" / "system_log"
        self.llm_client.save_call_log(log_dir / f"literature_summary_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        result = {
            "status": "completed",
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "paper_count": len(papers),
            "summary_path": str(summary_path),
            "parsed_papers_count": len(parsed_papers),
            "model_used": "kimi-k2.5",
            "execution_log": self.get_execution_log(),
        }
        
        return AgentIO(inputs=payload, outputs=result)