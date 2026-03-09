#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpiderEngine - 采集引擎
整合配置加载、请求调度、页面下载、数据提取
"""

import time
import random
from typing import List, Dict, Optional
from pathlib import Path

from config_loader import ConfigLoader
from extractor import GenericExtractor, XPathExtractor


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self):
        self.last_request_time = {}
        self.request_counts = {}
    
    def apply(self, site_name: str, strategy: Dict):
        """应用抓取策略"""
        now = time.time()
        
        # 检查请求间隔
        delay = strategy.get('delay_between_requests', 6)
        last_time = self.last_request_time.get(site_name, 0)
        elapsed = now - last_time
        
        if elapsed < delay:
            sleep_time = delay - elapsed
            print(f"[限流] {site_name} 等待 {sleep_time:.1f} 秒")
            time.sleep(sleep_time)
        
        # 更新记录
        self.last_request_time[site_name] = time.time()


class PageDownloader:
    """页面下载器"""
    
    def __init__(self):
        self.session = None
    
    def fetch(self, url: str, config: Dict) -> Optional[str]:
        """获取页面内容"""
        method = config.get('fetch', {}).get('method', 'requests')
        
        if method == 'playwright':
            return self._fetch_with_playwright(url, config)
        else:
            return self._fetch_with_requests(url, config)
    
    def _fetch_with_requests(self, url: str, config: Dict) -> Optional[str]:
        """使用requests获取"""
        import requests
        
        headers = config.get('fetch', {}).get('headers', {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        timeout = config.get('fetch', {}).get('strategy', {}).get('timeout', 15)
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.encoding = response.apparent_encoding or 'utf-8'
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"[错误] HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[错误] 请求失败: {e}")
            return None
    
    def _fetch_with_playwright(self, url: str, config: Dict) -> Optional[str]:
        """使用Playwright获取"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                wait_for = config.get('fetch', {}).get('playwright', {}).get('wait_for', 'networkidle')
                wait_timeout = config.get('fetch', {}).get('playwright', {}).get('wait_timeout', 30000)
                
                page.goto(url, wait_until=wait_for, timeout=wait_timeout)
                page.wait_for_timeout(3000)  # 额外等待3秒
                
                html = page.content()
                browser.close()
                
                return html
                
        except ImportError:
            print("[错误] Playwright未安装: pip install playwright")
            return None
        except Exception as e:
            print(f"[错误] Playwright失败: {e}")
            return None


class AntiCrawlDetector:
    """反爬检测器"""
    
    INDICATORS = [
        '滑块验证',
        '验证码',
        '访问过于频繁',
        '请稍后重试',
        '您的访问被阻断',
        '403 Forbidden',
        '429 Too Many Requests',
    ]
    
    def detect(self, html: str) -> bool:
        """检测是否触发反爬"""
        if not html:
            return False
        
        for indicator in self.INDICATORS:
            if indicator in html:
                return True
        
        return False
    
    def get_cooldown_time(self, config: Dict) -> int:
        """获取冷却时间"""
        return config.get('anti_crawl', {}).get('mitigation', {}).get('cooldown_minutes', 60)


class SpiderEngine:
    """采集引擎"""
    
    def __init__(self, config_dir: str = "site-configs"):
        self.config_loader = ConfigLoader(config_dir)
        self.downloader = PageDownloader()
        self.rate_limiter = RateLimiter()
        self.anti_crawl_detector = AntiCrawlDetector()
        
        # 加载配置
        self.config_loader.load_all()
    
    def fetch_site(self, site_name: str, limit: int = 5) -> List[Dict]:
        """抓取单个站点"""
        config = self.config_loader.get(site_name)
        if not config:
            print(f"[错误] 未找到配置: {site_name}")
            return []
        
        # 检查是否启用
        if not config.get('site', {}).get('enabled', True):
            print(f"[跳过] {site_name} 已禁用")
            return []
        
        site_name_cn = config.get('site', {}).get('name', site_name)
        print(f"\n[开始] 抓取 {site_name_cn}")
        
        # 检查反爬状态
        anti_crawl = config.get('anti_crawl', {})
        if anti_crawl.get('detected') and anti_crawl.get('status') == 'blocked':
            print(f"[跳过] {site_name} 当前被反爬拦截")
            return []
        
        # 应用限流策略
        strategy = config.get('fetch', {}).get('strategy', {})
        self.rate_limiter.apply(site_name, strategy)
        
        # 获取页面
        url = config.get('site', {}).get('base_url', '')
        html = self.downloader.fetch(url, config)
        
        if not html:
            print(f"[错误] {site_name} 页面下载失败")
            return []
        
        # 检测反爬
        if self.anti_crawl_detector.detect(html):
            print(f"[警告] {site_name} 触发反爬措施")
            return []
        
        # 提取数据
        extractor = self._get_extractor(config)
        articles = extractor.extract(html)
        
        # 限制数量
        articles = articles[:limit]
        
        # 添加来源信息
        for article in articles:
            article['source'] = site_name_cn
        
        print(f"[完成] {site_name_cn} 获取 {len(articles)} 条新闻")
        return articles
    
    def _get_extractor(self, config: Dict):
        """获取提取器"""
        extractor_type = config.get('extractor', 'default')
        
        if extractor_type == 'default':
            return GenericExtractor(config)
        elif extractor_type == 'xpath':
            return XPathExtractor(config)
        elif extractor_type == 'aibase':
            from aibase_extractor import AibaseExtractor
            return AibaseExtractor(config)
        else:
            # 自定义提取器，后续扩展
            print(f"[警告] 未知提取器类型: {extractor_type}，使用默认")
            return GenericExtractor(config)
    
    def fetch_all(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """抓取所有启用站点"""
        results = {}
        
        sites = self.config_loader.get_enabled_sites()
        
        for site_name in sites:
            articles = self.fetch_site(site_name, limit)
            results[site_name] = articles
        
        return results


if __name__ == "__main__":
    # 测试采集引擎
    engine = SpiderEngine("../site-configs")
    
    print("=" * 50)
    print("AI新闻获取器 - 配置化版本测试")
    print("=" * 50)
    
    # 测试单个站点
    results = engine.fetch_site("qbitai", limit=3)
    
    if results:
        print(f"\n提取结果:")
        for i, article in enumerate(results, 1):
            print(f"\n[{i}] {article.get('title', 'N/A')[:50]}...")
            print(f"    链接: {article.get('link', 'N/A')[:60]}...")
            print(f"    时间: {article.get('time', 'N/A')}")
