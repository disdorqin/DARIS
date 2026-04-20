"""
PubMed 文献爬取器
参考：https://github.com/YirenWangSdutcm/crawling-from-academic-database

优势：
- 无需登录
- 无需梯子
- 稳定可靠
- 包含完整摘要
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PubMedCrawler:
    """PubMed 文献爬取器"""
    
    def __init__(self, headless: bool = False):
        """
        初始化爬取器
        
        Args:
            headless: 是否无头模式
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 使用本地 ChromeDriver
        driver_path = Path(__file__).parent.parent / 'chromedriver-win32' / 'chromedriver.exe'
        if driver_path.exists():
            service = Service(str(driver_path))
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"Chrome WebDriver 初始化成功（本地 ChromeDriver）")
        else:
            # 回退到 webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver 初始化成功（webdriver-manager）")
        
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
    
    def fetch_articles(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """
        检索文献
        
        Args:
            keyword: 关键词
            max_results: 最大结果数
        
        Returns:
            文献列表
        """
        logger.info(f"开始检索关键词：{keyword}")
        results = []
        
        try:
            # 访问 PubMed
            self.driver.get("https://pubmed.ncbi.nlm.nih.gov/")
            time.sleep(2)
            
            # 输入关键词
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "term"))
            )
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            time.sleep(5)
            
            # 解析搜索结果
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            articles = soup.find_all('article', class_='full-docsum')
            
            logger.info(f"找到 {len(articles)} 篇文献")
            
            for i, article in enumerate(articles[:max_results]):
                article_data = self._parse_article(article)
                if article_data['title']:
                    results.append(article_data)
                    logger.info(f"  [{i+1}] {article_data['title'][:50]}...")
            
            self.stats['success_count'] += len(results)
            logger.info(f"✓ 关键词 '{keyword}' 检索完成，共 {len(results)} 篇")
            
        except Exception as e:
            logger.error(f"✗ 关键词 '{keyword}' 检索失败：{e}")
            import traceback
            logger.error(traceback.format_exc())
            self.stats['failed_count'] += 1
        
        return results
    
    def _parse_article(self, article) -> Dict:
        """解析单篇文献"""
        title_elem = article.find('a', class_='docsum-title')
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        authors_elem = article.find('span', class_='docsum-authors')
        authors = authors_elem.get_text(strip=True) if authors_elem else ""
        
        journal_elem = article.find('span', class_='docsum-journal-citation')
        journal = journal_elem.get_text(strip=True) if journal_elem else ""
        
        abstract = ""
        abstract_link = None
        
        if title_elem:
            abstract_link = "https://pubmed.ncbi.nlm.nih.gov" + title_elem['href']
            
            try:
                self.driver.get(abstract_link)
                time.sleep(2)
                
                abstract_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                abstract_section = abstract_soup.find('div', class_='abstract-content')
                
                if abstract_section:
                    # 移除参考文献
                    for ref in abstract_section.find_all('sup', class_='references'):
                        ref.decompose()
                    abstract = abstract_section.get_text(strip=True)
                    
            except Exception as e:
                logger.warning(f"  摘要获取失败：{e}")
                abstract = "Abstract unavailable"
        
        return {
            'keyword': '',  # 由上层填充
            'title': title,
            'authors': authors,
            'journal': journal,
            'abstract': abstract,
            'url': abstract_link or '',
            'source': 'PubMed'
        }
    
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
            
            articles = self.fetch_articles(keyword, max_results)
            for article in articles:
                article['keyword'] = keyword
            all_articles.extend(articles)
            
            # 关键词之间延迟
            if i < len(keywords) - 1:
                logger.info(f"等待 3 秒后继续下一个关键词...")
                time.sleep(3)
        
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
            filename = f'pubmed_literature_{timestamp}.json'
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存：{filepath}")
        return filepath
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PubMed 文献检索器')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['MTGNN', 'TimesNet', 'power load forecasting'],
                        help='检索关键词')
    parser.add_argument('--max-results', type=int, default=3,
                        help='每个关键词最大结果数')
    parser.add_argument('--headless', action='store_true',
                        help='无头模式')
    
    args = parser.parse_args()
    
    with PubMedCrawler(headless=args.headless) as crawler:
        results = crawler.search_multiple_keywords(args.keywords, args.max_results)
        crawler.save_results(results)
        
        print("\n" + "=" * 60)
        print("PubMed 检索完成")
        print(f"关键词数：{results['crawl_summary']['total_keywords']}")
        print(f"文献总数：{results['crawl_summary']['total_articles']}")
        print("=" * 60)


if __name__ == '__main__':
    main()