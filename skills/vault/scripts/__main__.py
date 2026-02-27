#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vault Skill - OpenClaw 技能入口
支持通过自然语言查询和管理凭据
"""

import sys
import os
import subprocess

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from vault import Vault, print_credential

def handle_query(vault, query: str, simple_mode: bool = True):
    """处理查询请求 - 简化输出，只显示关键信息"""
    query = query.lower().strip()
    
    # 尝试匹配平台名称
    all_creds = vault.list_all()
    
    # 精确匹配 slug
    if query in vault.credentials:
        cred = vault.credentials[query]
        # 简化模式：只显示关键敏感字段（如身份证号）
        if simple_mode or cred.get("category") == "other":
            for field in cred["fields"]:
                # 只显示 id_number 或 password 字段
                if field["key"] in ["id_number", "password", "pin", "kimi_code", "license_key"]:
                    val = field["value"] if not field.get("isSensitive", False) else vault._decrypt_sensitive(field["value"])
                    print(f"{val}")
            return
        else:
            cred_display = vault.get(query, show_sensitive=False)
            print_credential(cred_display)
        return
    
    # 模糊匹配名称
    for cred_info in all_creds:
        if query in cred_info['name'].lower() or query in cred_info['slug'].lower():
            cred = vault.credentials[cred_info['slug']]
            # 简化模式：只显示关键敏感字段
            if simple_mode or cred.get("category") == "other":
                for field in cred["fields"]:
                    if field["key"] in ["id_number", "password", "pin", "kimi_code", "license_key"]:
                        val = field["value"] if not field.get("isSensitive", False) else vault._decrypt_sensitive(field["value"])
                        print(f"{val}")
                return
            else:
                cred_display = vault.get(cred_info['slug'], show_sensitive=False)
                print_credential(cred_display)
            return
    
    print(f"未找到平台：{query}")
    print("\n可用平台:")
    for cred_info in all_creds:
        print(f"  - {cred_info['name']} ({cred_info['slug']})")

def handle_read(vault, query: str):
    """处理明文阅读请求 - 显示完整明文供阅读"""
    query = query.lower().strip()
    
    all_creds = vault.list_all()
    
    # 精确匹配
    if query in vault.credentials:
        cred = vault.credentials[query]
        print(f"\n{cred.get('icon', '🔑')} {cred['name']}")
        if cred.get('relation'):
            print(f"   关系：{cred['relation']}")
        print("\n   完整信息:")
        for field in cred["fields"]:
            val = vault._decrypt_sensitive(field["value"]) if field["isSensitive"] and field["value"] else field["value"]
            if val:
                print(f"     - {field['label']}: {val}")
        print()
        return
    
    # 模糊匹配
    for cred_info in all_creds:
        if query in cred_info['name'].lower() or query in cred_info['slug'].lower():
            cred = vault.credentials[cred_info['slug']]
            print(f"\n{cred.get('icon', '🔑')} {cred['name']}")
            if cred.get('relation'):
                print(f"   关系：{cred['relation']}")
            print("\n   完整信息:")
            for field in cred["fields"]:
                val = vault._decrypt_sensitive(field["value"]) if field["isSensitive"] and field["value"] else field["value"]
                if val:
                    print(f"     - {field['label']}: {val}")
            print()
            return
    
    print(f"未找到：{query}")

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

def copy_to_clipboard(text: str) -> bool:
    """复制到剪贴板"""
    try:
        # Windows: 使用 clip 命令
        if sys.platform == 'win32':
            subprocess.run(['clip'], input=text.encode('utf-8'), check=True)
            print("✅ 已复制到剪贴板！")
            return True
        # macOS: 使用 pbcopy
        elif sys.platform == 'darwin':
            subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            print("✅ 已复制到剪贴板！")
            return True
        # Linux: 使用 xclip 或 wl-clipboard
        else:
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
                print("✅ 已复制到剪贴板！")
                return True
            except FileNotFoundError:
                subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True)
                print("✅ 已复制到剪贴板！")
                return True
    except Exception as e:
        print(f"❌ 复制失败：{e}")
        return False

def handle_copy(vault, query: str, channel: str = "webchat"):
    """处理复制请求 - 显示明文和可点击格式，不自动复制"""
    query = query.lower().strip()
    
    # 飞书渠道：不提供复制功能
    if channel == "feishu":
        print("📌 飞书渠道不支持剪贴板操作，请使用以下命令查看明文：")
        print(f"   `vault read {query}`")
        print("\n然后手动复制需要的内容。")
        return False
    
    # 精确匹配 slug
    if query in vault.credentials:
        cred = vault.credentials[query]
        # 优先显示 id_number，其次显示其他敏感字段
        primary_field = None
        primary_label = ""
        backup_field = None
        backup_label = ""
        
        for field in cred["fields"]:
            is_sensitive = field.get("isSensitive", False) or cred.get("category") == "other"
            if is_sensitive and field["value"]:
                val = vault._decrypt_sensitive(field["value"]) if field.get("isSensitive", False) else field["value"]
                # 优先保留 id_number
                if field["key"] == "id_number":
                    primary_field = val
                    primary_label = field["label"]
                    break
                elif field["key"] in ["password", "pin", "kimi_code", "license_key"]:
                    if not primary_field:
                        primary_field = val
                        primary_label = field["label"]
                else:
                    backup_field = val
                    backup_label = field["label"]
        
        # 如果没有 id_number，使用备份字段
        if not primary_field and backup_field:
            primary_field = backup_field
            primary_label = backup_label
        
        if primary_field:
            # 显示可点击格式
            print(f"📋 **{cred['name']} - {primary_label}**")
            print(f"\n```\n{primary_field}\n```")
            print(f"\n点击代码块即可复制，或手动 `Ctrl+C` 复制。")
            return True
        else:
            print(f"❌ 没有找到可复制的信息")
            return False
    
    # 模糊匹配
    all_creds = vault.list_all()
    for cred_info in all_creds:
        if query in cred_info['name'].lower() or query in cred_info['slug'].lower():
            cred = vault.credentials[cred_info['slug']]
            primary_field = None
            primary_label = ""
            backup_field = None
            backup_label = ""
            
            for field in cred["fields"]:
                is_sensitive = field.get("isSensitive", False) or cred.get("category") == "other"
                if is_sensitive and field["value"]:
                    val = vault._decrypt_sensitive(field["value"]) if field.get("isSensitive", False) else field["value"]
                    if field["key"] == "id_number":
                        primary_field = val
                        primary_label = field["label"]
                        break
                    elif field["key"] in ["password", "pin", "kimi_code", "license_key"]:
                        if not primary_field:
                            primary_field = val
                            primary_label = field["label"]
                    else:
                        backup_field = val
                        backup_label = field["label"]
            
            if not primary_field and backup_field:
                primary_field = backup_field
                primary_label = backup_label
            
            if primary_field:
                print(f"📋 **{cred['name']} - {primary_label}**")
                print(f"\n```\n{primary_field}\n```")
                print(f"\n点击代码块即可复制，或手动 `Ctrl+C` 复制。")
                return True
            else:
                print(f"❌ 没有找到可复制的信息")
                return False
    
    print(f"未找到平台：{query}")
    return False

def main():
    """主函数"""
    vault = Vault()
    
    if len(sys.argv) < 2:
        print("Vault - 密码箱技能")
        print("\n用法:")
        print("  vault query <平台名>     - 查询凭据（简化输出）")
        print("  vault read <平台名>      - 查看明文（供阅读）")
        print("  vault copy <平台名>      - 显示可复制格式")
        print("  vault list               - 列出所有平台")
        print("  vault save <平台> <k>=<v> - 保存凭据")
        return
    
    command = sys.argv[1]
    
    if command == "query":
        if len(sys.argv) < 3:
            print("用法：vault query <平台名>")
            return
        query = " ".join(sys.argv[2:])
        handle_query(vault, query, simple_mode=True)
    
    elif command == "read":
        if len(sys.argv) < 3:
            print("用法：vault read <平台名>")
            return
        query = " ".join(sys.argv[2:])
        handle_read(vault, query)
    
    elif command == "copy":
        if len(sys.argv) < 3:
            print("用法：vault copy <平台名>")
            return
        query = " ".join(sys.argv[2:])
        # 检测渠道
        channel = os.getenv("OPENCLAW_CHANNEL", "webchat")
        handle_copy(vault, query, channel)
    
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
