"""
采集引擎 - 异步 HTTP 请求和调度
"""
import asyncio
import aiohttp
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator, Any
from urllib.parse import urljoin, urlparse
from lxml import html
import random
import time

from .extractors import FieldExtractor, ExtractionError

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """新闻条目数据类"""
    title: str
    summary: str = ""
    author: str = ""
    publish_time: Optional[datetime] = None
    url: str = ""
    source: str = ""  # 来源站点名称
    content: str = ""  # 完整内容（可选）
    tags: List[str] = field(default_factory=list)
    
    # 元数据
    crawled_at: datetime = field(default_factory=datetime.now)
    config_version: str = ""  # 采集时使用的配置版本
    
    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            "title": self.title,
            "summary": self.summary,
            "author": self.author,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "url": self.url,
            "source": self.source,
            "content": self.content,
            "tags": self.tags,
            "crawled_at": self.crawled_at.isoformat(),
            "config_version": self.config_version,
        }
    
    def is_valid(self) -> bool:
        """检查条目是否有效（至少有标题和URL）"""
        return bool(self.title and self.url)


@dataclass
class CrawlStats:
    """采集统计"""
    site_name: str
    total_requests: int = 0
    success_requests: int = 0
    failed_requests: int = 0
    items_extracted: int = 0
    items_valid: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.success_requests / self.total_requests
    
    def to_dict(self) -> dict:
        return {
            "site_name": self.site_name,
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "items_extracted": self.items_extracted,
            "items_valid": self.items_valid,
            "duration_seconds": self.duration_seconds,
            "success_rate": f"{self.success_rate:.1%}",
            "errors": self.errors[:5],  # 只保留前5个错误
        }


