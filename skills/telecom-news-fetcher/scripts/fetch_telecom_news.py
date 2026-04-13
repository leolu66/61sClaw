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


def format_output(news, wechat_articles=None, operators=None, days=None, start_date=None, end_date=None):
    """
    格式化输出
    
    Args:
        news: 网站新闻列表
        wechat_articles: 公众号文章列表
        operators: 筛选的运营商
        days: 最近N天
        start_date: 起始日期
        end_date: 结束日期
    
    Returns:
        str: 格式化后的Markdown字符串
    """
    output = []
    
    # 标题
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 筛选条件说明
    filter_desc = []
    if operators:
        filter_desc.append(f"运营商：{','.join(operators)}")
    else:
        filter_desc.append("全运营商")
    
    if start_date and end_date:
        filter_desc.append(f"时间：{start_date} ~ {end_date}")
    else:
        filter_desc.append(f"最近{days}天")
    
    output.append(f"## 📡 运营商新闻 [{now}] | {' · '.join(filter_desc)}\n")
    
    # 重要新闻
    if news:
        output.append("### 🔝 重要新闻（按优先级排序）\n")
        
        for idx, item in enumerate(news[:15], 1):  # 最多显示15条重要新闻
            title = item.get('title', '无标题')
            url = item.get('url', '#')
            date = item.get('date', '')
            source = item.get('source', '未知')
            credibility = item.get('credibility', 1)
            news_type = item.get('type', '未分类')
            summary = item.get('summary', item.get('content', ''))[:150] + "..." if len(item.get('content', '')) > 150 else item.get('content', '')
            
            output.append(f"#### {idx}. [{title}]({url})\n")
            output.append(f"📅 {date} · 📢 来源：{source}（可信度：{credibility}分）\n")
            if summary:
                output.append(f"📝 摘要：{summary}\n")
            output.append(f"🏷️ 标签：{news_type}\n\n")
    
    # 分类统计
    if news:
        output.append("### 📊 分类统计\n")
        
        # 按类型统计
        type_count = {}
        for item in news:
            t = item.get('type', '其他')
            type_count[t] = type_count.get(t, 0) + 1
        type_str = ' · '.join([f"{k}：{v}条" for k, v in type_count.items()])
        output.append(f"- 新闻类型：{type_str}\n")
        
        # 按运营商统计
        operator_keywords = {
            '中国移动': ['中国移动', '中移动', 'China Mobile'],
            '中国电信': ['中国电信', '中电信', 'China Telecom'],
            '中国联通': ['中国联通', '中联通', 'China Unicom'],
            '中国铁塔': ['中国铁塔', '中铁塔', 'China Tower']
        }
        op_count = {}
        for item in news:
            title = item.get('title', '')
            for op, kws in operator_keywords.items():
                for kw in kws:
                    if kw in title:
                        op_count[op] = op_count.get(op, 0) + 1
                        break
        op_str = ' · '.join([f"{k}：{v}条" for k, v in op_count.items()])
        output.append(f"- 运营商分布：{op_str}\n\n")
    
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
            
            for item in items[:5]:  # 每个公众号最多显示5条
                title = item.get('title', '无标题')
                output.append(f"- {title}\n")
            
            output.append("")
    
    # 提示信息
    output.append("\n---\n")
    source_count = len(set([item.get('source', '') for item in news])) if news else 0
    output.append(f"*由 OpenClaw 运营商新闻技能自动生成 · 共检索{source_count}个来源，有效新闻{len(news)}条*\n")
    
    return ''.join(output)


def filter_by_operator(news_list, operators):
    """按运营商筛选新闻"""
    if not operators:
        return news_list
    
    operator_keywords = {
        '中国移动': ['中国移动', '中移动', 'China Mobile'],
        '中国电信': ['中国电信', '中电信', 'China Telecom'],
        '中国联通': ['中国联通', '中联通', 'China Unicom'],
        '中国铁塔': ['中国铁塔', '中铁塔', 'China Tower']
    }
    
    filtered = []
    target_keywords = []
    for op in operators:
        target_keywords.extend(operator_keywords.get(op, []))
    
    for news in news_list:
        title = news.get('title', '').lower()
        content = news.get('content', '').lower()
        for keyword in target_keywords:
            if keyword.lower() in title or keyword.lower() in content:
                filtered.append(news)
                break
    
    return filtered


def filter_by_date(news_list, start_date=None, end_date=None, days=None):
    """按时间范围筛选新闻"""
    if not start_date and not end_date and not days:
        return news_list
    
    from datetime import datetime, timedelta
    
    # 计算时间范围
    now = datetime.now()
    if days:
        start_date = (now - timedelta(days=days)).date()
        end_date = now.date()
    else:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    filtered = []
    for news in news_list:
        news_date_str = news.get('date', '')
        if not news_date_str:
            # 没有日期的新闻默认保留（假设是最近的）
            filtered.append(news)
            continue
        
        try:
            # 尝试解析日期
            if len(news_date_str) == 5:  # 格式如 04-12
                news_date = datetime.strptime(f"{now.year}-{news_date_str}", '%Y-%m-%d').date()
            elif len(news_date_str) == 10:  # 格式如 2026-04-12
                news_date = datetime.strptime(news_date_str, '%Y-%m-%d').date()
            else:
                # 日期格式不认识的也保留
                filtered.append(news)
                continue
            
            # 检查是否在范围内
            if start_date and news_date < start_date:
                continue
            if end_date and news_date > end_date:
                continue
                
            filtered.append(news)
            
        except Exception:
            # 解析失败也保留
            filtered.append(news)
            continue
    
    return filtered


