"""
学术文献爬取器 - 基于 Selenium
参考：https://github.com/YirenWangSdutcm/crawling-from-academic-database

功能：
- 关键词批量搜索
- 自动获取详情页完整摘要
- 输出 JSON 格式结构化数据
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Selenium 相关
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# BeautifulSoup
from bs4 import BeautifulSoup

# WebDriver Manager
from webdriver_manager.chrome import ChromeDriverManager

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiteratureCrawler:
    """学术文献爬取器"""
    
    def __init__(
        self,
        headless: bool = False,
        wait_time: int = 10,
        max_results_per_keyword: int = 10,
        cnki_login: bool = False
    ):
        """
        初始化爬取器
        
        Args:
            headless: 是否无头模式（默认 False，方便调试）
            wait_time: 显式等待时间（秒）
            max_results_per_keyword: 每个关键词最大结果数
            cnki_login: 是否登录 CNKI（默认 False）
        """
        self.headless = headless
        self.wait_time = wait_time
        self.max_results = max_results_per_keyword
        self.cnki_login = cnki_login
        
        # 输出目录
        self.output_dir = Path('literature/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 从.env 读取 CNKI 账号密码
        self.cnki_username = os.getenv('SCHOOL_USERNAME', '')
        self.cnki_password = os.getenv('SCHOOL_PASSWORD', '')
        
        # 初始化浏览器
        self.driver = self._init_driver()
        
        # 统计数据
        self.stats = {
            'total_keywords': 0,
            'total_articles': 0,
            'failed_keywords': [],
            'success_count': 0,
            'failed_count': 0
        }
    
    def _init_driver(self) -> webdriver.Chrome:
        """初始化 Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # 基础配置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # 使用项目目录中的 ChromeDriver
        driver_path = Path(__file__).parent.parent / 'chromedriver-win32' / 'chromedriver.exe'
        if driver_path.exists():
            service = Service(str(driver_path))
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"Chrome WebDriver 初始化成功（使用本地 ChromeDriver: {driver_path}）")
        else:
            # 回退到 webdriver-manager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver 初始化成功（webdriver-manager 自动管理）")
        
        return driver
    
    def cnki_login_check(self):
        """CNKI 登录检查"""
        if self.cnki_username and self.cnki_password:
            logger.info(f"使用学号 {self.cnki_username} 登录 CNKI...")
            self._login_cnki()
        else:
            logger.warning("未在.env 中配置 SCHOOL_USERNAME 和 SCHOOL_PASSWORD")
    
    def _login_cnki(self):
        """登录 CNKI 知网"""
        try:
            # 访问 CNKI 登录页面
            self.driver.get('https://auth.cnki.net/login')
            time.sleep(3)
            
            # 等待登录表单加载
            username_input = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
            
            # 输入学号
            username_input.clear()
            username_input.send_keys(self.cnki_username)
            time.sleep(1)
            
            # 输入密码
            password_input = self.driver.find_element(By.NAME, 'password')
            password_input.clear()
            password_input.send_keys(self.cnki_password)
            time.sleep(1)
            
            # 点击登录
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], .login-btn')
            login_button.click()
            time.sleep(5)  # 等待登录完成
            
            # 检查登录状态
            if 'auth' not in self.driver.current_url.lower():
                logger.info("✓ CNKI 登录成功")
            else:
                logger.warning("⚠ CNKI 登录失败，请检查账号密码")
                
        except Exception as e:
            logger.error(f"CNKI 登录失败：{e}")
    
    def crawl_keyword(
        self,
        keyword: str,
        search_url: str,
        search_input_selector: str,
        search_button_selector: str,
        result_selectors: Dict[str, str],
        detail_url_extractor: Optional[callable] = None
    ) -> Dict:
        """
        爬取单个关键词的文献
        
        Args:
            keyword: 搜索关键词
            search_url: 搜索页面 URL
            search_input_selector: 搜索输入框选择器
            search_button_selector: 搜索按钮选择器
            result_selectors: 结果选择器字典
                - article_list: 文章列表选择器
                - title: 标题选择器
                - authors: 作者选择器
                - journal: 期刊选择器
                - link: 链接选择器
            detail_url_extractor: 详情页 URL 提取函数（可选）
        
        Returns:
            结构化数据字典
        """
        logger.info(f"开始爬取关键词：{keyword}")
        
        result = {
            'keyword': keyword,
            'crawl_time': datetime.now().isoformat(),
            'articles': []
        }
        
        try:
            # 直接访问搜索结果页面（避免页面元素查找失败）
            search_url_with_query = f"{search_url}&q={keyword.replace(' ', '+')}"
            logger.info(f"访问搜索 URL: {search_url_with_query}")
            self.driver.get(search_url_with_query)
            time.sleep(5)  # 等待页面加载
            
            # 获取搜索结果列表
            articles = self._parse_search_results(result_selectors)
            
            logger.info(f"解析到 {len(articles)} 篇文献")
            
            # 逐个访问详情页获取摘要
            for i, article in enumerate(articles[:self.max_results]):
                if article.get('detail_url'):
                    full_article = self._crawl_detail_page(
                        article['detail_url'],
                        result_selectors.get('abstract', '')
                    )
                    if full_article:
                        article.update(full_article)
                        result['articles'].append(article)
                        logger.info(f"  [{i+1}/{len(articles)}] 成功：{article.get('title', 'Unknown')[:50]}...")
                    else:
                        logger.warning(f"  [{i+1}/{len(articles)}] 详情页爬取失败")
                else:
                    result['articles'].append(article)
                    logger.info(f"  [{i+1}/{len(articles)}] 已收录：{article.get('title', 'Unknown')[:50]}...")
                
                # 礼貌延迟
                time.sleep(1)
            
            self.stats['success_count'] += len(result['articles'])
            logger.info(f"✓ 关键词 '{keyword}' 爬取完成，共 {len(result['articles'])} 篇")
            
        except Exception as e:
            logger.error(f"✗ 关键词 '{keyword}' 爬取失败：{e}")
            import traceback
            logger.error(traceback.format_exc())
            self.stats['failed_keywords'].append(keyword)
            self.stats['failed_count'] += 1
        
        return result
    
    def _parse_search_results(self, selectors: Dict[str, str]) -> List[Dict]:
        """解析搜索结果列表"""
        articles = []
        
        try:
            # 获取页面 HTML
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # 查找文章列表
            article_elements = soup.select(selectors.get('article_list', ''))
            
            for elem in article_elements:
                article = {
                    'title': '',
                    'authors': '',
                    'journal': '',
                    'abstract': '',
                    'url': '',
                    'detail_url': ''
                }
                
                # 提取标题
                title_elem = elem.select_one(selectors.get('title', ''))
                if title_elem:
                    article['title'] = title_elem.get_text(strip=True)
                    # 提取详情页链接
                    link_elem = title_elem.find('a')
                    if link_elem and link_elem.get('href'):
                        article['detail_url'] = link_elem['href']
                        article['url'] = link_elem['href']
                
                # 提取作者
                authors_elem = elem.select_one(selectors.get('authors', ''))
                if authors_elem:
                    article['authors'] = authors_elem.get_text(strip=True)
                
                # 提取期刊
                journal_elem = elem.select_one(selectors.get('journal', ''))
                if journal_elem:
                    article['journal'] = journal_elem.get_text(strip=True)
                
                if article['title']:
                    articles.append(article)
            
            logger.info(f"找到 {len(articles)} 篇文献")
            
        except Exception as e:
            logger.error(f"解析搜索结果失败：{e}")
        
        return articles
    
    def _crawl_detail_page(self, url: str, abstract_selector: str) -> Optional[Dict]:
        """爬取详情页获取摘要"""
        try:
            self.driver.get(url)
            time.sleep(3)  # 等待页面加载
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # 提取摘要
            abstract_elem = soup.select_one(abstract_selector)
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
            
            return {'abstract': abstract}
            
        except Exception as e:
            logger.error(f"爬取详情页失败：{e}")
            return None
    
    def crawl_multiple_keywords(
        self,
        keywords: List[str],
        search_config: Dict
    ) -> List[Dict]:
        """
        批量爬取多个关键词
        
        Args:
            keywords: 关键词列表
            search_config: 搜索配置字典
                - search_url: 搜索页面 URL
                - search_input_selector: 搜索输入框选择器
                - search_button_selector: 搜索按钮选择器
                - result_selectors: 结果选择器
        
        Returns:
            所有文献数据列表
        """
        self.stats['total_keywords'] = len(keywords)
        all_results = []
        
        for i, keyword in enumerate(keywords):
            logger.info(f"\n{'='*60}")
            logger.info(f"进度：[{i+1}/{len(keywords)}]")
            logger.info(f"{'='*60}")
            
            # 如果是 CNKI 且需要登录
            if search_config.get('login_url') and self.cnki_login:
                self.cnki_login_check()
            
            result = self.crawl_keyword(
                keyword=keyword,
                search_url=search_config['search_url'],
                search_input_selector=search_config['search_input_selector'],
                search_button_selector=search_config['search_button_selector'],
                result_selectors=search_config['result_selectors']
            )
            
            all_results.append(result)
            
            # 关键词之间延迟
            if i < len(keywords) - 1:
                logger.info(f"等待 5 秒后继续下一个关键词...")
                time.sleep(5)
        
        return all_results
    
    def save_results(self, results: List[Dict], filename: Optional[str] = None):
        """保存结果为 JSON 文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'crawled_literature_{timestamp}.json'
        
        filepath = self.output_dir / filename
        
        # 合并所有结果
        merged = {
            'crawl_summary': {
                'total_keywords': self.stats['total_keywords'],
                'total_articles': sum(len(r['articles']) for r in results),
                'crawl_time': datetime.now().isoformat()
            },
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        
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


# ==================== 预定义搜索配置 ====================

# CNKI 配置（需要机构订阅）
CNKI_CONFIG = {
    'search_url': 'https://www.cnki.net/',
    'login_url': 'https://auth.cnki.net/login',
    'search_input_selector': '#txt',
    'search_button_selector': '#btn',
    'result_selectors': {
        'article_list': '.result-table-list li, .search-result-list li',
        'title': '.fz14, .title',
        'authors': '.author, .Result',
        'journal': '.journal, .source',
        'abstract': '.abstract, .mark'
    }
}

# Google Scholar 配置
GOOGLE_SCHOLAR_CONFIG = {
    'search_url': 'https://scholar.google.com/scholar?hl=zh-CN&as_sdt=0%2C5',
    'search_input_selector': '#gs_hp_tsi',
    'search_button_selector': '#gs_hp_btn',
    'result_selectors': {
        'article_list': 'div.gs_r.gs_or.gs_scl',
        'title': 'h3.gs_rt a',
        'authors': 'div.gs_a',
        'journal': 'div.gs_a',
        'abstract': 'div.gs_rs'
    }
}


def main():
    """主函数 - 示例用法"""
    import argparse
    
    parser = argparse.ArgumentParser(description='学术文献爬取器')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=['MTGNN 时序预测', 'TimesNet 长时序'],
                        help='搜索关键词')
    parser.add_argument('--max-results', type=int, default=5,
                        help='每个关键词最大结果数')
    parser.add_argument('--headless', action='store_true',
                        help='无头模式')
    
    args = parser.parse_args()
    
    # 使用上下文管理器
    with LiteratureCrawler(
        headless=args.headless,
        max_results_per_keyword=args.max_results
    ) as crawler:
        # 示例：爬取 Google Scholar
        results = crawler.crawl_multiple_keywords(
            keywords=args.keywords,
            search_config=GOOGLE_SCHOLAR_CONFIG
        )
        
        # 保存结果
        crawler.save_results(results)
        
        # 输出统计
        print("\n" + "=" * 60)
        print("爬取完成")
        print(f"关键词数：{crawler.stats['total_keywords']}")
        print(f"文献总数：{crawler.stats['success_count']}")
        print(f"失败数：{crawler.stats['failed_count']}")
        print("=" * 60)


if __name__ == '__main__':
    main()