"""
Crossref 文献下载器 - 零密钥、免费、无限制
Crossref 是全球最大学术索引 API：
- 无需注册、无需密钥
- 永久免费、无请求限制
- 覆盖 90% 英文学术文献
- 支持 PDF 直链获取

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


class CrossrefDownloader:
    """Crossref 文献下载器 - 零门槛"""
    
    def __init__(self, max_results=20, request_interval=1.0):
        """
        初始化下载器
        
        Args:
            max_results: 最大检索结果数
            request_interval: 请求间隔秒数
        """
        self.max_results = max_results
        self.request_interval = request_interval
        self.api_url = "https://api.crossref.org/works"
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
        
        # 请求头（礼貌模式）
        self.headers = {
            'User-Agent': 'DARIS-Research-Bot/1.0 (mailto:disdorqin@qq.com)'
        }
    
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
        logger.info("Crossref 文献下载开始（零密钥、免费、无限制）")
        logger.info("=" * 60)
        
        for kw in keywords:
            logger.info(f"\n检索关键词：{kw}")
            
            try:
                # 执行检索
                params = {
                    'query': kw,
                    'rows': self.max_results,
                    'select': 'DOI,title,author,published,URL,link,abstract',
                    'sort': 'relevance',
                    'order': 'desc'
                }
                
                response = requests.get(self.api_url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items = data.get('message', {}).get('items', [])
                
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
        logger.info("Crossref 文献下载完成")
        logger.info(f"成功：{self.stats['success_count']} 篇")
        logger.info(f"失败：{self.stats['failed_count']} 篇")
        logger.info("=" * 60)
    
    def _process_item(self, item, index):
        """处理单篇文献"""
        try:
            # 提取元数据
            doi = item.get('DOI', '')
            title = item.get('title', ['Unknown'])[0]
            authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() 
                      for a in item.get('author', [])]
            published = item.get('published', {}).get('date-parts', [['Unknown']])[0]
            published_str = '-'.join(str(p) for p in published)
            
            # 获取 PDF 链接
            pdf_url = None
            links = item.get('link', [])
            for link in links:
                if link.get('content-type') == 'application/pdf':
                    pdf_url = link.get('URL')
                    break
            
            if not pdf_url:
                logger.info(f"  [{index}] 无 PDF 链接，跳过：{title[:40]}...")
                return
            
            # 生成文件名
            safe_doi = doi.replace('/', '_').replace(':', '_')
            safe_title = title[:30].replace('/', '_').replace('\\', '_')
            filename = f"crossref_{safe_doi}_{safe_title}.pdf"
            filepath = self.download_dir / filename
            
            # 检查是否已下载
            if filepath.exists():
                logger.info(f"  [{index}] 已存在，跳过")
                return
            
            # 下载 PDF
            logger.info(f"  [{index}] 下载：{title[:40]}...")
            pdf_response = requests.get(pdf_url, headers=self.headers, timeout=60)
            
            if pdf_response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(pdf_response.content)
                
                # 保存元数据
                metadata = {
                    'doi': doi,
                    'title': title,
                    'authors': authors,
                    'published': published_str,
                    'pdf_url': pdf_url,
                    'download_time': datetime.now().isoformat(),
                    'source': 'Crossref'
                }
                
                metadata_file = self.metadata_dir / f"crossref_{safe_doi}_metadata.json"
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
        stats_file = self.metadata_dir / 'crossref_download_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crossref 文献下载器')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['power load forecasting', 'time series forecasting'],
                        help='检索关键词')
    parser.add_argument('--max-results', type=int, default=10,
                        help='最大结果数')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='请求间隔秒数')
    
    args = parser.parse_args()
    
    downloader = CrossrefDownloader(
        max_results=args.max_results,
        request_interval=args.interval
    )
    downloader.search_and_download(args.keywords)


if __name__ == '__main__':
    main()