import asyncio
import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# 添加 spider 模块路径
sys.path.insert(0, str(Path(__file__).parent))

from spider.config_loader import ConfigLoader
from spider.engine import SpiderEngine, NewsItem
from spider.storage import StorageFactory

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CACHE_HOURS = 4
DEFAULT_LIMIT = 5
CACHE_DIR = Path(__file__).parent / "cache"
OUTPUT_DIR = Path(__file__).parent / "output"

# 站点名称映射（中文名 -> 配置文件名）
SITE_NAME_MAP = {
    "量子位": "qbitai",
    "qbitai": "qbitai",
    "InfoQ": "infoq",
    "infoq": "infoq",
    "InfoQ中国": "infoq",
    "智东西": "zhidx",
    "zhidx": "zhidx",
    "AI科技评论": "leiphone",
    "leiphone": "leiphone",
    "雷锋网": "leiphone",
    "极客公园": "geekpark",
    "geekpark": "geekpark",
    "GeekPark": "geekpark",
    "AiBase": "aibase",
    "aibase": "aibase",
    "AI基地": "aibase",
    "36氪": "36kr",
    "36kr": "36kr",
}

# 站点图标映射
SITE_ICONS = {
    "36氪AI": "1️⃣",
    "AiBase新闻": "2️⃣",
    "InfoQ AI简报": "3️⃣",
    "AI科技评论": "4️⃣",
    "量子位": "5️⃣",
    "智东西": "6️⃣",
    "极客公园": "7️⃣",
    "机器之心": "8️⃣",
}


