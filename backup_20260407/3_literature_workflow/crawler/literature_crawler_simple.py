"""
学术文献爬取器 - 简化版
直接照搬参考项目：https://github.com/YirenWangSdutcm/crawling-from-academic-database

支持网站：
- PubMed（https://pubmed.ncbi.nlm.nih.gov/）
- Google Scholar（需要梯子）
- CNKI（需要校园网）
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import json
import os
from pathlib import Path
from datetime import datetime

# 使用本地 ChromeDriver
driver_path = Path(__file__).parent.parent / 'chromedriver-win32' / 'chromedriver.exe'

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')

if driver_path.exists():
    driver = webdriver.Chrome(service=Service(str(driver_path)), options=chrome_options)
    print("[OK] ChromeDriver 初始化成功（本地）")
else:
    from webdriver_manager.chrome import ChromeDriverManager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    print("[OK] ChromeDriver 初始化成功（webdriver-manager）")

# 关键词列表
keywords = ["MTGNN", "TimesNet", "power load forecasting"]
results = []

# 输出目录
output_dir = Path('literature/crawled')
output_dir.mkdir(parents=True, exist_ok=True)


def fetch_articles(keyword):
    """爬取单篇文献"""
    try:
        print(f"\n正在处理关键词：{keyword}")
        
        # 访问 PubMed
        driver.get("https://pubmed.ncbi.nlm.nih.gov/")
        time.sleep(2)
        
        # 输入关键词
        search_box = driver.find_element("name", "term")
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)

        # 解析搜索结果
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        articles = soup.find_all('article', class_='full-docsum')
        
        print(f"找到 {len(articles)} 篇文献")
        
        keyword_results = []
        for i, article in enumerate(articles[:5]):  # 限制最多 5 篇
            title_elem = article.find('a', class_='docsum-title')
            title = title_elem.get_text(strip=True) if title_elem else "No title available"
            
            authors_elem = article.find('span', class_='docsum-authors')
            authors = authors_elem.get_text(strip=True) if authors_elem else "No authors available"
            
            journal_elem = article.find('span', class_='docsum-journal-citation')
            journal = journal_elem.get_text(strip=True) if journal_elem else "No journal information available"
            
            abstract_link = "https://pubmed.ncbi.nlm.nih.gov" + title_elem['href'] if title_elem else None
            
            # 获取摘要
            abstract = "No abstract available"
            if abstract_link:
                try:
                    driver.get(abstract_link)
                    time.sleep(2)
                    
                    abstract_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    abstract_section = abstract_soup.find('div', class_='abstract-content')
                    
                    if abstract_section:
                        # 移除参考文献
                        for ref in abstract_section.find_all('sup', class_='references'):
                            ref.decompose()
                        abstract = abstract_section.get_text(strip=True)
                    
                    print(f"  [{i+1}] {title[:50]}...")
                    
                except Exception as e:
                    print(f"  [{i+1}] 摘要获取失败：{e}")
                    abstract = "Abstract unavailable"
            
            keyword_results.append({
                'keyword': keyword,
                'title': title,
                'authors': authors,
                'journal': journal,
                'abstract': abstract,
                'url': abstract_link or '',
                'source': 'PubMed',
                'crawl_time': datetime.now().isoformat()
            })

        results.extend(keyword_results)
        return keyword_results

    except Exception as e:
        print(f"✗ 关键词 '{keyword}' 爬取失败：{e}")
        return []


# 主循环
print("=" * 60)
print("学术文献爬取器 - 开始运行")
print("=" * 60)

for keyword in keywords:
    keyword_results = fetch_articles(keyword)
    print(f"\n[OK] '{keyword}' 完成，共 {len(keyword_results)} 篇")
    
    # 关键词之间延迟
    if keyword != keywords[-1]:
        print("等待 3 秒后继续下一个关键词...")
        time.sleep(3)

# 关闭浏览器
driver.quit()

# 保存结果
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = output_dir / f'literature_{timestamp}.json'

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'crawl_summary': {
            'total_keywords': len(keywords),
            'total_articles': len(results),
            'crawl_time': datetime.now().isoformat()
        },
        'articles': results
    }, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 60)
print("爬取完成")
print(f"关键词数：{len(keywords)}")
print(f"文献总数：{len(results)}")
print(f"保存路径：{output_file}")
print("=" * 60)