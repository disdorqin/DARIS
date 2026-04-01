"""
DARIS 文献自动化下载启动脚本
一键调用：自动执行登录 + 检索 + 下载全流程

使用方法:
    python code/run_literature_download.py --platform all
    python code/run_literature_download.py --platform arxiv
    python code/run_literature_download.py --platform cnki --keyword "MTGNN"
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入文献下载工具
from utils.school_literature_spider import SchoolLiteratureSpider


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DARIS 学校内网文献自动化下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run_literature_download.py --platform all
    python run_literature_download.py --platform arxiv
    python run_literature_download.py --platform cnki --keyword "MTGNN"
        """
    )
    
    parser.add_argument(
        '--platform',
        type=str,
        default='all',
        choices=['all', 'arxiv', 'cnki', 'sciencedirect'],
        help='检索平台 (default: all)'
    )
    
    parser.add_argument(
        '--keyword',
        type=str,
        default=None,
        help='检索关键词 (default: 使用配置文件中的关键词列表)'
    )
    
    parser.add_argument(
        '--install-deps',
        action='store_true',
        help='安装依赖包后退出'
    )
    
    args = parser.parse_args()
    
    # 安装依赖
    if args.install_deps:
        print("正在安装依赖包...")
        os.system('pip install selenium python-dotenv webdriver-manager arxiv')
        print("依赖安装完成！")
        print("请重新运行：python run_literature_download.py --platform all")
        return
    
    # 执行文献下载
    spider = SchoolLiteratureSpider()
    spider.run(platform=args.platform)


if __name__ == '__main__':
    main()