#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 配置
DB_FILE = Path(__file__).parent.parent / "output" / "models.db"
JSON_DATA_FILE = Path(__file__).parent.parent / "output" / "models_data_full.json"
DEFAULT_LIMIT = 10

def check_db_exists():
    """检查数据库是否存在"""
    return DB_FILE.exists()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def parse_query(query):
    """解析用户查询，生成SQL查询条件和参数"""
    query = query.lower()
    conditions = []
    params = []
    query_type = 'list'
    
    # 1. 时间相关解析
    # 近N个月
    match = re.search(r'近(\d+)个月', query)
    if match:
        months = int(match.group(1))
        date_after = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        conditions.append("release_date >= ?")
        params.append(date_after)
    # 近半年
    if '近半年' in query:
        date_after = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        conditions.append("release_date >= ?")
        params.append(date_after)
    # 按年份
    match = re.search(r'(\d{4})年推出', query)
    if match:
        year = int(match.group(1))
        conditions.append("release_date >= ? AND release_date < ?")
        params.append(f"{year}-01-01")
        params.append(f"{year+1}-01-01")
    # 25年下半年
    if '25年下半年' in query:
        conditions.append("release_date >= ?")
        params.append("2025-07-01")
    # 26年
    if '26年' in query or '2026年' in query:
        conditions.append("release_date >= ?")
        params.append("2026-01-01")
    
    # 2. 价格相关
    match = re.search(r'输入价格低于(\d+)元', query)
    if match:
        conditions.append("input_price <= ?")
        params.append(int(match.group(1)))
    match = re.search(r'输出价格低于(\d+)元', query)
    if match:
        conditions.append("output_price <= ?")
        params.append(int(match.group(1)))
    match = re.search(r'价格低于(\d+)元', query)
    if match:
        price = int(match.group(1))
        conditions.append("input_price <= ? AND output_price <= ?")
        params.append(price)
        params.append(price * 5)
    
    # 3. 上下文长度
    match = re.search(r'上下文大于(\d+)k', query)
    if match:
        conditions.append("context_length >= ?")
        params.append(int(match.group(1)))
    match = re.search(r'上下文小于(\d+)k', query)
    if match:
        conditions.append("context_length <= ?")
        params.append(int(match.group(1)))
    
    # 4. 标签相关
    if '图片理解' in query or '理解图片' in query:
        conditions.append("tags LIKE ?")
        params.append('%图片理解%')
    if '深度思考' in query:
        conditions.append("tags LIKE ?")
        params.append('%深度思考%')
    if '工具调用' in query:
        conditions.append("tags LIKE ?")
        params.append('%工具调用%')
    if '结构化输出' in query:
        conditions.append("tags LIKE ?")
        params.append('%结构化输出%')
    if '长上下文' in query:
        conditions.append("tags LIKE ?")
        params.append('%长上下文%')
    if '多模态' in query:
        conditions.append("tags LIKE ?")
        params.append('%多模态%')
    
    # 5. 分类相关
    if '国产' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%国产%')
    if '国外' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%国外%')
    if '多模态模型' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%多模态%')
    if '文生图' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%文生图%')
    if 'embedding' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%Embedding%')
    if 'rerank' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%Rerank%')
    if '语音' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%语音%')
    if '开源' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%开源%')
    if '本地部署' in query:
        conditions.append("categories.name LIKE ?")
        params.append('%本地部署%')
    
    # 6. 查询类型判断
    if '平均' in query or '统计' in query:
        query_type = 'stat'
    if '推荐' in query:
        query_type = 'recommend'
    
    # 构建SQL
    base_sql = """
    SELECT models.*, categories.name as category_name 
    FROM models 
    LEFT JOIN categories ON models.category_id = categories.id
    """
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        sql = base_sql + where_clause
    else:
        sql = base_sql
    
    return sql, params, query_type

def execute_query(sql, params):
    """执行SQL查询"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def calculate_statistics(models, query):
    """计算统计数据"""
    if not models:
        return "无匹配模型，无法统计"
    
    result = ""
    if '上下文长度的平均值' in query or '平均上下文' in query:
        contexts = [m['context_length'] for m in models if m['context_length'] > 0]
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
        input_prices = [m['input_price'] for m in models if m['input_price'] > 0]
        output_prices = [m['output_price'] for m in models if m['output_price'] > 0]
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
        price = m['input_price']
        ctx = m['context_length']
        if price > 0 and ctx > 0:
            score = ctx / price
            scored.append((score, m))
    
    # 按得分降序
    scored.sort(reverse=True, key=lambda x: x[0])
    top_models = [m for _, m in scored[:limit]]
    
    result = "推荐模型列表：\n"
    result += "="*60 + "\n"
    for i, m in enumerate(top_models, 1):
        release_time = m['release_date'] if m['release_date'] else '未知'
        ctx = f"{m['context_length']}K" if m['context_length'] > 0 else '未知'
        in_price = f"{m['input_price']} 元/M tokens" if m['input_price'] > 0 else '未知'
        out_price = f"{m['output_price']} 元/M tokens" if m['output_price'] > 0 else '未知'
        tags = m['tags'].replace(',', '、') if m['tags'] else '无'
        result += f"[{i}] {m['name']}\n"
        result += f"    {release_time}上架 | {ctx}上下文\n"
        result += f"    {in_price} / {out_price}\n"
        result += f"    {tags}\n"
        result += f"    {m['description'][:80]}...\n"
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
        release_time = m['release_date'] if m['release_date'] else '未知'
        ctx = f"{m['context_length']}K" if m['context_length'] > 0 else '未知'
        in_price = f"{m['input_price']} 元/M tokens" if m['input_price'] > 0 else '未知'
        tags = m['tags'].replace(',', '、') if m['tags'] else '无'
        result += f"[{i}] {m['name']}\n"
        result += f"    {release_time} | {ctx} | {in_price}\n"
        result += f"    {tags}\n"
        result += "-"*60 + "\n"
    
    if len(models) > limit:
        result += f"\n... 还有 {len(models)-limit} 个模型未显示，使用 --limit 参数查看更多\n"
    
    return result

def main():
    parser = argparse.ArgumentParser(description='模型筛选和推荐工具（SQLite版本）')
    parser.add_argument('query', help='查询语句，如"统计2025年下半年新模型的平均上下文长度"')
    parser.add_argument('--update', action='store_true', help='先更新全量模型数据并重新导入数据库')
    parser.add_argument('--limit', type=int, default=DEFAULT_LIMIT, help='最多返回的结果数量')
    parser.add_argument('--output', choices=['markdown', 'json'], default='markdown', help='输出格式')
    
    args = parser.parse_args()
    
    # 检查数据库
    if not check_db_exists():
        print("数据库不存在，正在导入数据...")
        import import_to_sqlite
        import_to_sqlite.import_data()
    
    # 解析查询
    sql, params, query_type = parse_query(args.query)
    print(f"生成SQL：{sql}")
    print(f"查询参数：{params}")
    print(f"查询类型：{query_type}")
    
    # 执行查询
    models = execute_query(sql, params)
    print(f"查询到 {len(models)} 个匹配模型")
    
    # 根据查询类型处理
    if query_type == 'stat':
        result = calculate_statistics(models, args.query)
    elif query_type == 'recommend':
        result = generate_recommendation(models, args.limit)
    else:
        result = format_model_list(models, args.limit)
    
    # 输出结果
    print("\n" + result)

if __name__ == "__main__":
    main()
