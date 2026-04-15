#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量获取微信公众号文章列表
"""

import json
import random
import sys
import time
from pathlib import Path
import re
import requests
from datetime import datetime
from typing import List, Dict

# 配置
COOKIE = "appmsglist_action_3633754955=card; rewardsn=; wxtokenkey=777; _qpsvr_localtk=0.9655426738828691; uin=o0285967115; RK=uapCBvbRUE; ptcz=7c89f8d2d5488d6b0285e160e073230d6bb13c7ba484e2d7d110c1d73dc6c72f; skey=@5ghT1dJcB; _qimei_uuid42=1a20a01121f100e35e8290b23a5d8eaff5946df0f9; _qimei_fingerprint=6b3747d240fb686bbbdcee7241ee6ed3; _qimei_i_3=5af16683c153028dc0c6ac3253d521e0a3bbf1f7105d05d6b08d2d5b70932238676b31943989e28eafb6; _qimei_h38=e98840005e8290b23a5d8eaf0200000601a20a; poc_sid=HMN-kWmjn5_f253bu_sAFQuVsM75Gb59wDJ0xbK7; pac_uid=0_W293YBhXEC8jk; omgid=0_W293YBhXEC8jk; _qimei_q36=; ua_id=A7KHQRUxvjanzJ9LAAAAAKeJgYkDgYVivOuCdHXf0Ok=; wxuin=71342090718601; xid=f1c71428266adc9f6b357a55bd71a2f8; mm_lang=zh_CN; uuid=00a2f92be2b15b80c42d0db17520ceaa; cert=AMS1JAPVvkg0gWSIFMNUf3Nxg7_BA3x0; data_bizuin=3633754955; bizuin=3633754955; master_user=gh_40047c05299b; master_sid=UEVVeFRDS18zTFJWektXSmtqdEFUV0dRajBjYVBEYWk1QXR6d1E4S3JYNjJMWGNLa2pZNWMzWWhsVWloaFhBWlF4TG1RX2VXNVp3VkxJQnhRaFJ5NlVPSWhIdDEycFpyTFk1cTk4QXF5OUdQNkZneGlFNXJmQ3JDbzZJTUFjUGNPZzZrbVBCZHFWOGNHSzFE; master_ticket=ff0824aa6084b9fde73970e6dc7fde3f; data_ticket=nieaWuRgrybk+lZazgRi+Zh2ZFrXk6Pe+SKmVE/6V6WJVuNs4y1uHjQtbameqi/d; rand_info=CAESIJRZ++YQho8y359357GvI6FrD6mnC4aaWrqFk9uRz253; slave_bizuin=3633754955; slave_user=gh_40047c05299b; slave_sid=ZXZiQkFTN3VlRXd5U2RVS1hvaUFwcFAzaUZjOWpmTVZpM2VwaGxlMzhzRGpGWkhoVlZ4MUtuRE40dUJsY2pURXFWNjBpRjUwSDZMQ19CRlRFYVRHYTBCenJMcHRvemxVZFVlVHU3aE9oTFFHakh0UTFmNDljNDlVdDc3U0JCNmNQNWVicjFnWFNMOEM3U3FB; __wx_phantom_mark__=M1eFhHZD7e; _qimei_i_1=5ede77d79c5258dfc197fe350e8c71e9f7bca6f2435e578ae1de7e582493206c6163319539d8e0dc87bfc4e0; _clck=3633754955|1|g3q|0; _clsk=udyj10|1771573626949|1|1|mp.weixin.qq.com/weheat-agent/payload/record"
TOKEN = "655521572"

# 公众号列表
ACCOUNTS = [
    "究模智",
    "智猩猩AI",
    "架构师",
    "PaperAgent",
    "苏哲管理咨询",
    "AI寒武纪",
    "苍何",
    "腾讯研究院",
    "InfoQ",
    "逛逛GitHub",
    "熵衍AI",
    "AgenticAI",
    "AI产品阿颖"
]

# 输出目录
OUTPUT_DIR = Path(r"D:\anthropic\wechat\2025-02-20")

# 每个公众号获取的文章数量
ARTICLES_PER_ACCOUNT = 5


class WechatOfficialAccountFetcher:
    BASE_URL = "https://mp.weixin.qq.com"
    
    def __init__(self, cookie: str = None, token: str = None):
        self.cookie = cookie
        self.token = token
        self.session = self._create_session()
        
    def _create_session(self):
        session = requests.Session()
        
        if self.cookie:
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
                return []
        except Exception as e:
            return []
    
    def get_articles_by_fakeid(self, fakeid: str, page: int = 0) -> List[Dict]:
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
                return []
        except Exception as e:
            return []
    
    def get_articles(self, account_name: str, limit: int = 10) -> Dict:
        accounts = self.search_official_account(account_name)
        
        if not accounts:
            return {'account': account_name, 'articles': []}
        
        target_account = self._select_best_match(accounts, account_name)
        
        fakeid = target_account.get('fakeid')
        if not fakeid:
            return {'account': account_name, 'articles': []}
        
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
            time.sleep(0.5)
        
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
        keyword_lower = keyword.lower()
        
        for account in accounts:
            if account.get('nickname', '').lower() == keyword_lower:
                return account
        
        for account in accounts:
            if keyword_lower in account.get('nickname', '').lower():
                return account
        
        return accounts[0] if accounts else {}
    
    def _format_time(self, timestamp) -> str:
        if not timestamp:
            return ''
        try:
            if isinstance(timestamp, str) and timestamp.isdigit():
                timestamp = int(timestamp)
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
        except:
            return str(timestamp)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    shuffled_accounts = ACCOUNTS.copy()
    random.shuffle(shuffled_accounts)
    
    fetcher = WechatOfficialAccountFetcher(cookie=COOKIE, token=TOKEN)
    
    summary = {}
    
    for idx, account_name in enumerate(shuffled_accounts, 1):
        try:
            result = fetcher.get_articles(account_name, limit=ARTICLES_PER_ACCOUNT)
            
            filename = sanitize_filename(account_name) + ".json"
            output_path = OUTPUT_DIR / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            articles_count = len(result.get('articles', []))
            summary[account_name] = articles_count
            
        except Exception as e:
            summary[account_name] = 0
        
        if idx < len(shuffled_accounts):
            time.sleep(random.uniform(3, 5))
    
    # 保存汇总
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_accounts': len(ACCOUNTS),
            'total_articles': sum(summary.values()),
            'details': summary
        }, f, ensure_ascii=False, indent=2)
    
    # 输出结果
    print("\n=== 获取结果汇总 ===")
    for account_name in ACCOUNTS:
        count = summary.get(account_name, 0)
        print(f"{account_name}: {count} 篇")
    print(f"\n总计: {len(ACCOUNTS)} 个公众号, {sum(summary.values())} 篇文章")


if __name__ == '__main__':
    main()
