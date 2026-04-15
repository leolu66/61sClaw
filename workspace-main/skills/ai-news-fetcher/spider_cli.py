"""
命令行工具 - 测试配置和调试
"""
import asyncio
import sys
import logging
from pathlib import Path

import click
from lxml import html

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from spider.config_loader import ConfigLoader
from spider.extractors import FieldExtractor, extract_fields
from spider.engine import SpiderEngine, NewsItem
from spider.storage import StorageFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """新闻爬虫命令行工具"""
    pass


@cli.command()
@click.argument("site_name")
@click.option("--url", "-u", help="测试特定 URL（否则使用配置中的列表页）")
@click.option("--field", "-f", help="只测试特定字段")
@click.option("--detail", "-d", is_flag=True, help="测试详情页提取")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
def test(site_name: str, url: str, field: str, detail: bool, verbose: bool):
    """测试站点配置"""
    
    # 加载配置
    loader = ConfigLoader()
    config = loader.load_single(site_name)
    
    if not config:
        click.echo(f"❌ 未找到站点配置: {site_name}", err=True)
        sys.exit(1)
    
    site_config = config["site"]
    click.echo(f"\n🕷️  测试站点: {site_config['name']}")
    click.echo(f"📄 配置文件: {config['_meta']['file']}")
    click.echo(f"🔢 配置版本: {site_config.get('config_version', 'unknown')}")
    
    if detail:
        # 测试详情页
        _test_detail_page(config, url, field, verbose)
    else:
        # 测试列表页
        _test_list_page(config, url, field, verbose)


def _test_list_page(config: dict, test_url: str, field: str, verbose: bool):
    """测试列表页提取"""
    import aiohttp
    from lxml import html
    import json
    
    list_config = config["list_page"]
    request_config = config["site"].get("request", {})
    
    url = test_url or list_config["url"]
    
    click.echo(f"\n📃 测试列表页: {url}")
    
    # 检查是否为 JSON SSR 模式
    item_selector = list_config["item_selector"]
    if item_selector.get("type") == "json_ssr":
        _test_json_ssr_list_page(config, url, field, verbose)
        return
    
    async def fetch():
        async with aiohttp.ClientSession() as session:
            headers = request_config.get("headers", {})
            async with session.get(url, headers=headers) as resp:
                return await resp.text()
    
    html_content = asyncio.run(fetch())
    tree = html.fromstring(html_content)
    
    # 测试列表项选择（使用原始选择器）
    sel_type = item_selector.get("type", "xpath")
    sel_value = item_selector["value"]
    
    if sel_type == "xpath":
        items = tree.xpath(sel_value)
    elif sel_type == "css":
        items = tree.cssselect(sel_value)
    else:
        click.echo(f"❌ 未知的选择器类型: {sel_type}")
        return
    
    if not items:
        click.echo("❌ 未找到列表项，请检查 item_selector 配置")
        return
    
    click.echo(f"✅ 找到 {len(items)} 个列表项")
    
    # 测试字段提取
    fields_config = list_config.get("fields", {})
    
    if field:
        # 只测试指定字段
        if field not in fields_config:
            click.echo(f"❌ 字段 {field} 未在配置中定义")
            return
        fields_config = {field: fields_config[field]}
    
    # 显示前3个条目的提取结果
    show_count = min(3, len(items))
    for i, item in enumerate(items[:show_count], 1):
        click.echo(f"\n--- 条目 {i} ---")
        for field_name, field_conf in fields_config.items():
            try:
                extractor = FieldExtractor(field_conf)
                value = extractor.extract(item, url)
                value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                click.echo(f"  {field_name}: {value_str}")
            except Exception as e:
                click.echo(f"  {field_name}: ❌ {e}")