def get_cache_path(sources: List[str], limit: int) -> Path:
    """生成缓存文件路径"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = f"{'_'.join(sorted(sources))}_{limit}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()[:8]
    return CACHE_DIR / f"ai_news_{cache_hash}.json"


def is_cache_valid(cache_path: Path, cache_hours: int) -> bool:
    """检查缓存是否有效"""
    if not cache_path.exists():
        return False
    cache_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = cache_mtime + timedelta(hours=cache_hours)
    return datetime.now() < expiry_time


def load_cache(cache_path: Path) -> List[dict]:
    """加载缓存数据"""
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"加载缓存失败: {e}")
        return []


def save_cache(cache_path: Path, data: List[dict]):
    """保存缓存数据"""
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"保存缓存失败: {e}")


def parse_sources(sources_str: Optional[str]) -> List[str]:
    """解析来源字符串"""
    if not sources_str:
        return []
    sources = []
    for name in sources_str.replace("，", ",").split(","):
        name = name.strip()
        if name in SITE_NAME_MAP:
            sources.append(SITE_NAME_MAP[name])
    return sources if sources else []


def format_time(time_str: str) -> str:
    """格式化时间显示"""
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "刚刚"
        elif diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() / 60)}分钟前"
        elif diff < timedelta(hours=24):
            return f"{int(diff.total_seconds() / 3600)}小时前"
        elif diff < timedelta(days=2):
            return "昨天"
        elif diff < timedelta(days=7):
            return f"{int(diff.days)}天前"
        else:
            return dt.strftime("%m-%d")
    except:
        return time_str


def truncate_summary(text: str, max_length: int = 50) -> str:
    """截断摘要"""
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def generate_feishu_summary(all_items: List[dict], source_stats: dict) -> str:
    """生成飞书精简版消息（控制长度）"""
    lines = []
    
    # 标题
    lines.append(f"🤖 **AI 新闻速递** | {datetime.now().strftime('%m月%d日 %H:%M')}")
    lines.append("")
    
    # 汇总
    total = len(all_items)
    lines.append(f"📊 共 **{total}** 条新闻（{len(source_stats)}个来源）")
    lines.append("")
    
    # 按来源分组，每个来源只显示前3条
    from collections import defaultdict
    items_by_source = defaultdict(list)
    for item in all_items:
        items_by_source[item.get("source", "未知")].append(item)
    
    for site_name, items in items_by_source.items():
        icon = SITE_ICONS.get(site_name, "📰")
        lines.append(f"{icon} **{site_name}** ({len(items)}条)")
        
        # 只显示前3条
        for i, item in enumerate(items[:3], 1):
            title = item.get("title", "无标题")
            url = item.get("url", "")
            pub_time = format_time(item.get("publish_time", ""))
            
            # 标题截断
            if len(title) > 40:
                title = title[:40] + "..."
            
            if url:
                lines.append(f"{i}. [{title}]({url})")
            else:
                lines.append(f"{i}. {title}")
        
        if len(items) > 3:
            lines.append(f"   ... 还有 {len(items) - 3} 条")
        
        lines.append("")
    
    return "\n".join(lines)


async def fetch_with_playwright(config: dict, limit: int) -> List[dict]:
    """使用 Playwright 采集需要 JavaScript 渲染的站点"""
    from playwright.async_api import async_playwright
    from lxml import html
    
    site_config = config["site"]
    list_config = config["list_page"]
    site_name = site_config["name"]
    base_url = site_config["base_url"]
    
    items = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            list_url = list_config["url"]
            await page.goto(list_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            html_content = await page.content()
            tree = html.fromstring(html_content)
            
            item_selector = list_config["item_selector"]
            if item_selector.get("type") == "css":
                elements = tree.cssselect(item_selector["value"])
            else:
                elements = tree.xpath(item_selector["value"])
            
            fields_config = list_config.get("fields", {})
            
            for elem in elements[:limit]:
                try:
                    title_config = fields_config.get("title", {})
                    if title_config.get("type") == "css":
                        title_elem = elem.cssselect(title_config["value"])
                        title = title_elem[0].text_content().strip() if title_elem else ""
                    else:
                        title = ""
                    
                    link_config = fields_config.get("link", {})
                    if link_config.get("type") == "css":
                        link_elem = elem.cssselect(link_config["value"])
                        if link_elem:
                            href = link_elem[0].get("href", "")
                            if href and not href.startswith("http"):
                                href = base_url + href
                        else:
                            href = ""
                    else:
                        href = ""
                    
                    summary_config = fields_config.get("summary", {})
                    if summary_config.get("type") == "css":
                        summary_elem = elem.cssselect(summary_config["value"])
                        summary = summary_elem[0].text_content().strip() if summary_elem else ""
                    else:
                        summary = ""
                    
                    pub_time = ""
                    all_text = elem.xpath('.//text()')
                    for t in all_text:
                        t = t.strip()
                        if any(keyword in t for keyword in ['小时前', '天前', '分钟前', '昨天', '2026', '2025']):
                            pub_time = t
                            break
                    
                    if title and href:
                        items.append({
                            "title": title,
                            "url": href,
                            "summary": truncate_summary(summary, 50),
                            "publish_time": pub_time,
                            "source": site_name,
                            "site_url": base_url,
                        })
                except Exception as e:
                    logger.warning(f"提取条目失败: {e}")
                    continue
        finally:
            await browser.close()
    
    return items


async def fetch_news(
    sources: List[str] = None,
    limit: int = 5,
    no_cache: bool = False,
    cache_hours: int = DEFAULT_CACHE_HOURS,
) -> tuple[List[dict], dict]:
    """获取 AI 新闻"""
    cache_sources = sources if sources else ["all"]
    cache_path = get_cache_path(cache_sources, limit)
    
    if not no_cache and is_cache_valid(cache_path, cache_hours):
        print(f"📦 使用缓存数据（{cache_hours}小时内有效）")
        cached_data = load_cache(cache_path)
        if cached_data:
            source_stats = {}
            for item in cached_data:
                source = item.get("source", "未知")
                source_stats[source] = source_stats.get(source, 0) + 1
            return cached_data, source_stats
    
    loader = ConfigLoader()
    
    if sources:
        configs = []
        for site_name in sources:
            config = loader.load_single(site_name)
            if config:
                configs.append(config)
    else:
        configs = loader.load_all(enabled_only=True)
    
    if not configs:
        print("❌ 没有可用的站点配置")
        return [], {}
    
    playwright_sites = []
    normal_configs = []
    
    for config in configs:
        request_config = config["site"].get("request", {})
        if request_config.get("use_playwright"):
            playwright_sites.append(config)
        else:
            normal_configs.append(config)
    
    all_items = []
    source_stats = {}
    
    async with SpiderEngine(max_concurrent=3, default_delay=1.0) as engine:
        for config in normal_configs:
            site_name = config["site"]["name"]
            site_url = config["site"].get("base_url", "")
            
            try:
                count = 0
                async for item in engine.crawl_site(config, limit):
                    raw_time = getattr(item, '_raw_publish_time', None)
                    if raw_time:
                        pub_time_str = raw_time
                    elif item.publish_time:
                        pub_time_str = item.publish_time.isoformat()
                    else:
                        pub_time_str = ""
                    
                    item_dict = {
                        "title": item.title,
                        "url": item.url,
                        "summary": item.summary,
                        "publish_time": pub_time_str,
                        "source": site_name,
                        "site_url": site_url,
                    }
                    all_items.append(item_dict)
                    count += 1
                
                source_stats[site_name] = count
                print(f"  ✅ {site_name}: {count} 条")
            except Exception as e:
                print(f"  ❌ {site_name}: 采集失败 ({e})")
                source_stats[site_name] = 0
    
    for config in playwright_sites:
        site_name = config["site"]["name"]
        site_url = config["site"].get("base_url", "")
        
        try:
            items = await fetch_with_playwright(config, limit)
            for item in items:
                all_items.append(item)
            source_stats[site_name] = len(items)
            print(f"  ✅ {site_name}: {len(items)} 条")
        except Exception as e:
            print(f"  ❌ {site_name}: 采集失败 ({e})")
            source_stats[site_name] = 0
    
    if all_items:
        save_cache(cache_path, all_items)
    
    return all_items, source_stats


def main():
    """主函数 - 命令行入口"""
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(
        description="获取国内权威AI科技网站的最新新闻",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fetch_ai_news.py                    # 获取所有站点新闻
  python fetch_ai_news.py --limit 10         # 每个站点获取10条
  python fetch_ai_news.py --sources 量子位,InfoQ  # 只获取指定站点
  python fetch_ai_news.py --no-cache         # 强制刷新
  python fetch_ai_news.py --output news.md   # 保存到指定文件
  python fetch_ai_news.py --feishu           # 发送到飞书
        """
    )
    
    parser.add_argument("--limit", "-n", type=int, default=DEFAULT_LIMIT,
                        help=f"每个网站获取的新闻数量（默认{DEFAULT_LIMIT}条）")
    parser.add_argument("--sources", "-s", help="指定特定网站，用逗号分隔")
    parser.add_argument("--output", "-o", help="保存到指定Markdown文件")
    parser.add_argument("--no-cache", action="store_true", help="强制刷新")
    parser.add_argument("--cache-hours", type=int, default=DEFAULT_CACHE_HOURS,
                        help=f"缓存有效期（小时，默认{DEFAULT_CACHE_HOURS}小时）")
    parser.add_argument("--feishu", action="store_true", help="发送到飞书")
    
    args = parser.parse_args()
    
    sources = parse_sources(args.sources)
    
    print("🤖 开始获取 AI 新闻...")
    if sources:
        print(f"   指定站点: {', '.join(args.sources.split(','))}")
    else:
        print("   采集所有启用的站点")
    print(f"   每站数量: {args.limit} 条")
    print()
    
    try:
        all_items, source_stats = asyncio.run(fetch_news(
            sources=sources,
            limit=args.limit,
            no_cache=args.no_cache,
            cache_hours=args.cache_hours,
        ))
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 采集失败: {e}")
        sys.exit(1)
    
    if not all_items:
        print("\n❌ 未获取到任何新闻")
        sys.exit(1)
    
    # 生成飞书精简版消息
    feishu_message = generate_feishu_summary(all_items, source_stats)
    
    if args.feishu:
        # 发送到飞书
        print("\n📤 发送到飞书...")
        try:
            from message import send
            result = send(
                message=feishu_message,
                target="user:ou_1ff98dde85af548188b059cfcb464208",
                channel="feishu"
            )
            print(f"✅ 已发送到飞书")
        except Exception as e:
            print(f"❌ 发送失败: {e}")
    else:
        # 打印到控制台
        print()
        print(feishu_message)
    
    # 保存到文件
    if args.output:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / args.output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(feishu_message)
        print(f"\n💾 已保存到: {output_path}")
    
    # 同时保存完整版到日志目录
    log_dir = Path(__file__).parent.parent.parent / "logs" / "daily"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"ai-news-{datetime.now().strftime('%Y%m%d-%H')}.md"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(feishu_message)
    print(f"💾 已缓存到: {log_file}")


if __name__ == "__main__":
    main()
