#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章获取工具 - 方案1（公众号后台接口版）
通过扫码登录公众号后台，利用后台搜索接口获取文章
数据更实时、更完整
"""

import argparse
import json
import re
import sys
import time
import io
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class WechatOfficialAccountFetcher:
    """
    微信公众号文章获取器 - 基于公众号后台接口
    
    原理：
    1. 用户扫码登录公众号后台 (mp.weixin.qq.com)
    2. 利用后台"新建图文消息"页面的搜索功能
    3. 搜索其他公众号的文章
    4. 获取文章列表和详情
    """
    
    BASE_URL = "https://mp.weixin.qq.com"
    
    def __init__(self, cookie: str = None, token: str = None):
        """
        初始化
        
        Args:
            cookie: 登录后的 cookie 字符串
            token: 公众号后台 token
        """
        self.cookie = cookie
        self.token = token
        self.session = self._create_session()
        
    def _create_session(self):
        """创建带 cookie 的 session"""
        import requests
        session = requests.Session()
        
        if self.cookie:
            # 解析 cookie 字符串
            cookies = {}
            for item in self.cookie.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
            session.cookies.update(cookies)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mp.weixin.qq.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        return session
    
    def search_official_account(self, keyword: str, page: int = 0) -> List[Dict]:
        """
        搜索公众号
        
        接口：公众号后台的搜索接口
        /cgi-bin/searchbiz?action=search_biz
        
        Args:
            keyword: 搜索关键词
            page: 页码
            
        Returns:
            公众号列表
        """
        if not self.token:
            return self._mock_search_result(keyword)
        
        url = f"{self.BASE_URL}/cgi-bin/searchbiz"
        params = {
            'action': 'search_biz',
            'token': self.token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': str(int(time.time() * 1000)),
            'query': keyword,
            'begin': page * 5,
            'count': 5
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('base_resp', {}).get('ret') == 0:
                return data.get('list', [])
            else:
                print(f"搜索失败: {data.get('base_resp', {}).get('err_msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"请求失败: {e}")
            return []
    
    def get_articles_by_fakeid(self, fakeid: str, page: int = 0) -> List[Dict]:
        """
        获取公众号文章列表
        
        接口：
        /cgi-bin/appmsg?action=list_ex
        
        Args:
            fakeid: 公众号的 fakeid
            page: 页码
            
        Returns:
            文章列表
        """
        if not self.token:
            return self._mock_article_result(fakeid, page)
        
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
            'type': '9'  # 图文消息
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('base_resp', {}).get('ret') == 0:
                return data.get('app_msg_list', [])
            else:
                print(f"获取文章失败: {data.get('base_resp', {}).get('err_msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"请求失败: {e}")
            return []
    
    def get_articles(self, account_name: str, limit: int = 10) -> Dict:
        """
        获取公众号文章（主入口）
        
        Args:
            account_name: 公众号名称
            limit: 获取文章数量
            
        Returns:
            包含公众号信息和文章列表的字典
        """
        print(f"🔍 正在搜索公众号: {account_name}\n")
        
        # 1. 搜索公众号
        accounts = self.search_official_account(account_name)
        
        if not accounts:
            print("❌ 未找到相关公众号")
            return {'account': account_name, 'articles': []}
        
        # 2. 选择最匹配的公众号
        target_account = self._select_best_match(accounts, account_name)
        
        print(f"✅ 找到公众号: {target_account.get('nickname', account_name)}")
        print(f"   微信号: {target_account.get('alias', 'N/A')}")
        print(f"   介绍: {target_account.get('signature', 'N/A')[:50]}...")
        print()
        
        # 3. 获取文章列表
        fakeid = target_account.get('fakeid')
        if not fakeid:
            print("❌ 无法获取公众号ID")
            return {'account': account_name, 'articles': []}
        
        print(f"📰 正在获取文章列表...\n")
        
        articles = []
        page = 0
        while len(articles) < limit:
            page_articles = self.get_articles_by_fakeid(fakeid, page)
            if not page_articles:
                break
            
            for article in page_articles:
                articles.append({
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'create_time': self._format_time(article.get('create_time')),
                    'digest': article.get('digest', '')[:100],
                    'cover': article.get('cover', ''),
                    'is_original': article.get('copyright_stat', 0) == 11
                })
                
                if len(articles) >= limit:
                    break
            
            page += 1
            time.sleep(0.5)  # 避免请求过快
        
        result = {
            'account': {
                'name': target_account.get('nickname', account_name),
                'alias': target_account.get('alias', ''),
                'signature': target_account.get('signature', ''),
                'fakeid': fakeid
            },
            'articles': articles[:limit]
        }
        
        return result
    
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
    
    def _format_time(self, timestamp) -> str:
        """格式化时间戳"""
        if not timestamp:
            return ''
        try:
            if isinstance(timestamp, str) and timestamp.isdigit():
                timestamp = int(timestamp)
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
        except:
            return str(timestamp)
    
    def _mock_search_result(self, keyword: str) -> List[Dict]:
        """
        模拟搜索结果（用于演示）
        
        实际使用时需要真实的 cookie 和 token
        """
        print("⚠️  未配置登录凭证，返回模拟数据")
        print("   如需真实数据，请先登录公众号后台获取 cookie 和 token\n")
        
        return [
            {
                'fakeid': 'mock_fakeid_123',
                'nickname': keyword,
                'alias': 'mock_alias',
                'signature': '这是一个模拟的公众号介绍...',
                'round_head_img': ''
            }
        ]
    
    def _mock_article_result(self, fakeid: str, page: int) -> List[Dict]:
        """模拟文章结果（用于演示）"""
        mock_articles = [
            {
                'title': f'示例文章 {page * 5 + 1}：如何使用 AI 提升工作效率',
                'link': 'https://mp.weixin.qq.com/s/mock_link_1',
                'create_time': int(time.time()) - 86400,
                'digest': '这是一篇关于 AI 提升工作效率的示例文章...',
                'cover': '',
                'copyright_stat': 11
            },
            {
                'title': f'示例文章 {page * 5 + 2}：2024年技术趋势展望',
                'link': 'https://mp.weixin.qq.com/s/mock_link_2',
                'create_time': int(time.time()) - 172800,
                'digest': '展望2024年的技术发展趋势...',
                'cover': '',
                'copyright_stat': 0
            },
            {
                'title': f'示例文章 {page * 5 + 3}：深度学习的未来',
                'link': 'https://mp.weixin.qq.com/s/mock_link_3',
                'create_time': int(time.time()) - 259200,
                'digest': '探讨深度学习技术的未来发展方向...',
                'cover': '',
                'copyright_stat': 11
            }
        ]
        return mock_articles if page < 2 else []


def print_result(result: Dict):
    """打印结果"""
    account = result.get('account', {})
    articles = result.get('articles', [])
    
    print(f"\n📊 公众号信息")
    print(f"   名称: {account.get('name', 'N/A')}")
    print(f"   微信号: {account.get('alias', 'N/A')}")
    print(f"   介绍: {account.get('signature', 'N/A')[:60]}...")
    print()
    
    print(f"📝 文章列表 (共 {len(articles)} 篇)")
    print("-" * 60)
    
    for i, article in enumerate(articles, 1):
        original_tag = "[原创]" if article.get('is_original') else ""
        print(f"\n{i}. {article.get('title', 'Unknown')} {original_tag}")
        print(f"   时间: {article.get('create_time', 'N/A')}")
        print(f"   链接: {article.get('link', 'N/A')}")
        if article.get('digest'):
            print(f"   摘要: {article.get('digest')[:80]}...")
    
    print()


def main():
    parser = argparse.ArgumentParser(description='微信公众号文章获取工具（公众号后台接口版）')
    parser.add_argument('account', help='公众号名称')
    parser.add_argument('-n', '--num', type=int, default=10, help='获取文章数量（默认10篇）')
    parser.add_argument('-c', '--cookie', help='登录后的 cookie 字符串')
    parser.add_argument('-t', '--token', help='公众号后台 token')
    parser.add_argument('-o', '--output', help='输出文件路径（JSON格式）')
    
    args = parser.parse_args()
    
    # 初始化获取器
    fetcher = WechatOfficialAccountFetcher(
        cookie=args.cookie,
        token=args.token
    )
    
    # 获取文章
    result = fetcher.get_articles(args.account, args.num)
    
    # 打印结果
    print_result(result)
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存到: {args.output}")
    
    # 输出JSON到stdout
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
