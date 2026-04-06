#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 配置
DATA_FILE = Path(__file__).parent.parent / "output" / "models_data_full.json"
DEFAULT_LIMIT = 10

def load_model_data():
    """加载全量模型数据"""
    if not DATA_FILE.exists():
        return None, "模型数据文件不存在，请先运行 fetch_models.py 爬取数据"
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"加载数据失败：{str(e)}"

def get_all_models(data):
    """获取所有模型的扁平列表"""
    all_models = []
    for category in data:
        if 'models' in category:
            for model in category['models']:
                model['category'] = category['name']
                all_models.append(model)
        if 'subGroups' in category:
            for sub in category['subGroups']:
                if 'models' in sub:
                    for model in sub['models']:
                        model['category'] = f"{category['name']}/{sub['name']}"
                        all_models.append(model)
    return all_models

def parse_price(price_str):
    """解析价格字符串，返回数字"""
    if not price_str or price_str == "":
        return 0
    match = re.search(r'([\d.]+)', price_str)
    if match:
        return float(match.group(1))
    return 0

def parse_context_length(context_str):
    """解析上下文长度，返回K数"""
    if not context_str or context_str == "":
        return 0
    context_str = context_str.lower()
    if 'm' in context_str:
        match = re.search(r'([\d.]+)m', context_str)
        if match:
            return int(float(match.group(1)) * 1024)
    match = re.search(r'([\d.]+)k', context_str)
    if match:
        return int(float(match.group(1)))
    return 0

def parse_release_time(release_str):
    """解析发布时间，返回datetime对象"""
    if not release_str or release_str == "":
        return None
    try:
        return datetime.strptime(release_str, "%Y-%m-%d")
    except:
        return None

def filter_models(models, filters):
    """根据过滤条件筛选模型"""
    filtered = []
    for model in models:
        match = True
        
        # 时间范围过滤
        if 'release_after' in filters:
            release_time = parse_release_time(model.get('releaseTime', ''))
            if not release_time or release_time < filters['release_after']:
                match = False
        if 'release_before' in filters:
            release_time = parse_release_time(model.get('releaseTime', ''))
            if not release_time or release_time > filters['release_before']:
                match = False
        
        # 价格过滤
        if 'input_price_min' in filters:
            price = parse_price(model.get('inputPrice', ''))
            if price < filters['input_price_min']:
                match = False
        if 'input_price_max' in filters:
            price = parse_price(model.get('inputPrice', ''))
            if price > filters['input_price_max']:
                match = False
        if 'output_price_min' in filters:
            price = parse_price(model.get('outputPrice', ''))
            if price < filters['output_price_min']:
                match = False
        if 'output_price_max' in filters:
            price = parse_price(model.get('outputPrice', ''))
            if price > filters['output_price_max']:
                match = False
        
        # 上下文长度过滤
        if 'context_min' in filters:
            context = parse_context_length(model.get('contextLength', ''))
            if context < filters['context_min']:
                match = False
        if 'context_max' in filters:
            context = parse_context_length(model.get('contextLength', ''))
            if context > filters['context_max']:
                match = False
        
        # 标签过滤
        if 'include_tags' in filters:
            model_tags = [tag.lower() for tag in model.get('tags', [])]
            for tag in filters['include_tags']:
                if tag.lower() not in model_tags:
                    match = False
                    break
        if 'exclude_tags' in filters:
            model_tags = [tag.lower() for tag in model.get('tags', [])]
            for tag in filters['exclude_tags']:
                if tag.lower() in model_tags:
                    match = False
                    break
        
        # 分类过滤
        if 'categories' in filters:
            category = model.get('category', '').lower()
            found = False
            for cat in filters['categories']:
                if cat.lower() in category:
                    found = True
                    break
            if not found:
                match = False
        
        # 关键词过滤
        if 'keywords' in filters:
            text = f"{model.get('name', '')} {model.get('description', '')}".lower()
            for kw in filters['keywords']:
                if kw.lower() not in text:
                    found = False
                    break
        if match:
            filtered.append(model)
    return filtered

