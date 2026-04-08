"""
Zotero 文献检索器
使用 Zotero API 检索和获取文献元数据

优势：
- 无需爬取网页，直接使用 API
- 支持学校已订阅的数据库
- 稳定可靠
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZoteroCrawler:
    """Zotero 文献检索器"""
    
    def __init__(self):
        """初始化 Zotero 检索器"""
        # 从.env 读取配置
        self.api_key = os.getenv('ZOTERO_API_KEY', '')
        self.user_id = os.getenv('ZOTERO_USER_ID', '')
        self.library_type = os.getenv('ZOTERO_LIBRARY_TYPE', 'user')
        self.collection_name = os.getenv('ZOTERO_COLLECTION_NAME', 'DARIS')
        
        # API 基础 URL
        self.base_url = 'https://api.zotero.org'
        
        # 输出目录
        self.output_dir = Path('literature/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计数据
        self.stats = {
            'total_keywords': 0,
            'total_articles': 0,
            'success_count': 0,
            'failed_count': 0
        }
        
        logger.info(f"Zotero 检索器初始化成功")
        logger.info(f"Library Type: {self.library_type}, User ID: {self.user_id}")
    
    def search_by_keyword(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """
        通过关键词检索 Zotero 文献
        
        Args:
            keyword: 检索关键词
            max_results: 最大结果数
        
        Returns:
            文献列表
        """
        logger.info(f"开始检索关键词：{keyword}")
        
        articles = []
        
        try:
            # 构建检索 URL
            url = f"{self.base_url}/{self.library_type}s/{self.user_id}/items"
            params = {
                'q': keyword,
                'limit': max_results,
                'format': 'json',
                'include': 'data'
            }
            
            headers = {
                'Zotero-API-Key': self.api_key,
                'Accept': 'application/json'
            }
            
            logger.info(f"检索 URL: {url}")
            logger.info(f"检索参数：{params}")
            
            # 发送请求
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            items = response.json()
            
            logger.info(f"检索到 {len(items)} 篇文献")
            
            # 解析文献数据
            for item in items:
                data = item.get('data', {})
                article = {
                    'title': data.get('title', 'Unknown'),
                    'authors': self._extract_authors(data),
                    'journal': data.get('publicationTitle', ''),
                    'year': data.get('date', '')[:4] if data.get('date') else '',
                    'abstract': data.get('abstractNote', ''),
                    'doi': data.get('DOI', ''),
                    'url': data.get('url', ''),
                    'item_type': data.get('itemType', ''),
                    'tags': [tag.get('tag', '') for tag in data.get('tags', [])]
                }
                
                if article['title'] and article['title'] != 'Unknown':
                    articles.append(article)
                    logger.info(f"  收录：{article['title'][:50]}...")
            
            self.stats['success_count'] += len(articles)
            logger.info(f"✓ 关键词 '{keyword}' 检索完成，共 {len(articles)} 篇")
            
        except Exception as e:
            logger.error(f"✗ 关键词 '{keyword}' 检索失败：{e}")
            import traceback
            logger.error(traceback.format_exc())
            self.stats['failed_count'] += 1
        
        return articles
    
    def _extract_authors(self, data: Dict) -> str:
        """提取作者信息"""
        creators = data.get('creators', [])
        authors = []
        for creator in creators:
            if creator.get('creatorType') == 'author':
                first_name = creator.get('firstName', '')
                last_name = creator.get('lastName', '')
                authors.append(f"{last_name} {first_name}".strip())
        return ', '.join(authors) if authors else ''
    
    def search_multiple_keywords(self, keywords: List[str], max_results: int = 5) -> Dict:
        """
        批量检索多个关键词
        
        Args:
            keywords: 关键词列表
            max_results: 每个关键词最大结果数
        
        Returns:
            检索结果字典
        """
        self.stats['total_keywords'] = len(keywords)
        all_articles = []
        
        for i, keyword in enumerate(keywords):
            logger.info(f"\n{'='*60}")
            logger.info(f"进度：[{i+1}/{len(keywords)}]")
            logger.info(f"{'='*60}")
            
            articles = self.search_by_keyword(keyword, max_results)
            all_articles.extend(articles)
            
            # 关键词之间延迟
            if i < len(keywords) - 1:
                logger.info(f"等待 2 秒后继续下一个关键词...")
                time.sleep(2)
        
        self.stats['total_articles'] = len(all_articles)
        
        return {
            'crawl_summary': {
                'total_keywords': self.stats['total_keywords'],
                'total_articles': self.stats['total_articles'],
                'crawl_time': datetime.now().isoformat()
            },
            'articles': all_articles
        }
    
    def save_results(self, results: Dict, filename: Optional[str] = None):
        """保存结果为 JSON 文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'zotero_literature_{timestamp}.json'
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存：{filepath}")
        return filepath
    
    def get_collections(self) -> List[Dict]:
        """获取 Zotero 收藏列表"""
        try:
            url = f"{self.base_url}/{self.library_type}s/{self.user_id}/collections"
            headers = {
                'Zotero-API-Key': self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            collections = response.json()
            logger.info(f"找到 {len(collections)} 个收藏")
            
            return collections
            
        except Exception as e:
            logger.error(f"获取收藏失败：{e}")
            return []
    
    def get_collection_items(self, collection_key: str, max_results: int = 50) -> List[Dict]:
        """
        获取指定收藏的文献
        
        Args:
            collection_key: 收藏键
            max_results: 最大结果数
        
        Returns:
            文献列表
        """
        try:
            url = f"{self.base_url}/{self.library_type}s/{self.user_id}/collections/{collection_key}/items"
            params = {
                'limit': max_results,
                'format': 'json',
                'include': 'data'
            }
            headers = {
                'Zotero-API-Key': self.api_key
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            items = response.json()
            logger.info(f"收藏中有 {len(items)} 篇文献")
            
            articles = []
            for item in items:
                data = item.get('data', {})
                article = {
                    'title': data.get('title', 'Unknown'),
                    'authors': self._extract_authors(data),
                    'journal': data.get('publicationTitle', ''),
                    'year': data.get('date', '')[:4] if data.get('date') else '',
                    'abstract': data.get('abstractNote', ''),
                    'doi': data.get('DOI', ''),
                    'item_type': data.get('itemType', '')
                }
                
                if article['title']:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"获取收藏文献失败：{e}")
            return []


def main():
    """主函数 - 示例用法"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Zotero 文献检索器')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['MTGNN', 'TimesNet', 'power load forecasting'],
                        help='检索关键词')
    parser.add_argument('--max-results', type=int, default=5,
                        help='每个关键词最大结果数')
    
    args = parser.parse_args()
    
    # 创建检索器
    crawler = ZoteroCrawler()
    
    # 执行检索
    results = crawler.search_multiple_keywords(args.keywords, args.max_results)
    
    # 保存结果
    crawler.save_results(results)
    
    # 输出统计
    print("\n" + "=" * 60)
    print("Zotero 检索完成")
    print(f"关键词数：{results['crawl_summary']['total_keywords']}")
    print(f"文献总数：{results['crawl_summary']['total_articles']}")
    print("=" * 60)


if __name__ == '__main__':
    main()