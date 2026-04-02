# DARIS 文献爬取模块使用说明

## 功能概述

基于 Selenium 的学术文献自动爬取模块，支持：
- Google Scholar 搜索（免费）
- CNKI 知网搜索（需要校园网/机构订阅）
- 关键词批量搜索
- 自动获取详情页完整摘要
- JSON 格式结构化输出

---

## 前置要求

### 1. Python 环境
- Python 3.8+
- 已安装依赖：
```bash
pip install selenium webdriver-manager beautifulsoup4 lxml python-dotenv
```

### 2. Chrome 浏览器
确保已安装 Google Chrome 浏览器

### 3. ChromeDriver（必需）

由于 webdriver-manager 需要从 Google 服务器下载，在中国网络环境下可能失败。**推荐手动安装**：

#### 方式 1：使用国内镜像（推荐）

1. 查看 Chrome 版本：
   - 打开 Chrome
   - 点击右上角三个点 → 帮助 → 关于 Google Chrome
   - 记录版本号（如：120.0.6099.109）

2. 访问国内镜像下载：
   ```
   https://npmmirror.com/mirrors/chromedriver
   ```

3. 下载对应版本的 `chromedriver_win32.zip`

4. 解压到以下任一位置：
   - `C:\chromedriver\chromedriver.exe`
   - 项目目录 `code\chromedriver.exe`
   - 或任何在 PATH 中的目录

#### 方式 2：使用 webdriver-manager 自动下载（需要梯子）

如果已配置代理，webdriver-manager 会自动下载：
```bash
# 设置代理环境变量
set HTTP_PROXY=http://127.0.0.1:7890
set HTTPS_PROXY=http://127.0.0.1:7890

# 运行爬取脚本
python code/run_crawler.py --keywords "尖峰预测"
```

---

## 使用方法

### 基本用法

```bash
# 爬取 Google Scholar（5 篇）
python code/run_crawler.py --keywords "尖峰预测" --max-results 5

# 爬取 CNKI（自动使用.env 中的学校账号）
python code/run_crawler.py --source cnki --keywords "尖峰预测"

# 无头模式（后台运行，不显示浏览器）
python code/run_crawler.py --headless --keywords "尖峰预测" --max-results 10
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--keywords` | 搜索关键词（可多个） | `['MTGNN 时序预测']` |
| `--source` | 搜索来源（google/cnki） | `google` |
| `--max-results` | 每个关键词最大结果数 | `5` |
| `--headless` | 无头模式（不显示浏览器） | `False` |
| `--cnki-login` | CNKI 登录模式 | `自动检测` |

---

## CNKI 校园网登录

### 配置账号密码

在项目根目录的 `.env` 文件中添加：

```bash
# 学校图书馆配置（华东理工大学）
SCHOOL_USERNAME=24011507
SCHOOL_PASSWORD=Zlt20060313#
```

### 使用方式

```bash
# 爬取 CNKI 时会自动登录
python code/run_crawler.py --source cnki --keywords "尖峰预测"
```

---

## 输出格式

### 保存位置

结果保存到：`literature/crawled/crawled_literature_YYYYMMDD_HHMMSS.json`

### JSON 格式示例

```json
{
  "crawl_summary": {
    "total_keywords": 1,
    "total_articles": 5,
    "crawl_time": "2026-04-01T18:20:00"
  },
  "results": [
    {
      "keyword": "尖峰预测",
      "articles": [
        {
          "title": "基于深度学习的尖峰预测研究",
          "authors": "张三，李四",
          "journal": "自动化学报",
          "abstract": "本文提出了一种...",
          "url": "https://www.cnki.net/..."
        }
      ]
    }
  ]
}
```

---

## 常见问题

### Q1: ChromeDriver 下载失败

**错误信息**：
```
requests.exceptions.ConnectionError: Could not reach host. Are you offline?
```

**解决方案**：
1. 手动下载 ChromeDriver（见上方"前置要求"）
2. 或将 chromedriver.exe 放到项目目录

### Q2: CNKI 登录失败

**可能原因**：
- 账号密码错误
- 校园网 IP 不在白名单
- 需要验证码

**解决方案**：
1. 检查 `.env` 中的账号密码
2. 使用校园网连接
3. 手动登录一次后保持 Cookie

### Q3: 爬取结果为空

**可能原因**：
- 关键词无匹配结果
- 页面选择器过期

**解决方案**：
1. 更换关键词重试
2. 检查网站结构是否变化

---

## 文件结构

```
code/
├── crawler/
│   ├── __init__.py              # 模块初始化
│   └── literature_crawler.py    # 核心爬取模块
├── run_crawler.py               # 启动脚本
└── README_文献爬取模块使用说明.md  # 本说明文档
```

---

## 示例命令

```bash
# 测试 Google Scholar
python code/run_crawler.py --keywords "MTGNN" --max-results 3

# 测试 CNKI（需要校园网）
python code/run_crawler.py --source cnki --keywords "MTGNN" --max-results 3

# 批量爬取多个关键词
python code/run_crawler.py --keywords "MTGNN" "TimesNet" "XGBoost" --max-results 5

# 无头模式爬取
python code/run_crawler.py --headless --keywords "尖峰预测" --max-results 10
```

---

## 技术支持

如遇问题，请检查：
1. Chrome 浏览器是否安装
2. ChromeDriver 是否正确配置
3. 网络连接是否正常
4. `.env` 配置是否正确