def parse_query(query):
    """解析用户查询，生成过滤条件"""
    query = query.lower()
    filters = {}
    
    # 1. 时间相关解析
    # 近N个月
    match = re.search(r'近(\d+)个月', query)
    if match:
        months = int(match.group(1))
        filters['release_after'] = datetime.now() - timedelta(days=months*30)
    # 近半年
    if '近半年' in query:
        filters['release_after'] = datetime.now() - timedelta(days=180)
    
    # 按年份
    match = re.search(r'(\d{4})年推出', query)
    if match:
        year = int(match.group(1))
        filters['release_after'] = datetime(year, 1, 1)
        filters['release_before'] = datetime(year+1, 1, 1)
    
    # 按时间段
    if '25年下半年' in query:
        filters['release_after'] = datetime(2025, 7, 1)
    if '26年' in query or '2026年' in query:
        filters['release_after'] = datetime(2026, 1, 1)
    
    # 2. 价格相关
    match = re.search(r'输入价格低于(\d+)元', query)
    if match:
        filters['input_price_max'] = int(match.group(1))
    match = re.search(r'输出价格低于(\d+)元', query)
    if match:
        filters['output_price_max'] = int(match.group(1))
    match = re.search(r'价格低于(\d+)元', query)
    if match:
        price = int(match.group(1))
        filters['input_price_max'] = price
        filters['output_price_max'] = price * 5  # 假设输出价格是输入的5倍以内
    
    # 3. 上下文长度
    match = re.search(r'上下文大于(\d+)k', query)
    if match:
        filters['context_min'] = int(match.group(1))
    match = re.search(r'上下文小于(\d+)k', query)
    if match:
        filters['context_max'] = int(match.group(1))
    
    # 4. 标签相关
    tags_map = {
        '图片理解': '图片理解',
        '理解图片': '图片理解',
        '多模态': '多模态',
        '深度思考': '深度思考',
        '工具调用': '工具调用',
        '结构化输出': '结构化输出',
        '长上下文': '长上下文'
    }
    include_tags = []
    for tag_cn, tag_en in tags_map.items():
        if tag_cn in query:
            include_tags.append(tag_en)
    if include_tags:
        filters['include_tags'] = include_tags
    
    # 5. 分类相关
    categories_map = {
        '国产': '国产商用模型',
        '国外': '国外商用模型',
        '多模态': '多模态大模型',
        '文生图': '文生图大模型',
        'embedding': 'Embedding模型',
        'rerank': 'Rerank模型',
        '语音': '语音识别模型',
        '开源': '开源语言模型',
        '本地部署': '本地部署模型'
    }
    categories = []
    for cat_cn, cat_name in categories_map.items():
        if cat_cn in query:
            categories.append(cat_name)
    if categories:
        filters['categories'] = categories
    
    # 6. 查询类型判断
    query_type = 'list'
    if '平均' in query or '统计' in query:
        query_type = 'stat'
    if '推荐' in query:
        query_type = 'recommend'
    
    return filters, query_type

