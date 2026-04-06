#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path

# 配置
DATA_FILE = Path(__file__).parent.parent / "output" / "models_data_full.json"
DB_FILE = Path(__file__).parent.parent / "output" / "models.db"

def parse_price(price_str):
    """解析价格字符串，返回数字"""
    if not price_str or price_str == "":
        return 0.0
    match = re.search(r'([\d.]+)', price_str)
    if match:
        return float(match.group(1))
    return 0.0

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

def init_db():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 创建分类表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        expected_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建模型表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        model_name TEXT,
        model_code TEXT,
        model_id TEXT,
        description TEXT,
        input_price REAL DEFAULT 0,
        output_price REAL DEFAULT 0,
        cache_price REAL DEFAULT 0,
        context_length INTEGER DEFAULT 0,
        max_output INTEGER DEFAULT 0,
        release_date TEXT,
        billing_type TEXT,
        support_function_call BOOLEAN DEFAULT 0,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_release_date ON models (release_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_input_price ON models (input_price)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_context_length ON models (context_length)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_category_id ON models (category_id)')
    
    conn.commit()
    return conn

def import_data():
    """导入JSON数据到SQLite"""
    # 读取JSON数据
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = init_db()
    cursor = conn.cursor()
    
    # 清空旧数据
    cursor.execute('DELETE FROM models')
    cursor.execute('DELETE FROM categories')
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="categories" OR name="models"')
    
    category_id_map = {}
    
    # 导入分类和模型
    for category in data:
        cat_name = category['name']
        expected_count = category.get('expected_count', 0)
        
        # 插入分类
        cursor.execute('INSERT INTO categories (name, expected_count) VALUES (?, ?)', 
                      (cat_name, expected_count))
        category_id = cursor.lastrowid
        category_id_map[cat_name] = category_id
        
        # 导入分类下的模型
        if 'models' in category:
            for model in category['models']:
                import_model(cursor, category_id, model)
        
        # 导入子分类
        if 'subGroups' in category:
            for sub in category['subGroups']:
                sub_name = f"{cat_name}/{sub['name']}"
                sub_expected_count = sub.get('expected_count', 0)
                cursor.execute('INSERT INTO categories (name, expected_count) VALUES (?, ?)', 
                              (sub_name, sub_expected_count))
                sub_category_id = cursor.lastrowid
                category_id_map[sub_name] = sub_category_id
                
                if 'models' in sub:
                    for model in sub['models']:
                        import_model(cursor, sub_category_id, model)
    
    conn.commit()
    conn.close()
    
    # 统计导入结果
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM categories')
    cat_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM models')
    model_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"数据导入完成！")
    print(f"   分类数量：{cat_count}")
    print(f"   模型数量：{model_count}")
    print(f"   数据库文件：{DB_FILE}")

def import_model(cursor, category_id, model):
    """导入单个模型"""
    name = model.get('name', '')
    model_name = model.get('modelName', '')
    model_code = model.get('modelCode', '')
    model_id = model.get('modelId', '')
    description = model.get('description', '')
    
    input_price = parse_price(model.get('inputPrice', ''))
    output_price = parse_price(model.get('outputPrice', ''))
    cache_price = parse_price(model.get('cachePrice', ''))
    
    context_length = parse_context_length(model.get('contextLength', ''))
    max_output = parse_context_length(model.get('maxOutput', ''))
    
    release_date = model.get('releaseTime', '')
    billing_type = model.get('billingType', '')
    support_function_call = 1 if model.get('supportFunctionCall', False) else 0
    
    tags = ','.join(model.get('tags', []))
    
    cursor.execute('''
    INSERT INTO models (
        category_id, name, model_name, model_code, model_id, description,
        input_price, output_price, cache_price, context_length, max_output,
        release_date, billing_type, support_function_call, tags
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        category_id, name, model_name, model_code, model_id, description,
        input_price, output_price, cache_price, context_length, max_output,
        release_date, billing_type, support_function_call, tags
    ))

if __name__ == "__main__":
    import_data()