def filter_by_type(news_list, types):
    """按新闻类型筛选"""
    if not types:
        return news_list
    
    type_keywords = {
        '业务动态': ['套餐调整', '5G-A', '算力网络', '云服务', '数据中心', '服务升级', '业务上线'],
        '政策公告': ['业务关停', '资费调整', '新规', '公告', '通知', '政策'],
        '技术创新': ['AI', '物联网', '6G研发', '网络切片', '技术突破', '专利', '研发'],
        '战略合作': ['联合', '合作', '签约', '共建', '战略合作', '签约仪式'],
        '重大事件': ['系统升级', '安全事件', '社会责任', '重大活动', '保障', '事故'],
        '财务数据': ['财报', '营收', '利润', '财务报告', 'Q1', 'Q2', 'Q3', 'Q4', '年报']
    }
    
    filtered = []
    target_keywords = []
    for t in types:
        target_keywords.extend(type_keywords.get(t, []))
    
    for news in news_list:
        title = news.get('title', '').lower()
        content = news.get('content', '').lower()
        for keyword in target_keywords:
            if keyword.lower() in title or keyword.lower() in content:
                # 添加类型标签
                news['type'] = t
                filtered.append(news)
                break
    
    return filtered


def calculate_score(news):
    """计算新闻综合得分，用于排序"""
    # 可信度得分
    source_scores = {
        '中国移动官网': 5,
        '中国电信官网': 5,
        '中国联通官网': 5,
        '中国铁塔官网': 5,
        '新华社': 4,
        '人民日报': 4,
        '央视新闻': 4,
        'C114通信网': 3,
        '通信世界网': 3,
        '人民邮电报': 3,
        '新浪财经': 2,
        '百度新闻': 2,
        '东方财富网': 2
    }
    
    credibility_score = source_scores.get(news.get('source', ''), 1)
    
    # 时效性得分：越新分数越高
    from datetime import datetime, timedelta
    try:
        news_date_str = news.get('date', '')
        if len(news_date_str) == 5:
            news_date = datetime.strptime(f"{datetime.now().year}-{news_date_str}", '%Y-%m-%d')
        elif len(news_date_str) == 10:
            news_date = datetime.strptime(news_date_str, '%Y-%m-%d')
        else:
            news_date = datetime.now() - timedelta(days=30)
        
        days_diff = (datetime.now() - news_date).days
        if days_diff <= 0:
            time_score = 5
        elif days_diff <= 3:
            time_score = 4
        elif days_diff <=7:
            time_score = 3
        elif days_diff <=15:
            time_score = 2
        else:
            time_score = 1
    except:
        time_score = 1
    
    # 重要性得分（根据标题关键词）
    important_keywords = ['战略合作', '5G-A', '6G', '财报', '资费调整', '全国性', '重大', '首个', '突破']
    important_score = 1
    title = news.get('title', '')
    for kw in important_keywords:
        if kw in title:
            important_score += 1
    important_score = min(important_score, 5)
    
    # 综合得分
    total_score = credibility_score * 0.4 + time_score * 0.3 + important_score * 0.3
    news['score'] = round(total_score, 1)
    news['credibility'] = credibility_score
    
    return total_score


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='运营商新闻获取器')
    parser.add_argument('--limit', '-n', type=int, default=10, 
                        help='每来源获取的新闻数量 (默认10)')
    parser.add_argument('--sources', '-s', type=str, default='',
                        help='指定来源，用逗号分隔 (如: c114,cww)')
    parser.add_argument('--operator', '-op', type=str, default='',
                        help='指定运营商，用逗号分隔 (如: 中国移动,中国电信)')
    parser.add_argument('--days', '-d', type=int, default=7,
                        help='获取最近N天的新闻 (默认7天)')
    parser.add_argument('--start', type=str, default='',
                        help='起始日期 (格式: 2026-04-01)')
    parser.add_argument('--end', type=str, default='',
                        help='结束日期 (格式: 2026-04-12)')
    parser.add_argument('--type', '-t', type=str, default='',
                        help='指定新闻类型，用逗号分隔 (如: 技术创新,战略合作)')
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
    
    # 调试：先输出原始新闻
    # print("原始新闻:", [item.get('title') + ' | ' + item.get('date', '') for item in news])
    
    # 按运营商筛选
    operators = None
    if args.operator:
        operators = [op.strip() for op in args.operator.split(',')]
        news = filter_by_operator(news, operators)
    
    # 按时间范围筛选
    start_date = args.start if args.start else None
    end_date = args.end if args.end else None
    days = args.days if not start_date and not end_date else None
    news = filter_by_date(news, start_date, end_date, days)
    
    # 按新闻类型筛选
    news_types = None
    if args.type:
        news_types = [t.strip() for t in args.type.split(',')]
        news = filter_by_type(news, news_types)
    
    # 计算得分并排序
    if news:
        for item in news:
            calculate_score(item)
        # 按得分降序、时间降序排序
        news.sort(key=lambda x: (-x.get('score', 0), x.get('date', '')), reverse=True)
    
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
    output = format_output(news, wechat_articles, operators, days, start_date, end_date)
    
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