def calculate_statistics(models, query):
    """计算统计数据"""
    if not models:
        return "无匹配模型，无法统计"
    
    result = ""
    if '上下文长度的平均值' in query or '平均上下文' in query:
        contexts = []
        for m in models:
            ctx = parse_context_length(m.get('contextLength', ''))
            if ctx > 0:
                contexts.append(ctx)
        if contexts:
            avg_ctx = sum(contexts) / len(contexts)
            median_ctx = sorted(contexts)[len(contexts)//2]
            result += f"统计结果：\n"
            result += f"- 统计范围：{len(models)}个有效模型\n"
            result += f"- 平均上下文长度：{avg_ctx:.0f}K\n"
            result += f"- 中位数：{median_ctx}K\n"
            result += f"- 最大值：{max(contexts)}K\n"
            result += f"- 最小值：{min(contexts)}K\n"
    
    elif '平均价格' in query or '价格平均值' in query:
        input_prices = []
        output_prices = []
        for m in models:
            inp = parse_price(m.get('inputPrice', ''))
            out = parse_price(m.get('outputPrice', ''))
            if inp > 0:
                input_prices.append(inp)
            if out > 0:
                output_prices.append(out)
        if input_prices and output_prices:
            avg_in = sum(input_prices) / len(input_prices)
            avg_out = sum(output_prices) / len(output_prices)
            result += f"统计结果：\n"
            result += f"- 统计范围：{len(models)}个有效模型\n"
            result += f"- 平均输入价格：{avg_in:.1f} 元/M tokens\n"
            result += f"- 平均输出价格：{avg_out:.1f} 元/M tokens\n"
            # 价格分布
            low = len([p for p in input_prices if p < 5])
            mid = len([p for p in input_prices if 5 <= p < 10])
            high = len([p for p in input_prices if p >= 10])
            result += f"- 输入价格分布：\n"
            result += f"  0-5元：{low}个 ({low/len(input_prices)*100:.1f}%)\n"
            result += f"  5-10元：{mid}个 ({mid/len(input_prices)*100:.1f}%)\n"
            result += f"  10元以上：{high}个 ({high/len(input_prices)*100:.1f}%)\n"
    
    return result

def generate_recommendation(models, limit=DEFAULT_LIMIT):
    """生成推荐列表"""
    if not models:
        return "无符合条件的模型可以推荐"
    
    # 性价比排序：(上下文长度 / 输入价格) 越高越好
    scored = []
    for m in models:
        price = parse_price(m.get('inputPrice', ''))
        ctx = parse_context_length(m.get('contextLength', ''))
        if price > 0 and ctx > 0:
            score = ctx / price
            scored.append((score, m))
    
    # 按得分降序
    scored.sort(reverse=True, key=lambda x: x[0])
    top_models = [m for _, m in scored[:limit]]
    
    result = "推荐模型列表：\n"
    result += "="*60 + "\n"
    for i, m in enumerate(top_models, 1):
        release_time = m.get('releaseTime', '未知')
        ctx = m.get('contextLength', '未知')
        in_price = m.get('inputPrice', '未知').replace('¥', '')
        out_price = m.get('outputPrice', '未知').replace('¥', '')
        tags = "、".join(m.get('tags', []))
        result += f"[{i}] {m.get('name', '')}\n"
        result += f"    {release_time}上架 | {ctx}上下文\n"
        result += f"    {in_price} / {out_price}\n"
        result += f"    {tags}\n"
        result += f"    {m.get('description', '')[:80]}...\n"
        result += "-"*60 + "\n"
    
    return result

def format_model_list(models, limit=DEFAULT_LIMIT):
    """格式化输出模型列表"""
    if not models:
        return "未找到符合条件的模型"
    
    result = f"找到 {len(models)} 个符合条件的模型：\n"
    result += "="*60 + "\n"
    show_count = min(limit, len(models))
    for i, m in enumerate(models[:show_count], 1):
        release_time = m.get('releaseTime', '未知')
        ctx = m.get('contextLength', '未知')
        in_price = m.get('inputPrice', '未知').replace('¥', '')
        tags = "、".join(m.get('tags', []))
        result += f"[{i}] {m.get('name', '')}\n"
        result += f"    {release_time} | {ctx} | {in_price}\n"
        result += f"    {tags}\n"
        result += "-"*60 + "\n"
    
    if len(models) > limit:
        result += f"\n... 还有 {len(models)-limit} 个模型未显示，使用 --limit 参数查看更多\n"
    
    return result

def main():
    parser = argparse.ArgumentParser(description='模型筛选和推荐工具')
    parser.add_argument('query', help='查询语句，如"统计2025年下半年新模型的平均上下文长度"')
    parser.add_argument('--update', action='store_true', help='先更新全量模型数据')
    parser.add_argument('--limit', type=int, default=DEFAULT_LIMIT, help='最多返回的结果数量')
    parser.add_argument('--output', choices=['markdown', 'json'], default='markdown', help='输出格式')
    
    args = parser.parse_args()
    
    # 加载数据
    data, err = load_model_data()
    if err:
        print(f"错误：{err}")
        return
    
    # 获取所有模型
    all_models = get_all_models(data)
    print(f"共加载 {len(all_models)} 个模型")
    
    # 解析查询
    filters, query_type = parse_query(args.query)
    print(f"解析到过滤条件：{filters}")
    print(f"查询类型：{query_type}")
    
    # 筛选模型
    filtered_models = filter_models(all_models, filters)
    print(f"筛选后剩余 {len(filtered_models)} 个模型")
    
    # 根据查询类型处理
    if query_type == 'stat':
        result = calculate_statistics(filtered_models, args.query)
    elif query_type == 'recommend':
        result = generate_recommendation(filtered_models, args.limit)
    else:
        result = format_model_list(filtered_models, args.limit)
    
    # 输出结果
    print("\n" + result)

if __name__ == "__main__":
    main()
