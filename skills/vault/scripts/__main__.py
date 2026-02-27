#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vault Skill - OpenClaw 技能入口
支持通过自然语言查询和管理凭据
"""

import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from vault import Vault, print_credential

def handle_query(vault, query: str):
    """处理查询请求"""
    query = query.lower().strip()
    
    # 尝试匹配平台名称
    all_creds = vault.list_all()
    
    # 精确匹配 slug
    if query in vault.credentials:
        cred = vault.get(query, show_sensitive=False)
        print_credential(cred)
        return
    
    # 模糊匹配名称
    for cred_info in all_creds:
        if query in cred_info['name'].lower() or query in cred_info['slug'].lower():
            cred = vault.get(cred_info['slug'], show_sensitive=False)
            print_credential(cred)
            return
    
    print(f"未找到平台：{query}")
    print("\n可用平台:")
    for cred_info in all_creds:
        print(f"  - {cred_info['name']} ({cred_info['slug']})")

def handle_list(vault):
    """处理列表请求"""
    items = vault.list_all()
    if not items:
        print("暂无保存的凭据")
        return
    
    current_category = ""
    for item in items:
        if item["category"] != current_category:
            current_category = item["category"]
            print(f"\n📁 {current_category.upper()}")
            print("-" * 40)
        print(f"  {item['icon']} {item['name']} ({item['slug']})")

def main():
    """主函数"""
    vault = Vault()
    
    if len(sys.argv) < 2:
        print("Vault - 密码箱技能")
        print("\n用法:")
        print("  vault query <平台名>     - 查询凭据")
        print("  vault list               - 列出所有平台")
        print("  vault save <平台> <k>=<v> - 保存凭据")
        print("  vault show-secret <平台>  - 显示敏感信息")
        return
    
    command = sys.argv[1]
    
    if command == "query":
        if len(sys.argv) < 3:
            print("用法：vault query <平台名>")
            return
        query = " ".join(sys.argv[2:])
        handle_query(vault, query)
    
    elif command == "list":
        handle_list(vault)
    
    elif command == "save":
        if len(sys.argv) < 4:
            print("用法：vault save <平台> <key>=<value> [key=value ...]")
            return
        slug = sys.argv[2]
        fields = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                fields[key.strip()] = value.strip()
        
        if slug in vault.credentials:
            vault.update(slug, fields)
        else:
            vault.add(slug, fields)
    
    elif command == "show-secret":
        if len(sys.argv) < 3:
            print("用法：vault show-secret <平台名>")
            return
        slug = sys.argv[2]
        cred = vault.get(slug, show_sensitive=True)
        print_credential(cred)
    
    else:
        print(f"未知命令：{command}")

if __name__ == "__main__":
    # 设置 UTF-8 编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
