#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻获取脚本
从国内主流AI科技网站获取最新新闻
"""

import argparse
import sys
from datetime import datetime
from typing import List, Dict, Optional
import re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)


class NewsFetcher:
    """AI新闻获取器"""

    # 支持的网站配置
    SOURCES = {
        "机器之心": {
            "url": "https://www.jiqizhixin.com/",
            "selector": {
                "articles": ".article-item, .article-card, article, .news-item, .article-list-item",
                "title": "h2 a, h3 a, .article-title a, a.title, .title a",
                "link": "a",
                "summary": ".summary, .desc, .article-desc, p.summary, .article-content",
                "time": ".time, time, .publish-time, .article-time, .date"
            },
            "parse_func": "parse_jiqizhixin"
        },
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
            "url": "https://www.infoq.cn/",
            "selector": {
                "articles": ".article-item, .card, .news-item, .list-item",
                "title": "h3 a, h2 a, .title a, .article-title a",
                "link": "a",
                "summary": ".summary, .desc, .description, p, .content",
                "time": ".time, time, .date, .publish-time"
            },
            "parse_func": "parse_infoq"
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
            "url": "https://36kr.com/information/technology",
            "selector": {
                "articles": ".article-item, .article-card, .kr-article, .feed-item",
                "title": "h3 a, h2 a, .article-title a, .title a",
                "link": "a",
                "summary": ".article-summary, .summary, p, .excerpt, .brief",
                "time": ".time, time, .article-time, .publish-time"
            },
            "parse_func": "parse_36kr"
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

    def fetch_html(self, url: str, encoding: str = None) -> Optional[str]:
        """获取网页HTML内容"""
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

    def parse_zhidx(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析智东西的文章"""
        articles = []
        seen_titles = set()

        # 智东西的文章链接格式是 /p/xxxx.html
        all_links = soup.find_all('a', href=re.compile(r'/p/\d+\.html'))

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
                    href = 'https://zhidx.com' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section', 'header'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.summary, .excerpt, .post-excerpt, .desc') or
                                  parent.select_one('p'))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, .post-time, .entry-date')
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
            except Exception:
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

        # InfoQ首页的文章链接通常是 /article/xxx 格式
        # 查找所有符合条件的链接
        all_links = soup.find_all('a', href=re.compile(r'/article/\d+'))

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

        # 36氪的文章链接格式是 /p/xxxxxx
        all_links = soup.find_all('a', href=re.compile(r'/p/\d+'))

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
                    href = 'https://36kr.com' + href

                # 尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # 在父元素中查找摘要
                    summary_elem = (parent.select_one('.article-summary, .summary, .brief, .excerpt, p') or
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
                    "source": "36氪"
                })

                if len(articles) >= limit:
                    break
            except Exception:
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

    def parse_jiqizhixin(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """专门解析机器之心的文章"""
        articles = []
        seen_titles = set()

        # 机器之心的文章链接通常是 /reference/xxx 或 /article/xxx 格式
        # 查找所有符合条件的链接
        all_links = soup.find_all('a', href=re.compile(r'/(reference|article)/'))

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
                    href = 'https://www.jiqizhixin.com' + href

                # 对于机器之心，尝试在父元素中查找更多元数据
                summary = ""
                time_str = "未知时间"

                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # 在父元素中查找摘要（机器之心的摘要通常在.data-content或.description中）
                    summary_elem = (parent.select_one('.article-desc, .desc, .brief, .summary') or
                                  parent.select_one('[class*="content"]') or
                                  parent.select_one('p'))
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                    # 查找时间
                    time_elem = parent.select_one('time, .time, .date, [class*="time"]')
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
                    "source": "机器之心"
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
        if parse_func == "parse_jiqizhixin":
            return self.parse_jiqizhixin(soup, self.limit)
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
        url = self.SOURCES[source_name]["url"]

        # InfoQ需要强制使用UTF-8编码
        encoding = 'utf-8' if source_name == "InfoQ" else None
        html = self.fetch_html(url, encoding=encoding)

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
        lines.append(f"> 共获取 {sum(len(articles) for articles in all_articles.values())} 条新闻\n")
        lines.append("---\n")

        for source_name, articles in all_articles.items():
            if not articles:
                continue

            lines.append(f"\n## {source_name}\n")

            for i, article in enumerate(articles, 1):
                # 卡片格式
                lines.append(f"### {i}. {article['title']}")
                lines.append(f"")
                # 只在有摘要时显示摘要行
                if article.get('summary'):
                    lines.append(f"**摘要:** {article['summary']}")
                    lines.append(f"")
                lines.append(f"[阅读原文]({article['link']}) | 时间: {article['time']}")
                lines.append(f"")
                lines.append("---")
                lines.append(f"")

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


def main():
    parser = argparse.ArgumentParser(description="获取国内AI新闻")
    parser.add_argument("--limit", type=int, default=5, help="每个网站获取的新闻数量（默认5条）")
    parser.add_argument("--sources", type=str, default="", help="指定来源，逗号分隔（如：机器之心,量子位）")
    parser.add_argument("--format", type=str, default="markdown", choices=["markdown", "simple"], help="输出格式")
    parser.add_argument("--output", type=str, default="", help="输出文件路径")

    args = parser.parse_args()

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

    # 输出或保存
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n新闻已保存到: {args.output}")
    else:
        print("\n" + output)


if __name__ == "__main__":
    main()
