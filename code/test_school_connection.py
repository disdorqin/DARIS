"""
测试学校图书馆网站连接
"""

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 华东理工大学图书馆
ECUST_LIB_URL = "https://lib.ecust.edu.cn/"

# 其他学术网站
ACADEMIC_SITES = {
    "CNKI": "https://www.cnki.net/",
    "万方数据": "https://www.wanfangdata.com.cn/",
    "维普": "http://www.cqvip.com/",
    "Web of Science": "https://www.webofscience.com/",
    "Engineering Village": "https://www.engineeringvillage.com/",
    "ScienceDirect": "https://www.sciencedirect.com/",
    "Springer": "https://link.springer.com/",
    "IEEE Xplore": "https://ieeexplore.ieee.org/",
    "Google Scholar": "https://scholar.google.com/",
}

def test_simple_connection(url, site_name):
    """简单测试网站连接"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"[OK] {site_name}: 连接成功 (HTTP {response.status_code})")
            return True
        else:
            print(f"[WARN] {site_name}: 连接失败 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"[ERROR] {site_name}: 连接错误 ({str(e)[:50]})")
        return False

def test_selenium_connection(url, site_name):
    """使用 Selenium 测试网站连接（模拟浏览器）"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3)
        
        title = driver.title
        if title:
            print(f"[OK] {site_name}: 浏览器访问成功 - {title[:50]}")
            driver.quit()
            return True
        else:
            print(f"[WARN] {site_name}: 页面标题为空")
            driver.quit()
            return False
    except Exception as e:
        print(f"[ERROR] {site_name}: 浏览器访问错误 ({str(e)[:50]})")
        return False

def main():
    print("=" * 60)
    print("测试学校图书馆及学术网站连接")
    print("=" * 60)
    
    # 测试华东理工大学图书馆
    print("\n【华东理工大学图书馆】")
    test_simple_connection(ECUST_LIB_URL, "华东理工图书馆")
    
    # 测试其他学术网站
    print("\n【其他学术网站】")
    for name, url in ACADEMIC_SITES.items():
        test_simple_connection(url, name)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    main()