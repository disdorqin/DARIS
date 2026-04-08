from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from base_agent import BaseAgent, AgentIO


class LiteratureAgent(BaseAgent):
    """
    文献检索与归档智能体（环节 1）
    
    绑定开源项目:
    - OpenResearch: github.com/OpenResearchAI/OpenResearch
    - Zotero-GPT: github.com/MuiseDestiny/zotero-gpt
    
    复用核心模块:
    - 多源学术 API 集成检索模块
    - Zotero 自动归档模块
    - PDF 元数据补全模块
    - 文献去重过滤模块
    
    指定执行大模型：kimi-k2.5
    兜底备用模型：qwen3.5-plus
    """
    
    name = "literature_agent"
    description = "文献检索与归档智能体"
    
    # 绑定的开源项目仓库
    BOUND_REPOS = {
        "openresearch": "https://github.com/OpenResearchAI/OpenResearch",
        "zotero_gpt": "https://github.com/MuiseDestiny/zotero-gpt",
    }
    
    # 学术 API 端点
    ACADEMIC_APIS = {
        "semantic_scholar": "https://api.semanticscholar.org/graph/v1/paper/search",
        "arxiv": "https://export.arxiv.org/api/query",
        "crossref": "https://api.crossref.org/works",
    }
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        super().__init__(env)
        self.literature_dir = Path(__file__).resolve().parents[2] / "3_literature_workflow" / "literature_asset"
        self.zotero_config = {
            "api_key": self.env.get("ZOTERO_API_KEY", ""),
            "user_id": self.env.get("ZOTERO_USER_ID", ""),
            "library_type": self.env.get("ZOTERO_LIBRARY_TYPE", "user"),
            "collection_name": self.env.get("ZOTERO_COLLECTION_NAME", "DARIS"),
        }
    
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        """验证输入"""
        super().validate_inputs(payload)
        required_fields = ["keywords"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
    
    def search_literature(
        self,
        keywords: List[str],
        limit_per_keyword: int = 10,
        sources: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        多源学术 API 检索文献
        
        Args:
            keywords: 搜索关键词列表
            limit_per_keyword: 每个关键词的文献数量限制
            sources: 数据源列表，默认使用所有源
        
        Returns:
            文献列表
        """
        if sources is None:
            sources = ["crossref", "arxiv"]
        
        all_papers = []
        
        for keyword in keywords:
            self.log(f"正在检索关键词：{keyword}")
            
            for source in sources:
                try:
                    papers = self._search_source(source, keyword, limit_per_keyword)
                    all_papers.extend(papers)
                    self.log(f"从 {source} 检索到 {len(papers)} 篇文献")
                except Exception as e:
                    self.log(f"从 {source} 检索失败：{e}")
                
                time.sleep(0.5)  # 避免 API 限流
        
        # 去重
        unique_papers = self._deduplicate_papers(all_papers)
        self.log(f"去重后共 {len(unique_papers)} 篇文献")
        
        return unique_papers
    
    def _search_source(self, source: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """从指定数据源检索文献"""
        import requests
        
        if source == "crossref":
            return self._search_crossref(keyword, limit)
        elif source == "arxiv":
            return self._search_arxiv(keyword, limit)
        elif source == "semantic_scholar":
            return self._search_semantic_scholar(keyword, limit)
        else:
            return []
    
    def _search_crossref(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """CrossRef API 检索"""
        import requests
        
        params = {
            "query": keyword,
            "rows": limit,
            "sort": "relevance",
            "order": "desc",
        }
        
        resp = requests.get(self.ACADEMIC_APIS["crossref"], params=params, timeout=30)
        resp.raise_for_status()
        
        items = resp.json().get("message", {}).get("items", [])
        papers = []
        
        for item in items:
            title = item.get("title", [""])[0] if item.get("title") else ""
            abstract = item.get("abstract", "")
            authors = []
            for author in item.get("author", [])[:5]:
                name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                if name:
                    authors.append(name)
            
            papers.append({
                "source": "crossref",
                "title": title,
                "doi": item.get("DOI", ""),
                "year": item.get("created", {}).get("date-parts", [[None]])[0][0],
                "url": item.get("URL", ""),
                "authors": authors,
                "abstract": abstract,
                "keyword": keyword,
            })
        
        return papers
    
    def _search_arxiv(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """arXiv API 检索"""
        import requests
        import urllib.parse
        
        query = urllib.parse.quote(f"all:{keyword}")
        url = f"{self.ACADEMIC_APIS['arxiv']}?search_query={query}&start=0&max_results={limit}&sortBy=relevance&sortOrder=descending"
        
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        # 解析 Atom XML
        papers = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            for entry in root.findall("atom:entry", ns)[:limit]:
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                id_elem = entry.find("atom:id", ns)
                
                title = title_elem.text.strip() if title_elem is not None else ""
                summary = summary_elem.text.strip() if summary_elem is not None else ""
                paper_id = id_elem.text if id_elem is not None else ""
                
                # 获取作者
                authors = []
                for author in entry.findall("atom:author", ns)[:5]:
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                
                # 获取年份
                published_elem = entry.find("atom:published", ns)
                year = None
                if published_elem is not None and published_elem.text:
                    year = published_elem.text[:4]
                
                papers.append({
                    "source": "arxiv",
                    "title": title,
                    "doi": paper_id,
                    "year": year,
                    "url": paper_id,
                    "authors": authors,
                    "abstract": summary,
                    "keyword": keyword,
                })
        except Exception as e:
            self.log(f"解析 arXiv 响应失败：{e}")
        
        return papers
    
    def _search_semantic_scholar(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Semantic Scholar API 检索"""
        import requests
        
        api_key = self.env.get("SEMANTIC_SCHOLAR_API_KEY")
        headers = {"x-api-key": api_key} if api_key else {}
        
        params = {
            "query": keyword,
            "limit": limit,
            "fields": "title,authors,year,abstract,externalIds,url",
        }
        
        resp = requests.get(
            self.ACADEMIC_APIS["semantic_scholar"],
            params=params,
            headers=headers,
            timeout=30
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        papers = []
        
        for item in data.get("data", []):
            papers.append({
                "source": "semantic_scholar",
                "title": item.get("title", ""),
                "doi": item.get("externalIds", {}).get("DOI", ""),
                "year": item.get("year"),
                "url": item.get("url", ""),
                "authors": [a.get("name", "") for a in item.get("authors", [])][:5],
                "abstract": item.get("abstract", ""),
                "keyword": keyword,
            })
        
        return papers
    
    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """文献去重"""
        seen = set()
        unique = []
        
        for paper in papers:
            # 使用 DOI 或 title 作为去重键
            key = paper.get("doi", "") or paper.get("title", "").lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(paper)
        
        return unique
    
    def archive_to_zotero(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将文献归档到 Zotero
        
        Args:
            papers: 文献列表
        
        Returns:
            归档结果
        """
        import requests
        
        if not self.zotero_config["api_key"]:
            self.log("未配置 Zotero API Key，跳过归档")
            return {"status": "skipped", "reason": "no_api_key"}
        
        base_url = f"https://api.zotero.org/users/{self.zotero_config['user_id']}/items"
        headers = {
            "Zotero-API-Key": self.zotero_config["api_key"],
            "Content-Type": "application/json",
        }
        
        archived = []
        failed = []
        
        for paper in papers:
            try:
                # 创建 Zotero 条目
                item_data = {
                    "itemType": "journalArticle",
                    "title": paper.get("title", ""),
                    "abstractNote": paper.get("abstract", ""),
                    "creators": [
                        {"creatorType": "author", "firstName": name.split()[0] if name else "", "lastName": " ".join(name.split()[1:]) if name else ""}
                        for name in paper.get("authors", [])
                    ],
                    "date": str(paper.get("year", "")),
                    "DOI": paper.get("doi", ""),
                    "url": paper.get("url", ""),
                    "tags": [{"tag": paper.get("keyword", ""), "type": 1}],
                }
                
                resp = requests.post(base_url, headers=headers, json=item_data, timeout=30)
                
                if resp.status_code in [200, 201]:
                    archived.append(paper.get("title", ""))
                else:
                    failed.append({"title": paper.get("title", ""), "error": resp.text[:100]})
                
                time.sleep(0.1)  # Zotero API 限流
                
            except Exception as e:
                failed.append({"title": paper.get("title", ""), "error": str(e)})
        
        return {
            "status": "completed",
            "archived_count": len(archived),
            "failed_count": len(failed),
            "archived_titles": archived,
            "failed_items": failed,
        }
    
    def save_literature_list(self, papers: List[Dict[str, Any]]) -> Path:
        """保存文献列表到本地"""
        self.literature_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.literature_dir / f"literature_list_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_count": len(papers),
            "papers": papers,
        }
        
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log(f"文献列表已保存：{output_path}")
        
        return output_path
    
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        """
        执行文献检索与归档
        
        Args:
            payload: 包含 keywords, limit 等参数
        
        Returns:
            AgentIO 包含检索结果和归档状态
        """
        self.validate_inputs(payload)
        
        keywords = payload.get("keywords", [])
        limit = payload.get("limit", 10)
        sources = payload.get("sources", ["crossref", "arxiv"])
        archive = payload.get("archive", True)
        
        self.log(f"开始文献检索，关键词：{keywords}")
        
        # 检索文献
        papers = self.search_literature(keywords, limit, sources)
        
        # 保存文献列表
        literature_path = self.save_literature_list(papers)
        
        # 归档到 Zotero
        archive_result = {"status": "skipped"}
        if archive and papers:
            self.log("开始归档到 Zotero")
            archive_result = self.archive_to_zotero(papers)
        
        result = {
            "status": "completed",
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "papers_found": len(papers),
            "literature_path": str(literature_path),
            "archive_result": archive_result,
            "execution_log": self.get_execution_log(),
        }
        
        # 保存调用日志
        log_dir = Path(__file__).resolve().parents[2] / "7_monitor_system" / "system_log"
        self.llm_client.save_call_log(log_dir / f"literature_agent_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        return AgentIO(inputs=payload, outputs=result)