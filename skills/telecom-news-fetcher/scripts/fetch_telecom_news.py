# -*- coding: utf-8 -*-
"""
运营商新闻获取器
支持获取C114、通信世界网等网站新闻，以及微信公众号文章
"""

import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import argparse
import json
import os
import random
import time
from datetime import datetime

# 脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')

# 导入爬虫
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'spiders'))
from universal_spider import fetch_c114_news, fetch_cnii_news, fetch_cfyys_news, fetch_cww_news, fetch_ccidcom_news


def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_random_delay():
    """随机延迟"""
    config = load_config()
    delay = random.uniform(
        config['spider']['delay_min'],
        config['spider']['delay_max']
    )
    time.sleep(delay)


def fetch_all_news(sources=None, limit=10):
    """
    获取所有启用的新闻源
    
    Args:
        sources: 指定来源列表，如 ['c114', 'cww']
        limit: 每来源获取条数
    
    Returns:
        list: 所有新闻列表
    """
    config = load_config()
    all_news = []
    
    # 确定要获取的来源
    if sources:
        target_sources = {k: v for k, v in config['sources'].items() if k in sources}
    else:
        target_sources = {k: v for k, v in config['sources'].items() if v.get('enabled', False)}
    
    print(f"📡 正在获取运营商新闻...\n")
    
    for key, source in target_sources.items():
        if not source.get('enabled', False):
            continue
            
        print(f"🌐 正在获取: {source['name']}...")
        
        try:
            if key == 'c114':
                news = fetch_c114_news(key, limit)
            elif key == 'cnii':
                news = fetch_cnii_news(key, limit)
            elif key == 'cfyys':
                news = fetch_cfyys_news(key, limit)
            elif key == 'cww':
                news = fetch_cww_news(key, limit)
            elif key == 'ccidcom':
                news = fetch_ccidcom_news(key, limit)
            else:
                news = []
            
            all_news.extend(news)
            print(f"   ✅ 获取到 {len(news)} 条\n")
            
        except Exception as e:
            print(f"   ❌ 获取失败: {str(e)}\n")
    
    return all_news


def fetch_wechat_articles(accounts=None, limit=10):
    """
    获取微信公众号文章
    使用搜狗搜索方案
    
    Args:
        accounts: 公众号列表
        limit: 每公众号获取条数
    
    Returns:
        list: 文章列表
    """
    config = load_config()
    
    # 确定要获取的公众号
    if accounts is None:
        accounts = config['wechat'].get('accounts', [])
    
    if not accounts or not config['wechat'].get('enabled', False):
        return []
    
    print(f"📱 正在获取公众号文章...\n")
    
    # 调用公众号获取脚本
    wechat_script = os.path.join(SCRIPT_DIR, '..', 'wechat-article-fetcher', 'scripts', 'fetch_articles.py')
    
    # 检查公众号脚本是否存在
    if not os.path.exists(wechat_script):
        print(f"   ⚠️ 公众号获取脚本未找到: {wechat_script}")
        print(f"   💡 请确保已安装 wechat-article-fetcher 技能\n")
        return []
    
    all_articles = []
    
    for account in accounts:
        print(f"   🔍 搜索公众号: {account}...")
        
        try:
            # 使用搜狗方案
            import subprocess
            
            result = subprocess.run(
                [sys.executable, wechat_script, account, '-n', str(limit)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=SCRIPT_DIR
            )
            
            if result.returncode == 0:
                # 解析输出（简化处理）
                lines = result.stdout.strip().split('\n')
                for line in lines[:limit]:
                    if line.strip():
                        all_articles.append({
                            'title': line.strip(),
                            'source': account,
                            'type': 'wechat'
                        })
            
            get_random_delay()
            
        except Exception as e:
            print(f"   ❌ 获取失败: {str(e)}")
            continue
    
    print(f"   ✅ 共获取 {len(all_articles)} 篇公众号文章\n")
    
    return all_articles


def format_output(news, wechat_articles=None):
    """
    格式化输出
    
    Args:
        news: 网站新闻列表
        wechat_articles: 公众号文章列表
    
    Returns:
        str: 格式化后的Markdown字符串
    """
    output = []
    
    # 标题
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    output.append(f"## 📡 运营商新闻 [{now}]\n")
    
    # 网站新闻
    if news:
        output.append("### 🌐 网站新闻\n")
        
        # 按来源分组
        by_source = {}
        for item in news:
            source = item.get('source', '未知')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item)
        
        for source, items in by_source.items():
            output.append(f"**来源：{source}**\n")
            
            for item in items:
                title = item.get('title', '无标题')
                url = item.get('url', '#')
                date = item.get('date', '')
                
                date_str = f"📅 {date} · " if date else ""
                output.append(f"- [{title}]({url})\n  {date_str}🔗 阅读全文\n")
            
            output.append("")
    
    # 公众号文章
    if wechat_articles:
        output.append("\n### 📱 公众号精选\n")
        
        by_account = {}
        for item in wechat_articles:
            account = item.get('source', '未知')
            if account not in by_account:
                by_account[account] = []
            by_account[account].append(item)
        
        for account, items in by_account.items():
            output.append(f"**来源：{account}**\n")
            
            for item in items:
                title = item.get('title', '无标题')
                output.append(f"- {title}\n")
            
            output.append("")
    
    # 提示信息
    output.append("\n---\n")
    output.append("*由 OpenClaw 运营商新闻技能自动生成*\n")
    
    return ''.join(output)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='运营商新闻获取器')
    parser.add_argument('--limit', '-n', type=int, default=10, 
                        help='每来源获取的新闻数量 (默认10)')
    parser.add_argument('--sources', '-s', type=str, default='',
                        help='指定来源，用逗号分隔 (如: c114,cww)')
    parser.add_argument('--wechat', '-w', type=str, default='',
                        help='指定公众号，用逗号分隔 (如: 通信敢言,xxx)')
    parser.add_argument('--output', '-o', type=str, default='',
                        help='保存到文件')
    parser.add_argument('--no-wechat', action='store_true',
                        help='不获取公众号文章')
    
    args = parser.parse_args()
    
    config = load_config()
    limit = args.limit or config['output']['default_limit']
    
    # 解析来源
    sources = None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(',')]
    
    # 获取网站新闻
    news = fetch_all_news(sources, limit)
    
    # 获取公众号文章
    wechat_articles = []
    if not args.no_wechat:
        wechat_accounts = None
        if args.wechat:
            wechat_accounts = [w.strip() for w in args.wechat.split(',')]
        
        # 尝试获取公众号（可选功能）
        try:
            wechat_articles = fetch_wechat_articles(wechat_accounts, limit)
        except Exception as e:
            print(f"⚠️ 公众号获取跳过: {str(e)}")
    
    # 格式化输出
    output = format_output(news, wechat_articles)
    
    # 输出
    if args.output:
        output_path = os.path.join(SCRIPT_DIR, args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"💾 已保存到: {output_path}")
    else:
        print(output)
    
    print(f"\n📊 统计: 网站新闻 {len(news)} 条 | 公众号 {len(wechat_articles)} 篇")


if __name__ == '__main__':
    main()
