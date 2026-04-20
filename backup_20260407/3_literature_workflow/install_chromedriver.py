"""
ChromeDriver 自动安装脚本
解决无法访问 Google 服务器的问题，使用国内镜像
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
import requests
from packaging import version

# 使用国内镜像
MIRROR_URL = "https://npmmirror.com/mirrors/chromedriver"

def get_chrome_version():
    """获取 Chrome 版本"""
    import subprocess
    
    # Windows Chrome 路径
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                version_str = result.stdout.strip()
                # 提取版本号
                for part in version_str.split():
                    if part.count('.') >= 2:
                        return part.split('.')[0]
            except Exception as e:
                print(f"获取 Chrome 版本失败：{e}")
    
    return None

def download_chromedriver(chrome_version):
    """下载 ChromeDriver"""
    print(f"检测到 Chrome 版本：{chrome_version}")
    print(f"使用镜像：{MIRROR_URL}")
    
    # 安装路径
    install_path = Path("C:/chromedriver")
    install_path.mkdir(exist_ok=True)
    
    # 尝试几个版本
    versions_to_try = [
        f"{chrome_version}.0.7390.122",
        f"{chrome_version}.0.7390.116",
        f"{chrome_version}.0.7390.97",
        "LATEST_RELEASE"
    ]
    
    for ver in versions_to_try:
        download_url = f"{MIRROR_URL}/{ver}/chromedriver_win32.zip"
        print(f"\n尝试下载版本：{ver}")
        
        try:
            response = requests.get(download_url, timeout=30)
            if response.status_code == 200:
                zip_path = Path("chromedriver.zip")
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                print("下载完成，正在解压...")
                
                # 解压
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(install_path)
                
                # 清理
                zip_path.unlink()
                
                # 添加到 PATH
                current_path = os.environ.get('PATH', '')
                if str(install_path) not in current_path:
                    new_path = f"{current_path};{install_path}"
                    os.environ['PATH'] = new_path
                    print(f"已添加到 PATH: {install_path}")
                
                print("\n" + "=" * 50)
                print("ChromeDriver 安装完成！")
                print(f"安装路径：{install_path}")
                print("\n请重新运行爬取命令:")
                print("python code/run_crawler.py --keywords \"尖峰预测\" --max-results 3")
                print("=" * 50)
                return True
                
        except Exception as e:
            print(f"下载失败：{e}")
            continue
    
    print("\n自动下载失败，请手动安装:")
    print("1. 访问：https://npmmirror.com/mirrors/chromedriver")
    print("2. 下载对应版本的 chromedriver_win32.zip")
    print("3. 解压到 C:\\chromedriver 或添加到 PATH")
    return False

if __name__ == '__main__':
    chrome_version = get_chrome_version()
    if chrome_version:
        download_chromedriver(chrome_version)
    else:
        print("未找到 Chrome 浏览器，请先安装 Chrome")