def _test_json_ssr_list_page(config: dict, url: str, field: str, verbose: bool):
    """测试 JSON SSR 模式的列表页提取（Vue/Nuxt 服务端渲染）"""
    import aiohttp
    from lxml import html
    import json
    
    list_config = config["list_page"]
    request_config = config["site"].get("request", {})
    fields_config = list_config.get("fields", {})
    base_url = config["site"]["base_url"]
    
    if field:
        if field not in fields_config:
            click.echo(f"❌ 字段 {field} 未在配置中定义")
            return
        fields_config = {field: fields_config[field]}
    
    async def fetch():
        async with aiohttp.ClientSession() as session:
            headers = request_config.get("headers", {})
            async with session.get(url, headers=headers) as resp:
                return await resp.text()
    
    html_content = asyncio.run(fetch())
    tree = html.fromstring(html_content)
    
    # 提取 JSON 数据
    json_script = tree.xpath('//script[@type="application/json"]/text()')
    if not json_script:
        click.echo("❌ 未找到 SSR JSON 数据")
        return
    
    data = json.loads(json_script[0])
    
    # 解析索引引用（Vue SSR 的压缩格式）
    def resolve_ref(ref):
        if isinstance(ref, int) and ref < len(data):
            return data[ref]
        return ref
    
    # 查找新闻列表
    news_list = []
    item_selector = list_config.get("item_selector", {})
    custom_list_index = item_selector.get("ssr_list_index")
    
    if custom_list_index is not None and isinstance(custom_list_index, int):
        if custom_list_index < len(data):
            raw_list = data[custom_list_index]
            if isinstance(raw_list, list):
                news_list = [resolve_ref(r) for r in raw_list]
    else:
        # 查找 InfoQ 格式的 aibriefsList
        for item in data:
            if isinstance(item, dict) and 'aibriefsList' in item:
                list_idx = item['aibriefsList']
                news_data = resolve_ref(list_idx)
                if isinstance(news_data, dict) and 'list' in news_data:
                    list_ref = news_data['list']
                    raw_list = resolve_ref(list_ref)
                    if isinstance(raw_list, list):
                        news_list = [resolve_ref(r) for r in raw_list]
                break
    
    click.echo(f"✅ 从 SSR JSON 中提取到 {len(news_list)} 条新闻")
    
    # 显示前3条
    show_count = min(3, len(news_list))
    for i, news in enumerate(news_list[:show_count], 1):
        click.echo(f"\n--- 条目 {i} ---")
        for field_name, field_conf in fields_config.items():
            field_type = field_conf.get("type")
            transform = field_conf.get("transform")
            
            if field_type == "json_ssr_field":
                json_key = field_conf["value"]
                if json_key in news:
                    value = resolve_ref(news[json_key])
                    
                    # 应用转换器
                    if transform == "aibase_link":
                        value = f"{base_url}/news/{value}"
                    elif transform == "timestamp_seconds_to_iso":
                        if isinstance(value, (int, float)):
                            value = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                    
                    value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    click.echo(f"  {field_name}: {value_str}")
                else:
                    click.echo(f"  {field_name}: (未找到)")
            elif field_type == "constant":
                click.echo(f"  {field_name}: {field_conf['value']}")


def _test_detail_page(config: dict, test_url: str, field: str, verbose: bool):
    """测试详情页提取"""
    import aiohttp
    
    detail_config = config.get("detail_page", {})
    request_config = config["site"].get("request", {})
    
    if not test_url:
        click.echo("❌ 测试详情页需要指定 --url 参数")
        sys.exit(1)
    
    click.echo(f"\n📄 测试详情页: {test_url}")
    
    async def fetch():
        async with aiohttp.ClientSession() as session:
            headers = request_config.get("headers", {})
            async with session.get(test_url, headers=headers) as resp:
                return await resp.text()
    
    html_content = asyncio.run(fetch())
    tree = html.fromstring(html_content)
    
    fields_config = detail_config.get("fields", {})
    
    if field:
        # 只测试指定字段
        if field not in fields_config:
            click.echo(f"❌ 字段 {field} 未在配置中定义")
            return
        fields_config = {field: fields_config[field]}
    
    click.echo("\n字段提取结果:")
    for field_name, field_conf in fields_config.items():
        try:
            extractor = FieldExtractor(field_conf)
            value = extractor.extract(tree, test_url)
            
            # 格式化输出
            if isinstance(value, list):
                click.echo(f"\n  {field_name} (列表, {len(value)} 项):")
                for i, v in enumerate(value[:5], 1):
                    v_str = str(v)[:80] + "..." if len(str(v)) > 80 else str(v)
                    click.echo(f"    [{i}] {v_str}")
                if len(value) > 5:
                    click.echo(f"    ... 还有 {len(value) - 5} 项")
            else:
                value_str = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                click.echo(f"  {field_name}: {value_str}")
                
        except Exception as e:
            click.echo(f"  {field_name}: ❌ {e}")


