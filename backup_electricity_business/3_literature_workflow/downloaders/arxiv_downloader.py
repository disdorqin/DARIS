"""
arXiv 文献下载器 - 修复 429 限流版本
核心修复：
- 强制请求间隔 5 秒（超过官方 3 秒限制）
- 单线程运行，禁止并发
- 指数退避重试机制
- 最大请求数限制

作者：DARIS 团队
日期：2026-04-01
"""

import os
import time
import json
import logging
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

# 尝试导入 arxiv 库
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    logger.warning("arxiv 库未安装，运行：pip install arxiv")


class ArxivDownloader:
    """arXiv 文献下载器 - 带限流保护"""
    
    def __init__(self, max_results=20, request_interval=5.0):
        """
        初始化下载器
        
        Args:
            max_results: 最大检索结果数（默认 20，避免触发限流）
            request_interval: 请求间隔秒数（默认 5 秒，超过官方 3 秒限制）
        """
        self.max_results = max_results
        self.request_interval = request_interval
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
    
    def _exponential_backoff(self, attempt, base_delay=10):
        """指数退避等待"""
        delay = base_delay * (2 ** attempt)
        logger.info(f"  等待 {delay}秒后重试...")
        time.sleep(delay)
    
    def search_and_download(self, keywords, max_retries=3):
        """
        检索并下载文献
        
        Args:
            keywords: 检索关键词（字符串或列表）
            max_retries: 最大重试次数
        """
        if not ARXIV_AVAILABLE:
            logger.error("arxiv 库不可用，跳过下载")
            return
        
        if isinstance(keywords, str):
            keywords = [keywords]
        
        logger.info("=" * 60)
        logger.info("arXiv 文献下载开始")
        logger.info("=" * 60)
        
        for kw in keywords:
            logger.info(f"\n检索关键词：{kw}")
            logger.info(f"最大结果数：{self.max_results}, 请求间隔：{self.request_interval}秒")
            
            for attempt in range(max_retries):
                try:
                    # 执行检索（单线程，慢速）
                    search = arxiv.Search(
                        query=kw,
                        max_results=self.max_results,
                        sort_by=arxiv.SortCriterion.Relevance
                    )
                    
                    # 逐个下载（带间隔）
                    for i, result in enumerate(search.results()):
                        self._process_result(result, i + 1)
                        
                        # 强制间隔，防止 429
                        if i < len(list(search.results())) - 1:
                            logger.info(f"  等待 {self.request_interval}秒防止限流...")
                            time.sleep(self.request_interval)
                    
                    logger.info(f"✓ 关键词 '{kw}' 检索完成")
                    break  # 成功则跳出重试循环
                    
                except arxiv.HTTPError as e:
                    if e.status == 429:
                        logger.warning(f"⚠ 触发 429 限流（第{attempt + 1}次）")
                        self._exponential_backoff(attempt)
                    else:
                        logger.error(f"✗ arXiv API 错误：{e}")
                        break
                except Exception as e:
                    logger.error(f"✗ 未知错误：{e}")
                    break
        
        # 保存统计
        self._save_stats()
        
        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("arXiv 文献下载完成")
        logger.info(f"成功：{self.stats['success_count']} 篇")
        logger.info(f"失败：{self.stats['failed_count']} 篇")
        logger.info(f"保存目录：{self.download_dir.absolute()}")
        logger.info("=" * 60)
    
    def _process_result(self, result, index):
        """处理单篇文献"""
        try:
            # 生成文件名
            arxiv_id = result.get_short_id()
            safe_title = result.title[:50].replace('/', '_').replace('\\', '_')
            filename = f"arxiv_{arxiv_id}_{safe_title}.pdf"
            filepath = self.download_dir / filename
            
            # 检查是否已下载
            if filepath.exists():
                logger.info(f"  [{index}] 已存在，跳过：{result.title[:40]}...")
                return
            
            # 下载 PDF
            logger.info(f"  [{index}] 下载：{result.title[:40]}...")
            result.download_pdf(filename=str(filepath))
            
            # 保存元数据
            metadata = {
                'title': result.title,
                'authors': [str(a) for a in result.authors],
                'published': str(result.published),
                'arxiv_id': arxiv_id,
                'categories': result.categories,
                'summary': result.summary[:500] if len(result.summary) > 500 else result.summary,
                'pdf_url': result.pdf_url,
                'download_time': datetime.now().isoformat(),
                'source': 'arXiv'
            }
            
            metadata_file = self.metadata_dir / f"arxiv_{arxiv_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.stats['success_count'] += 1
            self.stats['downloaded_files'].append(filename)
            logger.info(f"  ✓ 下载成功")
            
        except Exception as e:
            logger.error(f"  ✗ 处理失败：{e}")
            self.stats['failed_count'] += 1
            self.stats['failed_files'].append(str(result.get_short_id()))
    
    def _save_stats(self):
        """保存统计信息"""
        stats_file = self.metadata_dir / 'arxiv_download_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='arXiv 文献下载器')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['power load forecasting', 'time series forecasting'],
                        help='检索关键词')
    parser.add_argument('--max-results', type=int, default=10,
                        help='最大结果数（默认 10，避免限流）')
    parser.add_argument('--interval', type=float, default=5.0,
                        help='请求间隔秒数（默认 5 秒）')
    
    args = parser.parse_args()
    
    downloader = ArxivDownloader(
        max_results=args.max_results,
        request_interval=args.interval
    )
    downloader.search_and_download(args.keywords)


if __name__ == '__main__':
    main()