class SpiderEngine:
    """
    采集引擎
    
    负责：
    - HTTP 请求管理
    - 请求频率控制
    - 重试机制
    - 字段提取调度
    """
    
    def __init__(
        self,
        max_concurrent: int = 3,
        default_timeout: int = 30,
        default_delay: float = 1.0,
        respect_robots: bool = True,
    ):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.default_delay = default_delay
        self.respect_robots = respect_robots
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self._last_request_time: Dict[str, float] = {}  # 域名 -> 上次请求时间
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            limit_per_host=self.max_concurrent,
        )
        timeout = aiohttp.ClientTimeout(total=self.default_timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def crawl_site(
        self, 
        config: dict,
        max_items: Optional[int] = None,
    ) -> AsyncGenerator[NewsItem, None]:
        """
        采集单个站点
        
        Args:
            config: 站点配置
            max_items: 最大采集条目数（None 则无限制）
            
        Yields:
            NewsItem 对象
        """
        site_name = config["site"]["name"]
        stats = CrawlStats(site_name=site_name)
        
        logger.info(f"开始采集站点: {site_name}")
        
        try:
            # 判断采集模式：列表页模式 或 API 模式
            if "api" in config:
                async for item in self._crawl_api_mode(config, stats, max_items):
                    if item.is_valid():
                        stats.items_valid += 1
                        yield item
            else:
                async for item in self._crawl_list_mode(config, stats, max_items):
                    if item.is_valid():
                        stats.items_valid += 1
                        yield item
                        
        except Exception as e:
            logger.error(f"采集站点 {site_name} 异常: {e}")
            stats.errors.append(str(e))
        finally:
            stats.end_time = datetime.now()
            logger.info(f"站点 {site_name} 采集完成: {stats.to_dict()}")
    
    def _select_items(self, tree: html.HtmlElement, selector_config: dict) -> List[html.HtmlElement]:
        """
        选择列表项元素（保留元素对象，不转换为文本）
        
        Args:
            tree: HTML 树
            selector_config: 选择器配置 {type, value}
            
        Returns:
            元素列表
        """
        sel_type = selector_config.get("type", "xpath")
        sel_value = selector_config["value"]
        
        if sel_type == "xpath":
            result = tree.xpath(sel_value)
        elif sel_type == "css":
            result = tree.cssselect(sel_value)
        else:
            logger.warning(f"未知的选择器类型: {sel_type}")
            return []
        
        # 确保返回列表
        if result is None:
            return []
        if not isinstance(result, list):
            return [result] if result else []
        
        return result

    async def _crawl_list_mode(
        self, 
        config: dict, 
        stats: CrawlStats,
        max_items: Optional[int],
    ) -> AsyncGenerator[NewsItem, None]:
        """列表页采集模式"""
        site_config = config["site"]
        list_config = config["list_page"]
        detail_config = config.get("detail_page", {})
        
        base_url = site_config["base_url"]
        request_config = site_config.get("request", {})
        
        # 检查采集模式
        list_fields = list_config.get("fields", {})
        item_selector = list_config["item_selector"]
        
        # 检查是否为 JSON SSR 模式
        if item_selector.get("type") == "json_ssr":
            logger.info(f"[{site_config['name']}] 使用 JSON SSR 提取模式")
            async for item in self._crawl_json_ssr_mode(
                config, stats, max_items
            ):
                yield item
            return
        
        # 检查是否支持列表页直接提取
        list_page_only = "title" in list_fields and list_fields["title"].get("required", False)
        
        if list_page_only:
            logger.info(f"[{site_config['name']}] 使用列表页直接提取模式")
            async for item in self._crawl_list_only_mode(
                config, stats, max_items
            ):
                yield item
            return
        
        # 原有详情页模式代码...
        
        # 构建列表页 URL 列表
        list_urls = self._build_list_urls(list_config)
        items_count = 0
        
        for list_url in list_urls:
            if max_items and items_count >= max_items:
                break
            
            try:
                # 下载列表页
                html_content = await self._fetch(list_url, request_config)
                tree = html.fromstring(html_content)
                
                # 提取列表项（使用原始选择器，保留元素对象）
                item_selector = list_config["item_selector"]
                items = self._select_items(tree, item_selector)
                
                if not items:
                    logger.warning(f"列表页未找到条目: {list_url}")
                    continue
                
                logger.debug(f"列表页找到 {len(items)} 个条目")
                
                # 遍历列表项
                for item_elem in items:
                    if max_items and items_count >= max_items:
                        break
                    
                    try:
                        # 提取详情页链接
                        link_config = list_config["fields"]["link"]
                        link_extractor = FieldExtractor(link_config)
                        detail_url = link_extractor.extract(item_elem, list_url)
                        
                        if not detail_url:
                            continue
                        
                        # 下载详情页
                        detail_html = await self._fetch(detail_url, request_config)
                        detail_tree = html.fromstring(detail_html)
                        
                        # 提取详情字段
                        news = self._extract_news_item(
                            detail_tree, 
                            detail_url, 
                            detail_config, 
                            site_config
                        )
                        
                        if news:
                            stats.items_extracted += 1
                            items_count += 1
                            yield news
                            
                    except Exception as e:
                        logger.warning(f"提取条目失败: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"处理列表页失败 {list_url}: {e}")
                stats.errors.append(str(e))
                continue
    
    async def _crawl_api_mode(
        self,
        config: dict,
        stats: CrawlStats,
        max_items: Optional[int],
    ) -> AsyncGenerator[NewsItem, None]:
        """API 采集模式（直接返回 JSON 数据）"""
        # TODO: 实现 API 模式
        logger.warning("API 模式尚未实现")
        return
    
    def _extract_news_item(
        self,
        tree: html.HtmlElement,
        url: str,
        detail_config: dict,
        site_config: dict,
    ) -> Optional[NewsItem]:
        """从详情页提取新闻条目"""
        fields_config = detail_config.get("fields", {})
        
        fields = {}
        for field_name, field_conf in fields_config.items():
            try:
                extractor = FieldExtractor(field_conf)
                fields[field_name] = extractor.extract(tree, url)
            except ExtractionError as e:
                logger.debug(f"提取字段 {field_name} 失败: {e}")
                fields[field_name] = field_conf.get("default")
        
        # 构建 NewsItem
        news = NewsItem(
            title=fields.get("title", ""),
            summary=fields.get("summary", ""),
            author=fields.get("author", ""),
            url=url,
            source=site_config["name"],
            content=fields.get("content", ""),
            config_version=site_config.get("config_version", ""),
        )
        
        # 处理发布时间
        pub_time = fields.get("publish_time") or fields.get("update_time")
        if pub_time:
            if isinstance(pub_time, datetime):
                news.publish_time = pub_time
            elif isinstance(pub_time, str):
                # 尝试解析
                from dateutil import parser
                try:
                    news.publish_time = parser.parse(pub_time)
                except:
                    pass
        
        return news
    
    async def _crawl_list_only_mode(
        self,
        config: dict,
        stats: CrawlStats,
        max_items: Optional[int],
    ) -> AsyncGenerator[NewsItem, None]:
        """
        列表页直接提取模式
        所有字段直接从列表页提取，无需访问详情页
        """
        site_config = config["site"]
        list_config = config["list_page"]
        base_url = site_config["base_url"]
        request_config = site_config.get("request", {})
        
        list_urls = self._build_list_urls(list_config)
        items_count = 0
        
        for list_url in list_urls:
            if max_items and items_count >= max_items:
                break
            
            try:
                # 下载列表页
                html_content = await self._fetch(list_url, request_config)
                tree = html.fromstring(html_content)
                
                # 提取列表项（使用原始选择器，保留元素对象）
                item_selector = list_config["item_selector"]
                items = self._select_items(tree, item_selector)
                
                if not items:
                    logger.warning(f"列表页未找到条目: {list_url}")
                    continue
                
                logger.debug(f"列表页找到 {len(items)} 个条目")
                
                # 遍历列表项，直接从列表项提取所有字段
                for item_elem in items:
                    if max_items and items_count >= max_items:
                        break
                    
                    try:
                        news = self._extract_news_item_from_list_element(
                            item_elem, list_url, list_config, site_config
                        )
                        
                        if news:
                            stats.items_extracted += 1
                            items_count += 1
                            yield news
                            
                    except Exception as e:
                        logger.warning(f"提取条目失败: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"处理列表页失败 {list_url}: {e}")
                stats.errors.append(str(e))
                continue
    
    def _extract_news_item_from_list_element(
        self,
        item_elem,
        list_url: str,
        list_config: dict,
        site_config: dict,
    ) -> Optional[NewsItem]:
        """从列表项元素提取新闻条目（列表页直接模式）"""
        list_fields = list_config.get("fields", {})
        
        fields = {}
        for field_name, field_conf in list_fields.items():
            try:
                extractor = FieldExtractor(field_conf)
                fields[field_name] = extractor.extract(item_elem, list_url)
            except ExtractionError as e:
                logger.debug(f"提取字段 {field_name} 失败: {e}")
                fields[field_name] = field_conf.get("default")
        
        # 构建 NewsItem
        url = fields.get("link", list_url)
        news = NewsItem(
            title=fields.get("title", ""),
            summary=fields.get("summary", ""),
            author=fields.get("author", ""),
            url=url,
            source=site_config["name"],
            content=fields.get("content", ""),
            config_version=site_config.get("config_version", ""),
        )
        
        # 处理发布时间
        pub_time = fields.get("publish_time") or fields.get("update_time")
        if pub_time:
            if isinstance(pub_time, datetime):
                news.publish_time = pub_time
            elif isinstance(pub_time, str):
                from dateutil import parser
                try:
                    news.publish_time = parser.parse(pub_time)
                except:
                    # 解析失败时，将原始字符串存入额外字段
                    news.publish_time = None
                    # 使用一个特殊属性存储原始时间字符串
                    setattr(news, '_raw_publish_time', pub_time)
        
        return news

    async def _crawl_json_ssr_mode(
        self,
        config: dict,
        stats: CrawlStats,
        max_items: Optional[int],
    ) -> AsyncGenerator[NewsItem, None]:
        """
        JSON SSR 提取模式（Vue/Nuxt 服务端渲染）
        从 <script type="application/json"> 中提取数据
        """
        import json
        import re
        from lxml import html
        
        site_config = config["site"]
        list_config = config["list_page"]
        base_url = site_config["base_url"]
        request_config = site_config.get("request", {})
        
        list_url = list_config["url"]
        list_fields = list_config.get("fields", {})
        
        try:
            # 下载页面
            html_content = await self._fetch(list_url, request_config)
            tree = html.fromstring(html_content)
            
            # 提取 JSON 数据
            json_script = tree.xpath('//script[@type="application/json"]/text()')
            if not json_script:
                logger.error("未找到 SSR JSON 数据")
                return
            
            data = json.loads(json_script[0])
            
            # 解析索引引用格式，构建对象列表
            def resolve_ref(ref):
                if isinstance(ref, int) and ref < len(data):
                    return data[ref]
                return ref
            
            # 查找新闻列表
            news_list = []
            item_selector = list_config.get("item_selector", {})
            
            # 检查是否有自定义 ssr_list_index
            custom_list_index = item_selector.get("ssr_list_index")
            
            if custom_list_index is not None and isinstance(custom_list_index, int):
                # 使用指定的索引位置
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
            
            logger.info(f"从 SSR JSON 中提取到 {len(news_list)} 条新闻")
            
            items_count = 0
            for news in news_list:
                if max_items and items_count >= max_items:
                    break
                
                try:
                    # 提取字段
                    fields = {}
                    for field_name, field_conf in list_fields.items():
                        field_type = field_conf.get("type")
                        transform = field_conf.get("transform")
                        
                        if field_type == "json_ssr_field":
                            json_key = field_conf["value"]
                            if json_key in news:
                                value = resolve_ref(news[json_key])
                                
                                # 应用转换器
                                if transform == "aibase_link":
                                    # AiBase 链接格式: /news/{oid}
                                    value = f"{base_url}/news/{value}"
                                elif transform == "timestamp_seconds_to_iso":
                                    # 秒级时间戳转 ISO
                                    if isinstance(value, (int, float)):
                                        value = datetime.fromtimestamp(value).isoformat()
                                
                                fields[field_name] = value
                            else:
                                fields[field_name] = field_conf.get("default")
                        elif field_type == "constant":
                            fields[field_name] = field_conf["value"]
                        else:
                            fields[field_name] = field_conf.get("default")
                    
                    # 构建 NewsItem
                    url = fields.get("link", list_url)
                    news_item = NewsItem(
                        title=fields.get("title", ""),
                        summary=fields.get("summary", ""),
                        author=fields.get("author", ""),
                        url=url,
                        source=site_config["name"],
                        content="",
                        config_version=site_config.get("config_version", ""),
                    )
                    
                    # 处理时间戳（支持字符串 ISO 格式）
                    pub_time = fields.get("publish_time")
                    if pub_time:
                        if isinstance(pub_time, datetime):
                            news_item.publish_time = pub_time
                        elif isinstance(pub_time, str):
                            from dateutil import parser
                            try:
                                news_item.publish_time = parser.parse(pub_time)
                            except:
                                pass
                        elif isinstance(pub_time, (int, float)):
                            if pub_time > 1e10:
                                pub_time = pub_time / 1000
                            news_item.publish_time = datetime.fromtimestamp(pub_time)
                    
                    if news_item.is_valid():
                        stats.items_extracted += 1
                        items_count += 1
                        yield news_item
                        
                except Exception as e:
                    logger.warning(f"提取条目失败: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"JSON SSR 模式失败: {e}")
            stats.errors.append(str(e))

    async def _fetch(self, url: str, request_config: dict) -> str:
        """
        下载页面内容
        
        Args:
            url: 目标 URL
            request_config: 请求配置
            
        Returns:
            HTML 内容字符串
        """
        # 获取域名进行频率控制
        domain = urlparse(url).netloc
        
        # 礼貌延迟
        await self._respect_delay(domain, request_config)
        
        # 准备请求头
        headers = request_config.get("headers", {})
        if "User-Agent" not in headers:
            headers["User-Agent"] = self._get_random_ua()
        
        # 执行请求
        async with self.semaphore:
            try:
                async with self.session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.text()
                    self._last_request_time[domain] = time.time()
                    return content
                    
            except aiohttp.ClientError as e:
                logger.error(f"请求失败 {url}: {e}")
                raise
    
    async def _respect_delay(self, domain: str, request_config: dict):
        """遵守请求频率限制"""
        delay = request_config.get("delay", self.default_delay)
        
        if delay <= 0:
            return
        
        last_time = self._last_request_time.get(domain, 0)
        elapsed = time.time() - last_time
        
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.debug(f"等待 {wait_time:.2f}s 以遵守频率限制")
            await asyncio.sleep(wait_time)
    
    def _build_list_urls(self, list_config: dict) -> List[str]:
        """
        构建列表页 URL 列表
        
        支持：
        - 单页: url
        - 分页: pagination + page_start + page_max
        """
        urls = []
        
        if "pagination" in list_config:
            # 分页模式
            template = list_config["pagination"]
            start = list_config.get("page_start", 1)
            max_page = list_config.get("page_max", 1)
            
            for page in range(start, max_page + 1):
                # 支持多种分页格式：?page={page}, /page/{page}, 等
                url = template.format(page=page, offset=(page-1)*20)
                urls.append(url)
        else:
            # 单页模式
            urls.append(list_config["url"])
        
        return urls
    
    def _get_random_ua(self) -> str:
        """获取随机 User-Agent"""
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        return random.choice(uas)


# ==================== 便捷函数 ====================

async def crawl_single_site(config: dict, max_items: Optional[int] = None) -> List[NewsItem]:
    """快捷采集单个站点"""
    items = []
    async with SpiderEngine() as engine:
        async for item in engine.crawl_site(config, max_items):
            items.append(item)
    return items


async def crawl_multiple_sites(configs: List[dict], max_items_per_site: Optional[int] = None) -> Dict[str, List[NewsItem]]:
    """快捷采集多个站点"""
    results = {}
    
    async with SpiderEngine() as engine:
        for config in configs:
            site_name = config["site"]["name"]
            items = []
            async for item in engine.crawl_site(config, max_items_per_site):
                items.append(item)
            results[site_name] = items
    
    return results
