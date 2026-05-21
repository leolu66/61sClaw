#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 GitHub token 存储格式 - 将明文重新加密
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from vault import Vault, VaultCrypto, CREDENTIALS_FILE, MASTER_PASSWORD

def fix_github_token():
    """修复 GitHub token 加密存储"""
    
    # 读取当前数据
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    github_cred = data['credentials']['github']
    fields = github_cred['fields']
    
    # 找到 token 字段
    token_field = None
    for field in fields:
        if field['key'] == 'token':
            token_field = field
            break
    
    if not token_field:
        print("[ERROR] 未找到 token 字段")
        return False
    
    current_value = token_field['value']
    
    # 检查是否已经是密文（密文通常包含 / + = 等字符，且长度较长）
    if len(current_value) > 50 and ('/' in current_value or '+' in current_value):
        print("[INFO] Token 看起来已经是密文格式")
        return True
    
    print(f"[INFO] 当前 token: {current_value[:20]}...")
    print("[INFO] 正在加密存储...")
    
    # 加密 token
    crypto = VaultCrypto(MASTER_PASSWORD)
    encrypted_token = crypto.encrypt(current_value)
    
    print(f"[INFO] 加密后: {encrypted_token[:30]}...")
    
    # 更新字段
    token_field['value'] = encrypted_token
    
    # 保存
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("[OK] GitHub token 已加密存储")
    return True

if __name__ == '__main__':
    fix_github_token()
