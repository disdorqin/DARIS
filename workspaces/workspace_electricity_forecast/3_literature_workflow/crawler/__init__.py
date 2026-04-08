# DARIS 文献爬取模块
"""
基于 Selenium 的学术文献自动爬取模块
参考：https://github.com/YirenWangSdutcm/crawling-from-academic-database

功能：
- 支持关键词批量搜索
- 自动获取详情页完整摘要
- 输出 JSON 格式结构化数据
"""

from .literature_crawler import LiteratureCrawler

__all__ = ['LiteratureCrawler']