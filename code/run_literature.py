"""
DARIS 文献下载引擎 - 一键启动
执行优先级：arXiv → Crossref → Semantic Scholar
零门槛、免费、无校园网依赖、无 Selenium

作者：DARIS 团队
日期：2026-04-01
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all(keywords, max_results, interval):
    """运行所有下载器"""
    from utils.arxiv_downloader import ArxivDownloader
    from utils.crossref_downloader import CrossrefDownloader
    from utils.semantic_scholar_downloader import SemanticScholarDownloader
    
    print("\n" + "=" * 70)
    print("DARIS 文献下载引擎 - 全渠道启动")
    print("=" * 70)
    
    # 1. arXiv
    print("\n[1/3] 启动 arXiv 下载器...")
    arxiv_dl = ArxivDownloader(max_results=max_results, request_interval=interval)
    arxiv_dl.search_and_download(keywords)
    
    # 2. Crossref
    print("\n[2/3] 启动 Crossref 下载器...")
    crossref_dl = CrossrefDownloader(max_results=max_results, request_interval=interval)
    crossref_dl.search_and_download(keywords)
    
    # 3. Semantic Scholar
    print("\n[3/3] 启动 Semantic Scholar 下载器...")
    semantic_dl = SemanticScholarDownloader(max_results=max_results, request_interval=interval)
    semantic_dl.search_and_download(keywords)
    
    # 总结
    print("\n" + "=" * 70)
    print("DARIS 文献下载引擎 - 全部完成")
    print("=" * 70)
    print(f"\narXiv:        {arxiv_dl.stats['success_count']} 成功，{arxiv_dl.stats['failed_count']} 失败")
    print(f"Crossref:     {crossref_dl.stats['success_count']} 成功，{crossref_dl.stats['failed_count']} 失败")
    print(f"Semantic:     {semantic_dl.stats['success_count']} 成功，{semantic_dl.stats['failed_count']} 失败")
    print(f"\n总计：        {arxiv_dl.stats['success_count'] + crossref_dl.stats['success_count'] + semantic_dl.stats['success_count']} 成功")
    print(f"保存目录：    {Path('literature/pdf').absolute()}")
    print("=" * 70)


def run_arxiv(keywords, max_results, interval):
    """仅运行 arXiv"""
    from utils.arxiv_downloader import ArxivDownloader
    dl = ArxivDownloader(max_results=max_results, request_interval=interval)
    dl.search_and_download(keywords)


def run_crossref(keywords, max_results, interval):
    """仅运行 Crossref"""
    from utils.crossref_downloader import CrossrefDownloader
    dl = CrossrefDownloader(max_results=max_results, request_interval=interval)
    dl.search_and_download(keywords)


def run_semantic(keywords, max_results, interval):
    """仅运行 Semantic Scholar"""
    from utils.semantic_scholar_downloader import SemanticScholarDownloader
    dl = SemanticScholarDownloader(max_results=max_results, request_interval=interval)
    dl.search_and_download(keywords)


def main():
    parser = argparse.ArgumentParser(
        description='DARIS 文献下载引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有下载器
  python run_literature.py --all

  # 仅运行 arXiv
  python run_literature.py --arxiv

  # 仅运行 Crossref
  python run_literature.py --crossref

  # 仅运行 Semantic Scholar
  python run_literature.py --semantic

  # 自定义关键词
  python run_literature.py --all --keywords "MTGNN" "TimesNet"
        """
    )
    
    parser.add_argument('--all', action='store_true',
                        help='运行所有下载器')
    parser.add_argument('--arxiv', action='store_true',
                        help='仅运行 arXiv')
    parser.add_argument('--crossref', action='store_true',
                        help='仅运行 Crossref')
    parser.add_argument('--semantic', action='store_true',
                        help='仅运行 Semantic Scholar')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['power load forecasting', 'time series forecasting', 'MTGNN'],
                        help='检索关键词')
    parser.add_argument('--max-results', type=int, default=5,
                        help='每个渠道最大结果数（默认 5，避免限流）')
    parser.add_argument('--interval', type=float, default=5.0,
                        help='请求间隔秒数（默认 5 秒）')
    
    args = parser.parse_args()
    
    # 如果没有指定任何渠道，默认运行所有
    if not (args.arxiv or args.crossref or args.semantic or args.all):
        args.all = True
    
    if args.all:
        run_all(args.keywords, args.max_results, args.interval)
    elif args.arxiv:
        run_arxiv(args.keywords, args.max_results, args.interval)
    elif args.crossref:
        run_crossref(args.keywords, args.max_results, args.interval)
    elif args.semantic:
        run_semantic(args.keywords, args.max_results, args.interval)


if __name__ == '__main__':
    main()