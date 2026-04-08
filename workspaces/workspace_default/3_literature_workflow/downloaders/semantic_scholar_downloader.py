"""
Semantic Scholar 文献下载器 - 个人免费 API
申请教程（1 分钟搞定）：
1. 访问：https://www.semanticscholar.org/product/api
2. 点击"Request API Key"
3. 填写邮箱，提交
4. 立即收到 API 密钥（邮件）
5. 将密钥填入.env 的 SEMANTIC_SCHOLAR_API_KEY

无密钥也能运行（使用公开 API，有限额）

作者：DARIS 团队
日期：2026-04-01
"""

import os
import time
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SemanticScholarDownloader:
    """Semantic Scholar 文献下载器"""
    
    def __init__(self, api_key=None, max_results=20, request_interval=1.0):
        """
        初始化下载器
        
        Args:
            api_key: Semantic Scholar API 密钥（可选）
            max_results: 最大检索结果数
            request_interval: 请求间隔秒数
        """
        self.api_key = api_key or os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        self.max_results = max_results
        self.request_interval = request_interval
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.download_dir = Path('literature/pdf')
        self.metadata_dir = Path('literature/structured')
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.stats = {
            'success_count': 0,
            'failed_count': 0,
            'downloaded_files': [],
            'failed_files': []
        }
        
        # 请求头
        self.headers = {}
        if self.api_key:
            self.headers['x-api-key'] = self.api_key
            logger.info("使用 API 密钥模式（无限制）")
        else:
            logger.info("使用公开 API 模式（有限额，建议申请免费密钥）")
    
    def search_and_download(self, keywords, max_retries=3):
        """
        检索并下载文献
        
        Args:
            keywords: 检索关键词
            max_retries: 最大重试次数
        """
        if isinstance(keywords, str):
            keywords = [keywords]
        
        logger.info("=" * 60)
        logger.info("Semantic Scholar 文献下载开始")
        logger.info("=" * 60)
        
        for kw in keywords:
            logger.info(f"\n检索关键词：{kw}")
            
            try:
                # 执行检索
                params = {
                    'query': kw,
                    'limit': self.max_results,
                    'fields': 'title,authors,year,venue,doi,url,abstract,openAccessPdf'
                }
                
                response = requests.get(self.base_url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items = data.get('data', [])
                
                logger.info(f"检索到 {len(items)} 篇文献")
                
                # 处理每篇文献
                for i, item in enumerate(items):
                    self._process_item(item, i + 1)
                    time.sleep(self.request_interval)
                
                logger.info(f"✓ 关键词 '{kw}' 检索完成")
                
            except Exception as e:
                logger.error(f"✗ 检索失败：{e}")
        
        # 保存统计
        self._save_stats()
        
        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("Semantic Scholar 文献下载完成")
        logger.info(f"成功：{self.stats['success_count']} 篇")
        logger.info(f"失败：{self.stats['failed_count']} 篇")
        logger.info("=" * 60)
    
    def _process_item(self, item, index):
        """处理单篇文献"""
        try:
            # 提取元数据
            doi = item.get('doi', '')
            title = item.get('title', 'Unknown')
            authors = [a.get('name', 'Unknown') for a in item.get('authors', [])]
            year = item.get('year', 'Unknown')
            venue = item.get('venue', 'Unknown')
            abstract = item.get('abstract', 'No abstract available')
            
            # 获取 PDF 链接
            pdf_url = None
            open_access = item.get('openAccessPdf', {})
            if open_access and open_access.get('url'):
                pdf_url = open_access['url']
            
            if not pdf_url:
                logger.info(f"  [{index}] 无 PDF 链接，跳过：{title[:40]}...")
                return
            
            # 生成文件名
            safe_doi = doi.replace('/', '_').replace(':', '_') if doi else f"no_doi_{index}"
            safe_title = title[:30].replace('/', '_').replace('\\', '_')
            filename = f"semantic_{safe_doi}_{safe_title}.pdf"
            filepath = self.download_dir / filename
            
            # 检查是否已下载
            if filepath.exists():
                logger.info(f"  [{index}] 已存在，跳过")
                return
            
            # 下载 PDF
            logger.info(f"  [{index}] 下载：{title[:40]}...")
            pdf_response = requests.get(pdf_url, timeout=60)
            
            if pdf_response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(pdf_response.content)
                
                # 保存元数据
                metadata = {
                    'doi': doi,
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'venue': venue,
                    'abstract': abstract,
                    'pdf_url': pdf_url,
                    'download_time': datetime.now().isoformat(),
                    'source': 'Semantic Scholar'
                }
                
                metadata_file = self.metadata_dir / f"semantic_{safe_doi}_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                self.stats['success_count'] += 1
                self.stats['downloaded_files'].append(filename)
                logger.info(f"  ✓ 下载成功")
            else:
                logger.warning(f"  ✗ PDF 下载失败：HTTP {pdf_response.status_code}")
                self.stats['failed_count'] += 1
                self.stats['failed_files'].append(doi)
                
        except Exception as e:
            logger.error(f"  ✗ 处理失败：{e}")
            self.stats['failed_count'] += 1
    
    def _save_stats(self):
        """保存统计信息"""
        stats_file = self.metadata_dir / 'semantic_download_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Semantic Scholar 文献下载器')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['power load forecasting', 'time series forecasting'],
                        help='检索关键词')
    parser.add_argument('--max-results', type=int, default=10,
                        help='最大结果数')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='请求间隔秒数')
    parser.add_argument('--api-key', type=str, default=None,
                        help='Semantic Scholar API 密钥（可选）')
    
    args = parser.parse_args()
    
    downloader = SemanticScholarDownloader(
        api_key=args.api_key,
        max_results=args.max_results,
        request_interval=args.interval
    )
    downloader.search_and_download(args.keywords)


if __name__ == '__main__':
    main()