@cli.command()
@click.argument("site_name")
@click.option("--max-items", "-n", default=5, help="最大采集条目数")
@click.option("--output", "-o", help="输出文件路径")
@click.option("--format", "fmt", "-f", default="json", type=click.Choice(["json", "csv", "md"]))
def crawl(site_name: str, max_items: int, output: str, fmt: str):
    """运行单个站点采集"""
    
    # 加载配置
    loader = ConfigLoader()
    config = loader.load_single(site_name)
    
    if not config:
        click.echo(f"❌ 未找到站点配置: {site_name}", err=True)
        sys.exit(1)
    
    click.echo(f"\n🕷️  开始采集: {config['site']['name']}")
    click.echo(f"📊 计划采集: {max_items} 条\n")
    
    async def run():
        items = []
        async with SpiderEngine() as engine:
            async for item in engine.crawl_site(config, max_items):
                items.append(item)
                click.echo(f"✅ [{len(items)}] {item.title[:50]}...")
        return items
    
    items = asyncio.run(run())
    
    click.echo(f"\n✨ 采集完成: {len(items)} 条")
    
    # 保存结果
    if output:
        storage = StorageFactory.create(fmt, output)
        storage.save(items)
        click.echo(f"💾 已保存到: {output}")


@cli.command()
def list_sites():
    """列出所有可用站点配置"""
    loader = ConfigLoader()
    configs = loader.load_all(enabled_only=False)
    
    click.echo("\n📋 站点配置列表:\n")
    click.echo(f"{'名称':<15} {'版本':<15} {'状态':<8} {'来源文件'}")
    click.echo("-" * 60)
    
    for config in configs:
        site = config["site"]
        name = site.get("name", "N/A")
        version = site.get("config_version", "unknown")
        enabled = "✅ 启用" if site.get("enabled", True) else "⛔ 禁用"
        file = config["_meta"]["file"]
        
        click.echo(f"{name:<15} {version:<15} {enabled:<8} {file}")


@cli.command()
@click.argument("url")
@click.option("--selector", "-s", help="测试选择器")
@click.option("--type", "sel_type", default="xpath", type=click.Choice(["xpath", "css", "regex"]))
def probe(url: str, selector: str, sel_type: str):
    """探测网页结构，辅助编写选择器"""
    import aiohttp
    
    click.echo(f"\n🔍 探测 URL: {url}")
    
    async def fetch():
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()
    
    html_content = asyncio.run(fetch())
    tree = html.fromstring(html_content)
    
    # 显示基本信息
    title = tree.xpath("//title/text()")
    click.echo(f"📄 页面标题: {title[0] if title else 'N/A'}")
    
    # 自动发现可能的新闻列表
    click.echo("\n🤖 自动发现的新闻列表区域:")
    
    # 常见的列表容器选择器
    list_patterns = [
        "//article",
        "//div[contains(@class, 'article')]",
        "//div[contains(@class, 'news')]",
        "//div[contains(@class, 'post')]",
        "//div[contains(@class, 'item')]",
        "//li[contains(@class, 'item')]",
    ]
    
    for pattern in list_patterns:
        items = tree.xpath(pattern)
        if len(items) >= 3:
            click.echo(f"  发现 {len(items)} 个元素匹配: {pattern}")
            # 显示第一个元素的属性
            if items:
                elem = items[0]
                class_attr = elem.get("class", "")
                click.echo(f"    示例 class: {class_attr[:50] if class_attr else 'N/A'}")
    
    # 测试用户提供的选则器
    if selector:
        click.echo(f"\n🧪 测试选择器 [{sel_type}]: {selector}")
        
        try:
            if sel_type == "xpath":
                result = tree.xpath(selector)
            elif sel_type == "css":
                result = tree.cssselect(selector)
            else:
                import re
                result = re.findall(selector, html_content)
            
            click.echo(f"✅ 匹配到 {len(result)} 个元素")
            
            for i, elem in enumerate(result[:5], 1):
                if hasattr(elem, "text_content"):
                    text = elem.text_content().strip()[:100]
                    click.echo(f"  [{i}] {text}...")
                else:
                    click.echo(f"  [{i}] {str(elem)[:100]}...")
            
            if len(result) > 5:
                click.echo(f"  ... 还有 {len(result) - 5} 个")
                
        except Exception as e:
            click.echo(f"❌ 选择器错误: {e}")


if __name__ == "__main__":
    cli()
