#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻获取脚本
从国内主流AI科技网站获取最新新闻
"""

import argparse
import sys
import io
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

# 修复Windows终端UTF-8编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 默认保存目录
DEFAULT_SAVE_DIR = os.path.expanduser("~/.openclaw/workspace-main/logs/daily")
CACHE_HOURS = 4  # 缓存有效期4小时

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

# Playwright 可选导入，用于动态页面
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class NewsFetcher:
    """AI新闻获取器"""

    # 支持的网站配置
    SOURCES = {
        "量子位": {
            "url": "https://www.qbitai.com/category/%e8%b5%84%e8%ae%af",
            "selector": {
                "articles": ".article-item, article, .post-item, .news-item",
                "title": "h2 a, h3 a, .post-title a, .title a",
                "link": "a",
                "summary": ".post-excerpt, .article-excerpt, p, .excerpt",
                "time": ".post-time, time, .publish-date, .date"
            },
            "parse_func": "parse_qbitai"
        },
        "InfoQ": {
            "url": "https://www.infoq.cn/topic/AI&LLM",
            "selector": {
                "articles": ".article-item, .card, .news-item, .list-item",
                "title": "h3 a, h2 a, .title a, .article-title a",
                "link": "a",
                "summary": ".summary, .desc, .description, p, .content",
                "time": ".time, time, .date, .publish-time"
            },
            "parse_func": "parse_infoq",
            "use_playwright": True
        },
        "智东西": {
            "url": "https://zhidx.com/p/category/zhidongxi/topnews",
            "selector": {
                "articles": ".article-item, .post-item, article, .news-item, .post",
                "title": "h2 a, h3 a, .entry-title a, .post-title a, .title a",
                "link": "a",
                "summary": ".entry-summary, .post-summary, .summary, .excerpt, .post-excerpt, p",
                "time": ".entry-date, .post-date, .time, time, .post-time"
            },
            "parse_func": "parse_zhidx"
        },
        "AI科技评论": {
            "url": "https://www.leiphone.com/",
            "selector": {
                "articles": ".article-item, .post, .news-box, .lph-article",
                "title": "h3 a, h2 a, .lph-title a, .title a",
                "link": "a",
                "summary": ".lph-summary, .summary, p, .excerpt, .desc",
                "time": ".time, time, .lph-time, .post-time"
            },
            "parse_func": "parse_leiphone"
        },
        "36氪": {
            "url": "https://36kr.com/",
            "selector": {
                "articles": ".article-item, .article-card, .kr-article, .feed-item",
                "title": "h3 a, h2 a, .article-title a, .title a",
                "link": "a",
                "summary": ".article-summary, .summary, p, .excerpt, .brief",
                "time": ".time, time, .article-time, .publish-time"
            },
            "parse_func": "parse_36kr",
            "use_playwright": True
        },
        "AiBase": {
            "url": "https://news.aibase.cn/zh/daily",
            "selector": {
                "articles": ".article-item, .news-item, .daily-item, .card",
                "title": "h3 a, h2 a, .title a, .news-title a",
                "link": "a",
                "summary": ".summary, .desc, .brief, p, .content",
                "time": ".time, time, .date, .publish-time"
            },
            "parse_func": "parse_aibase"
        },
        "极客公园": {
            "url": "https://www.geekpark.net/column/304",
            "selector": {
                "articles": ".article-item, .news-item, .article-card, .feed-item",
                "title": "h3 a, h2 a, .title a, .article-title a",
                "link": "a",
                "summary": ".summary, .desc, .brief, p, .excerpt",
                "time": ".time, time, .date, .publish-time"
            },
            "parse_func": "parse_geekpark"
        }
    }

    def __init__(self, limit: int = 5):
        self.limit = limit
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def fetch_html(self, url: str, encoding: str = None, use_playwright: bool = False) -> Optional[str]:
        """获取网页HTML内容"""
        # 如果指定使用 Playwright 或检测到需要动态渲染
        if use_playwright and PLAYWRIGHT_AVAILABLE:
            return self._fetch_with_playwright(url)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            # 如果指定了编码，使用指定编码；否则自动检测
            if encoding:
                response.encoding = encoding
            else:
                response.encoding = response.apparent_encoding or 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                print(f"  获取失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"  请求错误: {e}")
            return None

    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """使用 Playwright 获取动态渲染的页面内容"""
        if not PLAYWRIGHT_AVAILABLE:
            print("  Playwright 未安装，跳过")
            return None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.headers["User-Agent"],
                    viewport={"width": 1920, "height": 1080}
                )
                page = context.new_page()
                
                # 访问页面并等待加载完成
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 等待页面内容加载
                page.wait_for_timeout(3000)
                
                # 获取页面内容
                html = page.content()
                
                browser.close()
                return html
        except Exception as e:
            print(f"  Playwright 错误: {e}")
            return None

    def parse_zhidx(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析智东西的文章"""
        articles = []
        seen_titles = set()

        # 查找所有新闻项 - 使用class选择器
        news_items = soup.select('li .info-left-content')
        
        for item in news_items:
            try:
                # 查找标题
                title_elem = item.select_one('.info-left-title a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)
                
                # 查找摘要
                summary = ""
                desc_elem = item.select_one('.info-left-desc')
                if desc_elem:
                    summary = desc_elem.get_text(strip=True)
                
                # 查找时间
                time_str = "未知时间"
                time_elem = item.select_one('.ilr-time')
                if time_elem:
                    time_str = time_elem.get_text(strip=True)
                
                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."
                
                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "智东西"
                })
                
                if len(articles) >= limit:
                    break
            except Exception as e:
                continue
        
        return articles

    def parse_qbitai(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析量子位的文章"""
        articles = []
        seen_titles = set()

        # 量子位的文章链接格式是 /2026/02/xxxxxx.html
        all_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d+\.html'))

        for link in all_links:
            try:
                # 获取标题
                title = link.get_text(strip=True)

                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)

                # 获取链接
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.qbitai.com' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.excerpt, .summary, .post-excerpt, .desc, p') or
                                  parent.find_next_sibling(['div', 'p']))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, .post-time, .publish-date')
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)

                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."

                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "量子位"
                })

                if len(articles) >= limit:
                    break
            except Exception:
                continue

        return articles

    def parse_infoq(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析InfoQ的文章"""
        articles = []
        seen_titles = set()

        # InfoQ首页的文章链接通常是 /article/xxx 格式（xxx是字母数字混合）
        # 查找所有符合条件的链接
        all_links = soup.find_all('a', href=re.compile(r'/article/[a-zA-Z0-9]+'))

        for link in all_links:
            try:
                # 获取标题
                title = link.get_text(strip=True)

                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)

                # 获取链接
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.infoq.cn' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section', '.article-item'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.summary, .desc, .content, p') or
                                  parent.find_next_sibling(['div', 'p']))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, .publish-time')
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)

                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."

                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "InfoQ"
                })

                if len(articles) >= limit:
                    break
            except Exception:
                continue

        return articles

    def parse_leiphone(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析AI科技评论（雷锋网）的文章"""
        articles = []
        seen_titles = set()

        # 雷锋网的文章链接格式是 /category/xxxx/xxxxx.html
        all_links = soup.find_all('a', href=re.compile(r'/category/\w+/\w+\.html'))

        for link in all_links:
            try:
                # 获取标题
                title = link.get_text(strip=True)

                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)

                # 获取链接
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.leiphone.com' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.lph-summary, .summary, .excerpt, .desc, p') or
                                  parent.find_next_sibling(['div', 'p']))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, .lph-time, .post-time')
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)

                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."

                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "AI科技评论"
                })

                if len(articles) >= limit:
                    break
            except Exception:
                continue

        return articles

    def parse_36kr(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析36氪的文章"""
        articles = []
        seen_titles = set()

        # 36氪首页的新闻结构：每个新闻在一个div中
        # 查找所有可能的新闻容器
        news_divs = soup.select('div[class*="article"], div[class*="feed"], div[class*="item"]')
        
        for div in news_divs:
            try:
                # 查找标题链接
                title_link = div.find('a', href=re.compile(r'/p/\d+'))
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                
                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)
                
                # 获取链接
                href = title_link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://36kr.com' + href
                
                # 查找摘要 - 在标题附近的div中
                summary = ""
                # 先尝试找兄弟元素
                parent = title_link.find_parent('div')
                if parent:
                    # 查找父元素的兄弟div
                    grandparent = parent.find_parent('div')
                    if grandparent:
                        # 查找摘要div
                        summary_elem = grandparent.select_one('div:not(:has(a))')
                        if summary_elem:
                            summary_text = summary_elem.get_text(strip=True)
                            # 确保不是标题重复
                            if summary_text and summary_text != title:
                                summary = summary_text
                
                # 如果没找到，尝试其他选择器
                if not summary:
                    summary_elem = div.select_one('p, .summary, .desc')
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)
                
                # 查找时间
                time_str = "未知时间"
                time_elem = div.select_one('span, time, .time')
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    # 过滤掉纯数字或太短的文本
                    if time_text and len(time_text) > 2 and not time_text.isdigit():
                        time_str = time_text
                
                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."
                
                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "36氪"
                })
                
                if len(articles) >= limit:
                    break
            except Exception as e:
                continue
        
        return articles

    def parse_aibase(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析AiBase的文章"""
        articles = []
        seen_titles = set()

        # AiBase的文章链接格式是 /daily/xxxxx 或 /news/xxxxx
        all_links = soup.find_all('a', href=re.compile(r'/(daily|news)/\d+'))

        for link in all_links:
            try:
                # 获取标题
                title = link.get_text(strip=True)

                # 清理标题中的广告词
                # 去掉 "欢迎来到【AI日报】栏目!" 及其变体
                title = re.sub(r'欢迎来到【AI日报】栏目!?.*$', '', title)
                title = re.sub(r'这里是你每天探索人工智能.*$', '', title)
                title = re.sub(r'这里是你每.*$', '', title)
                title = title.strip()

                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)

                # 获取链接
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://news.aibase.cn' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.summary, .desc, .brief, .content, p') or
                                  parent.find_next_sibling(['div', 'p']))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, .publish-time')
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)

                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."

                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "AiBase"
                })

                if len(articles) >= limit:
                    break
            except Exception:
                continue

        return articles

    def parse_geekpark(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析极客公园的文章"""
        articles = []
        seen_titles = set()

        # 极客公园的文章链接格式是 /news/xxxxxx
        all_links = soup.find_all('a', href=re.compile(r'/news/\d+'))

        for link in all_links:
            try:
                # 获取标题
                title = link.get_text(strip=True)

                # 过滤无效标题
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                seen_titles.add(title)

                # 获取链接
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.geekpark.net' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.summary, .desc, .brief, .content, p') or
                                  parent.find_next_sibling(['div', 'p']))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, .publish-time')
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)

                # 限制摘要长度
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."

                articles.append({
                    "title": title,
                    "link": href,
                    "summary": summary,
                    "time": time_str,
                    "source": "极客公园"
                })

                if len(articles) >= limit:
                    break
            except Exception:
                continue

        return articles

    def parse_articles(self, html: str, source_name: str) -> List[Dict]:
        """解析文章列表"""
        config = self.SOURCES[source_name]
        selector = config.get("selector", {})

        soup = BeautifulSoup(html, 'html.parser')

        # 如果配置了专门的解析函数，使用它
        parse_func = config.get("parse_func")
        if parse_func == "parse_qbitai":
            return self.parse_qbitai(soup, self.limit)
        if parse_func == "parse_zhidx":
            return self.parse_zhidx(soup, self.limit)
        if parse_func == "parse_infoq":
            return self.parse_infoq(soup, self.limit)
        if parse_func == "parse_leiphone":
            return self.parse_leiphone(soup, self.limit)
        if parse_func == "parse_36kr":
            return self.parse_36kr(soup, self.limit)
        if parse_func == "parse_aibase":
            return self.parse_aibase(soup, self.limit)
        if parse_func == "parse_geekpark":
            return self.parse_geekpark(soup, self.limit)

        # 通用解析逻辑
        articles = []
        article_elements = soup.select(selector.get("articles", ""))

        # 如果没有找到文章，尝试更通用的选择器
        if not article_elements:
            article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'article|post|news|item|card'))

        for elem in article_elements[:self.limit]:
            try:
                # 提取标题
                title_elem = elem.select_one(selector.get("title", "")) or elem.find(['h1', 'h2', 'h3', 'h4'])
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                # 提取链接
                link_elem = elem.select_one(selector.get("link", "")) or title_elem
                link = link_elem.get('href', '') if link_elem else ''
                if link and not link.startswith('http'):
                    base_url = config["url"].rstrip('/')
                    link = base_url + ('' if link.startswith('/') else '/') + link

                # 提取摘要
                summary_elem = elem.select_one(selector.get("summary", ""))
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                if summary and len(summary) > 200:
                    summary = summary[:200] + "..."

                # 提取时间
                time_elem = elem.select_one(selector.get("time", ""))
                publish_time = time_elem.get_text(strip=True) if time_elem else "未知时间"

                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "time": publish_time,
                        "source": source_name
                    })
            except Exception:
                continue

        return articles

    def fetch_source(self, source_name: str) -> List[Dict]:
        """从指定来源获取新闻"""
        if source_name not in self.SOURCES:
            print(f"不支持的来源: {source_name}")
            return []

        print(f"正在获取 {source_name} 的新闻...")
        config = self.SOURCES[source_name]
        url = config["url"]

        # 检查是否需要使用 Playwright
        use_playwright = config.get("use_playwright", False)
        
        # InfoQ需要强制使用UTF-8编码
        encoding = 'utf-8' if source_name == "InfoQ" and not use_playwright else None
        html = self.fetch_html(url, encoding=encoding, use_playwright=use_playwright)

        if html:
            articles = self.parse_articles(html, source_name)
            print(f"  成功获取 {len(articles)} 条新闻")
            return articles
        return []

    def generate_markdown(self, all_articles: Dict[str, List[Dict]]) -> str:
        """生成Markdown格式的输出"""
        lines = []
        lines.append("# 最新AI新闻")
        lines.append(f"\n> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        total_count = sum(len(articles) for articles in all_articles.values())
        lines.append(f"> 共获取 {total_count} 条新闻\n")
        lines.append("---\n")

        # 结果汇总表格
        lines.append("\n## 结果汇总\n")
        lines.append("| 来源 | 获取数量 | 链接 |")
        lines.append("| ---------- | -------- | ------- |")
        
        source_urls = {
            "量子位": ("https://www.qbitai.com", "qbitai.com"),
            "InfoQ": ("https://www.infoq.cn", "infoq.cn"),
            "智东西": ("https://zhidx.com", "zhidx.com"),
            "AI科技评论": ("https://www.leiphone.com", "leiphone.com"),
            "36氪": ("https://36kr.com", "36kr.com"),
            "AiBase": ("https://news.aibase.cn/news", "aibase.cn"),
            "极客公园": ("https://www.geekpark.net", "geekpark.net")
        }
        
        for source_name, articles in all_articles.items():
            count = len(articles)
            url_info = source_urls.get(source_name, ("#", "#"))
            full_url, domain = url_info
            lines.append(f"| {source_name} | {count}条 | [{domain}]({full_url}) |")
        
        lines.append("")

        # 每个来源的详细表格
        for source_name, articles in all_articles.items():
            if not articles:
                continue

            lines.append(f"\n## {source_name}\n")
            lines.append("| 序号 | 标题 | 摘要 | 更新时间 |")
            lines.append("| ---- | ---- | ---- | -------- |")

            for i, article in enumerate(articles, 1):
                # 标题带链接
                title_link = f"[{article['title']}]({article['link']})"
                # 摘要（限制30字，避免表格过宽）
                summary = article.get('summary', '')
                if len(summary) > 30:
                    summary = summary[:30] + "..."
                # 时间
                time_str = article.get('time', '未知时间')
                
                lines.append(f"| {i} | {title_link} | {summary} | {time_str} |")
            
            lines.append("")

        return "\n".join(lines)

    def generate_simple_output(self, all_articles: Dict[str, List[Dict]]) -> str:
        """生成简化文本输出"""
        lines = []
        lines.append("=" * 60)
        lines.append("最新AI新闻")
        lines.append("=" * 60)
        lines.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        for source_name, articles in all_articles.items():
            if not articles:
                continue

            lines.append(f"\n【{source_name}】")
            lines.append("-" * 40)

            for i, article in enumerate(articles, 1):
                lines.append(f"\n{i}. {article['title']}")
                lines.append(f"   摘要: {article['summary'][:100]}...")
                lines.append(f"   链接: {article['link']}")
                lines.append(f"   时间: {article['time']}")

        return "\n".join(lines)


def get_cache_file_path() -> str:
    """获取缓存文件路径，按小时命名"""
    now = datetime.now()
    filename = f"ai-news-{now.strftime('%Y%m%d-%H')}.md"
    return os.path.join(DEFAULT_SAVE_DIR, filename)


def check_cache() -> Optional[str]:
    """检查是否有有效的缓存文件
    
    返回:
        缓存文件内容，如果没有有效缓存则返回None
    """
    cache_file = get_cache_file_path()
    
    if not os.path.exists(cache_file):
        return None
    
    # 获取文件修改时间
    mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
    now = datetime.now()
    
    # 检查是否在4小时内
    if now - mtime < timedelta(hours=CACHE_HOURS):
        print(f"发现 {CACHE_HOURS} 小时内的缓存文件，直接读取...")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    return None


def save_to_cache(content: str) -> str:
    """保存内容到缓存文件
    
    返回:
        保存的文件路径
    """
    # 确保目录存在
    os.makedirs(DEFAULT_SAVE_DIR, exist_ok=True)
    
    cache_file = get_cache_file_path()
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return cache_file


def main():
    global CACHE_HOURS
    
    parser = argparse.ArgumentParser(description="获取国内AI新闻")
    parser.add_argument("--limit", type=int, default=5, help="每个网站获取的新闻数量（默认5条）")
    parser.add_argument("--sources", type=str, default="", help="指定来源，逗号分隔（如：量子位,InfoQ）")
    parser.add_argument("--format", type=str, default="markdown", choices=["markdown", "simple"], help="输出格式")
    parser.add_argument("--output", type=str, default="", help="输出文件路径（可选，默认保存到缓存目录）")
    parser.add_argument("--no-cache", action="store_true", help="强制刷新，忽略缓存")
    parser.add_argument("--cache-hours", type=int, default=CACHE_HOURS, help=f"缓存有效期（小时，默认{CACHE_HOURS}小时）")

    args = parser.parse_args()
    
    CACHE_HOURS = args.cache_hours

    # 检查缓存（除非强制刷新）
    if not args.no_cache:
        cached_content = check_cache()
        if cached_content:
            print(cached_content)
            cache_file = get_cache_file_path()
            print(f"\n[缓存文件: {cache_file}]")
            return

    # 确定要抓取的来源
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",")]
    else:
        sources = list(NewsFetcher.SOURCES.keys())

    # 创建获取器
    fetcher = NewsFetcher(limit=args.limit)

    # 获取所有新闻
    all_articles = {}
    for source in sources:
        articles = fetcher.fetch_source(source)
        if articles:
            all_articles[source] = articles

    # 生成输出
    if args.format == "markdown":
        output = fetcher.generate_markdown(all_articles)
    else:
        output = fetcher.generate_simple_output(all_articles)

    # 保存到缓存文件
    cache_file = save_to_cache(output)
    
    # 如果指定了输出路径，同时保存到指定路径
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n新闻已保存到: {args.output}")
    
    # 输出内容
    print(output)
    print(f"\n[已缓存至: {cache_file}]")


if __name__ == "__main__":
    main()
