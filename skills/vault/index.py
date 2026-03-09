#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vault Skill Handler - 密码箱技能处理入口
处理用户查询密码、token等请求
"""

import sys
import os
import re
import io

# 设置 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加脚本目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from vault import Vault

def handle_query(query: str) -> str:
    """
    处理用户查询请求
    
    Args:
        query: 用户输入，如 "查github的token"
    
    Returns:
        查询结果或错误信息
    """
    query = query.lower().strip()
    
    # 匹配 "查xxx的yyy" 或 "查看xxx的yyy" 或 "xxx的yyy"
    patterns = [
        r'查[看询]?\s*(\w+)\s*的\s*(\w+)',
        r'(\w+)\s*的\s*(\w+)',
        r'查[看询]?\s*(\w+)',
    ]
    
    platform = None
    field = None
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                platform = groups[0]
                field = groups[1]
            else:
                platform = groups[0]
            break
    
    if not platform:
        return "[ERROR] 无法识别查询请求"
    
    # 平台别名映射
    aliases = {
        'github': 'github',
        'git': 'github',
        'gh': 'github',
        'kimi': 'moonshot',
        '智谱': 'zhipu',
        '智谱ai': 'zhipu',
        '飞书': 'feishu',
        '阿里云': 'aliyun',
        '阿里': 'aliyun',
        '火山': 'volcengine',
        '七牛': 'qiniu',
    }
    
    platform = aliases.get(platform, platform)
    
    # 初始化 vault
    vault = Vault()
    
    # 查询凭据（敏感信息解密显示）
    cred = vault.get(platform, show_sensitive=True)
    if not cred:
        return f"[ERROR] 未找到平台 '{platform}' 的凭据"
    
    fields = cred.get('fields', {})
    
    # 如果指定了字段，返回该字段值
    if field:
        # 字段别名映射
        field_map = {
            'token': ['token', 'private_token', 'access_token'],
            'password': ['password', 'pwd'],
            'username': ['username', 'user'],
            'key': ['api_key', 'key', 'secret_key'],
        }
        
        target_keys = field_map.get(field.lower(), [field])
        
        # 查找匹配的字段（不区分大小写）
        for fk, fv in fields.items():
            if fk.lower() in [k.lower() for k in target_keys]:
                return fv
        
        return f"[ERROR] 未找到字段 '{field}'"
    
    # 没有指定字段，返回所有信息
    result = [f"{cred['name']}"]
    for fk, fv in fields.items():
        result.append(f"  {fk}: {fv}")
    
    return '\n'.join(result)

def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("用法: python index.py '查github的token'")
        return
    
    query = ' '.join(sys.argv[1:])
    result = handle_query(query)
    print(result)

if __name__ == '__main__':
    main()
