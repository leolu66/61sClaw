"""
RSS 新闻获取器 - 多信源聚合 → 过滤去重 → Top N 精选 → 原文抓取
"""
import asyncio
import hashlib
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _safe_print(*args, **kwargs):
    """安全 print，兼容 Windows GBK 终端"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 回退：替换无法编码的字符
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode(sys.stdout.encoding or 'gbk', errors='replace').decode(sys.stdout.encoding or 'gbk'))
            else:
                safe_args.append(a)
        print(*safe_args, **kwargs)

# ==================== RSS 信源配置 ====================
RSS_FEEDS = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "site_url": "https://techcrunch.com",
        "icon": "🌐",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "site_url": "https://www.theverge.com",
        "icon": "📱",
    },
    {
        "name": "Ars Technica AI",
        "url": "https://arstechnica.com/tag/ai/feed/",
        "site_url": "https://arstechnica.com",
        "icon": "🔬",
    },
    {
        "name": "MIT Tech Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "site_url": "https://www.technologyreview.com",
        "icon": "🎓",
    },
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/rss",
        "site_url": "https://news.ycombinator.com",
        "icon": "💻",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "site_url": "https://venturebeat.com",
        "icon": "🚀",
    },
]

# 文章内容提取的正文容器选择器
CONTENT_SELECTORS = [
    "article",
    '[class*="article-body"]',
    '[class*="article-content"]',
    '[class*="post-content"]',
    '[class*="entry-content"]',
    ".article__body",
    ".article-body",
    ".post-body",
    ".entry-body",
    "#article-body",
    "#article-content",
    "main",
    '[class*="content-body"]',
    ".prose",
]


@dataclass
class RSSItem:
    """RSS 新闻条目"""
    title: str
    url: str
    summary: str = ""
    published: Optional[datetime] = None
    source: str = ""
    source_url: str = ""
    source_icon: str = "📰"
    content: str = ""          # 抓取的原文内容
    deep_summary: str = ""     # LLM 生成的深度总结
    title_cn: str = ""         # 中文翻译标题
    summary_cn: str = ""       # 中文翻译摘要
    content_length: int = 0    # 原文长度

    @property
    def display_title(self) -> str:
        """优先显示中文标题"""
        return self.title_cn or self.title

    @property
    def display_summary(self) -> str:
        """优先显示中文总结"""
        return self.summary_cn or self.deep_summary or self.summary

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "title_cn": self.title_cn,
            "url": self.url,
            "summary": self.summary,
            "summary_cn": self.summary_cn,
            "published": self.published.isoformat() if self.published else "",
            "source": self.source,
            "source_url": self.source_url,
            "source_icon": self.source_icon,
            "content": self.content,
            "deep_summary": self.deep_summary,
            "content_length": self.content_length,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RSSItem":
        pub = None
        if d.get("published"):
            try:
                pub = datetime.fromisoformat(d["published"])
            except (ValueError, TypeError):
                pass
        return cls(
            title=d.get("title", ""),
            url=d.get("url", ""),
            summary=d.get("summary", ""),
            published=pub,
            source=d.get("source", ""),
            source_url=d.get("source_url", ""),
            source_icon=d.get("source_icon", "📰"),
            content=d.get("content", ""),
            deep_summary=d.get("deep_summary", ""),
            title_cn=d.get("title_cn", ""),
            summary_cn=d.get("summary_cn", ""),
            content_length=d.get("content_length", 0),
        )


def normalize_url(url: str) -> str:
    """URL 归一化用于去重"""
    try:
        parsed = urlparse(url)
        # 去掉尾部斜杠、去掉 query string（Hacker News 等站点使用 ?id=xxx）
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            parsed.params,
            '',  # 去掉 query
            '',  # 去掉 fragment
        ))
        return normalized
    except Exception:
        return url.lower()


def clean_html(html_text: str) -> str:
    """从 HTML 中提取纯文本"""
    if not html_text or len(html_text) < 20:
        return html_text.strip() if html_text else ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        # 移除 script/style 标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        # 合并多余空行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()
    except Exception:
        return re.sub(r'<[^>]+>', '', html_text).strip()


async def fetch_rss_feed(feed_config: dict, session: aiohttp.ClientSession) -> List[RSSItem]:
    """获取单个 RSS 源的条目"""
    feed_url = feed_config["url"]
    items = []

    try:
        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                logger.warning(f"RSS 源返回 {resp.status}: {feed_config['name']}")
                return items
            xml_content = await resp.text()

        # feedparser 是同步的，在线程中运行
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, xml_content)

        for entry in feed.entries:
            # 提取标题
            title = entry.get("title", "").strip()
            if not title:
                continue

            # 提取链接
            link = entry.get("link", "")
            if not link:
                continue

            # 提取摘要（去掉 HTML 标签）
            summary_raw = entry.get("summary", entry.get("description", ""))
            summary = clean_html(summary_raw)[:300] if summary_raw else ""

            # 提取发布时间
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass

            items.append(RSSItem(
                title=title,
                url=link,
                summary=summary[:300],
                published=published,
                source=feed_config["name"],
                source_url=feed_config["site_url"],
                source_icon=feed_config.get("icon", "📰"),
            ))

        logger.info(f"  ✅ {feed_config['name']}: {len(items)} 条")

    except asyncio.TimeoutError:
        logger.warning(f"  ⏱️ {feed_config['name']}: 超时")
    except Exception as e:
        logger.warning(f"  ❌ {feed_config['name']}: {e}")

    return items


def deduplicate_and_rank(items: List[RSSItem], top_n: int = 20, min_per_source: int = 2) -> List[RSSItem]:
    """
    去重 + 按渠道公平分配 + 取 Top N
    
    策略：
    1. URL 去重
    2. 每个信源按时间排序取 top_k（优先保底 min_per_source 条）
    3. 剩余名额按时间轮询补齐到 top_n
    """
    from collections import defaultdict
    
    # 1. URL 归一化去重
    seen_urls: Dict[str, RSSItem] = {}
    for item in items:
        norm_url = normalize_url(item.url)
        if norm_url in seen_urls:
            existing = seen_urls[norm_url]
            if item.published and (not existing.published or item.published > existing.published):
                seen_urls[norm_url] = item
        else:
            seen_urls[norm_url] = item

    deduped = list(seen_urls.values())

    # 2. 按信源分组，每组按时间降序
    by_source: Dict[str, List[RSSItem]] = defaultdict(list)
    for item in deduped:
        by_source[item.source].append(item)

    for source in by_source:
        by_source[source].sort(
            key=lambda x: x.published or datetime(2000, 1, 1, tzinfo=timezone.utc),
            reverse=True
        )

    # 3. 公平分配：先给每个信源保底 min_per_source 条
    selected: List[RSSItem] = []
    source_pool: Dict[str, List[RSSItem]] = {}
    per_source_max = max(min_per_source, top_n // len(by_source))

    for source, source_items in by_source.items():
        take = min(per_source_max, len(source_items))
        selected.extend(source_items[:take])
        source_pool[source] = source_items[take:]  # 剩余的

    # 4. 如果已选不足 top_n，轮询从各信源剩余池取（按时间优先）
    if len(selected) < top_n:
        # 所有剩余条目混合排序
        remainder = []
        for source, pool in source_pool.items():
            for item in pool:
                remainder.append(item)
        remainder.sort(
            key=lambda x: x.published or datetime(2000, 1, 1, tzinfo=timezone.utc),
            reverse=True
        )
        needed = top_n - len(selected)
        selected.extend(remainder[:needed])

    # 5. 最终按时间排序
    selected.sort(
        key=lambda x: x.published or datetime(2000, 1, 1, tzinfo=timezone.utc),
        reverse=True
    )

    return selected[:top_n]


async def fetch_article_content(item: RSSItem, session: aiohttp.ClientSession) -> RSSItem:
    """抓取单篇文章的原文内容"""
    try:
        async with session.get(item.url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                logger.debug(f"文章请求 {resp.status}: {item.url}")
                return item
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # 移除无关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        # 尝试找到正文容器
        content_elem = None
        for selector in CONTENT_SELECTORS:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if content_elem:
            # 移除文章内的广告、推荐等
            for tag in content_elem.select(
                '[class*="ad-"], [class*="advertisement"], '
                '[class*="related-"], [class*="recommend"], '
                '[class*="newsletter"], [class*="subscribe"], '
                '[aria-hidden="true"]'
            ):
                tag.decompose()
            text = content_elem.get_text(separator="\n")
        else:
            # 回退：取 body 文本
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n")
            else:
                text = soup.get_text(separator="\n")

        # 清理文本
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        # 限制最大长度（避免超长文章）
        if len(text) > 15000:
            text = text[:15000] + "\n\n... (内容已截断)"

        item.content = text
        item.content_length = len(text)

    except asyncio.TimeoutError:
        logger.debug(f"文章超时: {item.url}")
    except Exception as e:
        logger.debug(f"文章抓取失败: {item.url} - {e}")

    return item


async def fetch_all_rss(
    top_n: int = 20,
    fetch_content: bool = True,
    max_concurrent: int = 5,
) -> List[RSSItem]:
    """
    主流程：RSS 多信源 → 去重 → Top N → 抓原文

    Args:
        top_n: 精选条数
        fetch_content: 是否抓取原文
        max_concurrent: 最大并发数

    Returns:
        RSSItem 列表
    """
    connector = aiohttp.TCPConnector(limit=max_concurrent * 2, limit_per_host=3)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # 1. 并发获取所有 RSS 源
        _safe_print("📡 正在获取 RSS 源...")
        tasks = [fetch_rss_feed(feed, session) for feed in RSS_FEEDS]
        results = await asyncio.gather(*tasks)

        all_items = []
        for items in results:
            all_items.extend(items)

        total_raw = len(all_items)
        _safe_print(f"   原始条目: {total_raw} 条")

        # 2. 去重 + 公平分配 + 取 Top N
        top_items = deduplicate_and_rank(all_items, top_n)
        
        # 显示各信源分布
        from collections import Counter
        source_dist = Counter(item.source for item in top_items)
        dist_parts = []
        for feed in RSS_FEEDS:
            count = source_dist.get(feed["name"], 0)
            if count > 0:
                dist_parts.append(f"{feed['name']}:{count}")
        _safe_print(f"   精选 {len(top_items)} 条 | {"  ".join(dist_parts)}")

        if not fetch_content:
            return top_items

        # 3. 并发抓取原文
        _safe_print("📄 正在抓取文章原文...")
        sem = asyncio.Semaphore(max_concurrent)

        async def fetch_with_limit(item):
            async with sem:
                return await fetch_article_content(item, session)

        tasks = [fetch_with_limit(item) for item in top_items]
        top_items = await asyncio.gather(*tasks)

        # 统计
        with_content = sum(1 for item in top_items if item.content)
        _safe_print(f"   成功抓取原文: {with_content}/{len(top_items)} 篇")

        return list(top_items)


def format_rss_time(dt: Optional[datetime]) -> str:
    """格式化 RSS 发布时间"""
    if not dt:
        return "未知"
    now = datetime.now(timezone.utc)
    diff = now - dt
    if diff.days > 7:
        return dt.strftime("%m-%d")
    elif diff.days > 1:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}小时前"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}分钟前"
    else:
        return "刚刚"


def generate_rss_markdown(items: List[RSSItem]) -> str:
    """生成 RSS 新闻的 Markdown 输出"""
    lines = []
    lines.append("## 🌍 RSS 国际 AI 快讯")
    lines.append("")
    lines.append(f"> 来自 {len(RSS_FEEDS)} 个国际 RSS 信源，精选 {len(items)} 条")
    lines.append("")

    # 按来源分组
    from collections import defaultdict
    by_source = defaultdict(list)
    for item in items:
        by_source[item.source].append(item)

    for source_name, source_items in by_source.items():
        icon = source_items[0].source_icon if source_items else "📰"
        source_url = source_items[0].source_url if source_items else ""
        lines.append(f"### {icon} {source_name}")
        lines.append("")
        lines.append("| # | 标题 | 时间 |")
        lines.append("|---|------|------|")

        for i, item in enumerate(source_items, 1):
            title_link = f"[{item.display_title}]({item.url})"
            pub_time = format_rss_time(item.published)
            # 如果有深度总结，显示在标题下方
            summary_cell = title_link
            if item.display_summary and item.display_summary != item.summary:
                summary_cell = f"{title_link}<br><small>💡 {item.display_summary[:120]}</small>"
            lines.append(f"| {i} | {summary_cell} | {pub_time} |")

        lines.append("")

    # 如果有深度总结，单独列出
    has_deep = any(item.display_summary for item in items)
    if has_deep:
        lines.append("---")
        lines.append("")
        lines.append("### 📝 深度总结")
        lines.append("")
        for item in items:
            display_summary = item.display_summary
            if display_summary and display_summary != item.summary:
                lines.append(f"**[{item.display_title}]({item.url})** ({item.source})")
                lines.append(f"> {display_summary}")
                lines.append("")

    return "\n".join(lines)


# ==================== 命令行调试入口 ====================
async def main():
    """测试用入口"""
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    _safe_print("=" * 60)
    _safe_print("  RSS 新闻获取器 - 测试运行")
    _safe_print("=" * 60)
    _safe_print()

    items = await fetch_all_rss(top_n=10, fetch_content=True)

    _safe_print()
    _safe_print(generate_rss_markdown(items))

    # 保存 JSON 供后续使用
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    import json
    json_path = output_dir / "rss_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2)
    _safe_print(f"\n💾 已保存到: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
