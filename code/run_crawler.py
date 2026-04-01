"""
DARIS 文献爬取引擎启动脚本
基于 Selenium 的学术文献自动爬取

使用方法:
    # 爬取 Google Scholar
    python run_crawler.py --source google --keywords "MTGNN" "TimesNet"
    
    # 爬取 CNKI（需要校园网/机构订阅）
    python run_crawler.py --source cnki --keywords "MTGNN" "时序预测"
    
    # 无头模式（后台运行）
    python run_crawler.py --headless --keywords "MTGNN"
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.crawler.literature_crawler import (
    LiteratureCrawler,
    CNKI_CONFIG,
    GOOGLE_SCHOLAR_CONFIG
)


def run_crawler(
    keywords,
    source='google',
    max_results=5,
    headless=False
):
    """运行文献爬取器"""
    
    # 选择搜索配置
    if source.lower() == 'cnki':
        config = CNKI_CONFIG
        print("\n" + "=" * 60)
        print("使用 CNKI 搜索（需要校园网/机构订阅）")
        print("=" * 60)
    else:
        config = GOOGLE_SCHOLAR_CONFIG
        print("\n" + "=" * 60)
        print("使用 Google Scholar 搜索")
        print("=" * 60)
    
    # 使用上下文管理器运行
    with LiteratureCrawler(
        headless=headless,
        max_results_per_keyword=max_results
    ) as crawler:
        
        # 执行爬取
        results = crawler.crawl_multiple_keywords(
            keywords=keywords,
            search_config=config
        )
        
        # 保存结果
        filepath = crawler.save_results(results)
        
        # 输出统计
        print("\n" + "=" * 60)
        print("爬取完成")
        print(f"关键词数：{crawler.stats['total_keywords']}")
        print(f"文献总数：{crawler.stats['success_count']}")
        print(f"失败数：{crawler.stats['failed_count']}")
        print(f"保存路径：{filepath}")
        print("=" * 60)
        
        return filepath


def main():
    parser = argparse.ArgumentParser(
        description='DARIS 文献爬取引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 爬取 Google Scholar
  python run_crawler.py --source google --keywords "MTGNN" "TimesNet"
  
  # 爬取 CNKI
  python run_crawler.py --source cnki --keywords "MTGNN" "时序预测"
  
  # 无头模式（后台运行）
  python run_crawler.py --headless --keywords "MTGNN" --max-results 10
        """
    )
    
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['MTGNN 时序预测', 'TimesNet 长时序'],
                        help='搜索关键词')
    parser.add_argument('--source', type=str, default='google',
                        choices=['google', 'cnki'],
                        help='搜索来源（google=Google Scholar, cnki=知网）')
    parser.add_argument('--max-results', type=int, default=5,
                        help='每个关键词最大结果数')
    parser.add_argument('--headless', action='store_true',
                        help='无头模式（不显示浏览器）')
    
    args = parser.parse_args()
    
    run_crawler(
        keywords=args.keywords,
        source=args.source,
        max_results=args.max_results,
        headless=args.headless
    )


if __name__ == '__main__':
    main()