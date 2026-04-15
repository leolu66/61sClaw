#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 文章列表获取模块
通过公众号后台接口获取文章列表
"""

import time
import random
from typing import List, Dict, Optional
import requests


class ArticleListFetcher:
    """公众号文章列表获取器"""
    
    BASE_URL = "https://mp.weixin.qq.com"
    
    def __init__(self, cookie: str = None, token: str = None):
        self.cookie = cookie
        self.token = token
        self.session = self._create_session()
        self.request_count = 0
        
    def _create_session(self) -> requests.Session:
        """创建带 cookie 的 session"""
        session = requests.Session()
        
        if self.cookie:
            cookies = {}
            for item in self.cookie.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
            session.cookies.update(cookies)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mp.weixin.qq.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        return session
    
    def _random_delay(self, min_sec: float = 1, max_sec: float = 3):
        """随机延迟，避免被检测"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def search_account(self, keyword: str) -> Optional[Dict]:
        """
        搜索公众号
        
        Args:
            keyword: 公众号名称
            
        Returns:
            公众号信息字典，未找到返回 None
        """
        if not self.token:
            print(f"[警告] 未配置 token，无法搜索公众号: {keyword}")
            return None
        
        url = f"{self.BASE_URL}/cgi-bin/searchbiz"
        params = {
            'action': 'search_biz',
            'token': self.token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': str(int(time.time() * 1000)),
            'query': keyword,
            'begin': 0,
            'count': 5
        }
        
        try:
            self._random_delay()
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('base_resp', {}).get('ret') == 0:
                accounts = data.get('list', [])
                if accounts:
                    # 返回最匹配的结果
                    return self._select_best_match(accounts, keyword)
            else:
                print(f"[错误] 搜索失败: {data.get('base_resp', {}).get('err_msg', '未知错误')}")
                
        except Exception as e:
            print(f"[错误] 请求失败: {e}")
        
        return None
    
    def get_articles(self, fakeid: str, limit: int = 10) -> List[Dict]:
        """
        获取公众号文章列表
        
        Args:
            fakeid: 公众号 fakeid
            limit: 获取数量
            
        Returns:
            文章列表
        """
        if not self.token:
            print("[警告] 未配置 token，无法获取文章列表")
            return []
        
        articles = []
        page = 0
        
        while len(articles) < limit:
            batch = self._fetch_article_batch(fakeid, page)
            if not batch:
                break
            
            for article in batch:
                articles.append({
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'create_time': article.get('create_time', 0),
                    'digest': article.get('digest', ''),
                    'cover': article.get('cover', ''),
                    'is_original': article.get('copyright_stat', 0) == 11
                })
                
                if len(articles) >= limit:
                    break
            
            page += 1
            self._random_delay(1, 2)  # 批次间延迟
        
        return articles[:limit]
    
    def _fetch_article_batch(self, fakeid: str, page: int) -> List[Dict]:
        """获取一批文章"""
        url = f"{self.BASE_URL}/cgi-bin/appmsg"
        params = {
            'action': 'list_ex',
            'token': self.token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': str(int(time.time() * 1000)),
            'fakeid': fakeid,
            'query': '',
            'begin': page * 5,
            'count': 5,
            'type': '9'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('base_resp', {}).get('ret') == 0:
                return data.get('app_msg_list', [])
            else:
                print(f"[错误] 获取文章失败: {data.get('base_resp', {}).get('err_msg', '未知错误')}")
                
        except Exception as e:
            print(f"[错误] 请求失败: {e}")
        
        return []
    
    def _select_best_match(self, accounts: List[Dict], keyword: str) -> Dict:
        """选择最匹配的公众号"""
        keyword_lower = keyword.lower()
        
        # 优先完全匹配
        for account in accounts:
            if account.get('nickname', '').lower() == keyword_lower:
                return account
        
        # 其次包含匹配
        for account in accounts:
            if keyword_lower in account.get('nickname', '').lower():
                return account
        
        # 默认返回第一个
        return accounts[0] if accounts else {}
    
    def fetch_account_articles(self, account_name: str, limit: int = 10,
                                min_articles: int = 3, days_threshold: int = 3) -> Dict:
        """
        获取指定公众号的文章列表（主入口）
        
        智能数量策略：
        - 先获取最多 limit 篇文章
        - 如果前 min_articles 篇文章都在 days_threshold 天内，则继续获取更多
        - 否则只返回最近 days_threshold 天内的文章
        
        Args:
            account_name: 公众号名称
            limit: 最大获取数量
            min_articles: 最少文章数
            days_threshold: 天数阈值
            
        Returns:
            包含公众号信息和文章列表的字典
        """
        print(f"\n[搜索] 正在查找公众号: {account_name}")
        
        account = self.search_account(account_name)
        if not account:
            return {
                'account': {'name': account_name},
                'articles': [],
                'error': '未找到公众号'
            }
        
        print(f"[成功] 找到公众号: {account.get('nickname')}")
        print(f"       微信号: {account.get('alias', 'N/A')}")
        
        fakeid = account.get('fakeid')
        if not fakeid:
            return {
                'account': {'name': account_name},
                'articles': [],
                'error': '无法获取公众号ID'
            }
        
        print(f"[获取] 正在读取文章列表 (智能数量)...")
        
        # 获取文章列表（智能数量策略）
        articles = self._get_articles_smart(
            fakeid, 
            limit=limit,
            min_articles=min_articles,
            days_threshold=days_threshold
        )
        
        print(f"[完成] 成功获取 {len(articles)} 篇文章")
        
        return {
            'account': {
                'name': account.get('nickname', account_name),
                'alias': account.get('alias', ''),
                'signature': account.get('signature', ''),
                'fakeid': fakeid
            },
            'articles': articles
        }
    
    def _get_articles_smart(self, fakeid: str, limit: int = 10,
                           min_articles: int = 3, days_threshold: int = 3) -> List[Dict]:
        """
        智能获取文章列表
        
        策略：
        1. 先获取最多 limit 篇
        2. 检查前 min_articles 篇是否都在 days_threshold 天内
        3. 如果是，返回全部；否则只返回 days_threshold 天内的文章
        """
        import time
        from datetime import datetime, timedelta
        
        all_articles = []
        page = 0
        cutoff_time = time.time() - (days_threshold * 24 * 3600)
        
        seen_links = set()  # 用于去重
        
        while len(all_articles) < limit:
            batch = self._fetch_article_batch(fakeid, page)
            if not batch:
                break
            
            for article in batch:
                link = article.get('link', '')
                
                # 跳过重复文章（根据链接去重）
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                article_data = {
                    'title': article.get('title', ''),
                    'link': link,
                    'create_time': article.get('create_time', 0),
                    'digest': article.get('digest', ''),
                    'cover': article.get('cover', ''),
                    'is_original': article.get('copyright_stat', 0) == 11
                }
                all_articles.append(article_data)
                
                if len(all_articles) >= limit:
                    break
            
            page += 1
            self._random_delay(1, 2)
        
        if not all_articles:
            return []
        
        # 智能数量判断
        if len(all_articles) >= min_articles:
            # 检查前 min_articles 篇的时间
            recent_count = sum(
                1 for a in all_articles[:min_articles]
                if a['create_time'] > cutoff_time
            )
            
            if recent_count < min_articles:
                # 发布不频繁，只返回最近 days_threshold 天的文章
                filtered = [a for a in all_articles if a['create_time'] > cutoff_time]
                if filtered:
                    print(f"       发布频率较低，仅返回最近{days_threshold}天的 {len(filtered)} 篇")
                    return filtered
        
        return all_articles
