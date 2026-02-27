#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 credentials.json 中的明文密码问题
自动识别 password/token/secret 等字段并重新加密
"""

import json
import hashlib
import base64
import os
import sys
import io
from pathlib import Path
from datetime import datetime

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 配置
VAULT_DIR = Path.home() / ".openclaw" / "vault"
CREDENTIALS_FILE = VAULT_DIR / "credentials.json"

# 主密码
MASTER_PASSWORD = "768211"

# 敏感字段关键词（包含这些词的就认为是敏感字段）
SENSITIVE_KEYWORDS = [
    'password', 'pwd', 'passwd', 'pass',
    'token', 'secret', 'key', 'apikey', 'api_key',
    'credential', 'auth', 'license'
]

# 敏感字段类型
SENSITIVE_TYPES = ['password', 'token', 'secret']


class SimpleCrypto:
    """简单加密工具（复制自 vault.py）"""
    
    def __init__(self, password: str):
        self.password = password
        self.salt = b"vault_salt_2026"
        
    def _derive_key(self) -> bytes:
        key = hashlib.pbkdf2_hmac(
            'sha256',
            self.password.encode('utf-8'),
            self.salt,
            100000
        )
        return key
    
    def encrypt(self, plaintext: str) -> str:
        # 简化版：使用 base64+hash（实际应该用 AES-GCM）
        # 这里为了兼容 vault.py 的降级方案
        key = self._derive_key()
        # 简单 XOR 加密 + base64（仅用于演示，实际应该用 cryptography 库）
        import hashlib
        seed = int(hashlib.sha256(key).hexdigest()[:16], 16)
        
        encrypted_chars = []
        for i, char in enumerate(plaintext):
            encrypted_char = chr(ord(char) ^ ((seed >> (i % 32)) & 0xFF))
            encrypted_chars.append(encrypted_char)
        
        encrypted = ''.join(encrypted_chars)
        return base64.b64encode(encrypted.encode('latin-1')).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        # 尝试解密，如果失败就返回原文
        try:
            # 这里简化处理，实际应该实现完整的 XOR 解密
            return ciphertext  # 暂时返回原文
        except:
            return ciphertext


def is_sensitive_field(key: str, field_type: str) -> bool:
    """判断字段是否应该标记为敏感"""
    key_lower = key.lower()
    
    # 检查是否包含敏感关键词
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in key_lower:
            return True
    
    # 检查字段类型
    if field_type in SENSITIVE_TYPES:
        return True
    
    return False


def fix_credentials():
    """修复 credentials.json"""
    if not CREDENTIALS_FILE.exists():
        print(f"❌ 文件不存在：{CREDENTIALS_FILE}")
        return
    
    # 备份原文件
    backup_file = CREDENTIALS_FILE.with_suffix('.json.bak')
    import shutil
    shutil.copy2(CREDENTIALS_FILE, backup_file)
    print(f"[OK] 已备份原文件：{backup_file}")
    
    # 读取数据
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    credentials = data.get('credentials', {})
    crypto = SimpleCrypto(MASTER_PASSWORD)
    
    fixed_count = 0
    total_sensitive = 0
    
    for slug, cred in credentials.items():
        fields = cred.get('fields', [])
        
        for field in fields:
            key = field.get('key', '')
            field_type = field.get('type', 'text')
            is_sensitive = field.get('isSensitive', False)
            value = field.get('value', '')
            
            # 判断是否应该是敏感字段
            should_be_sensitive = is_sensitive_field(key, field_type)
            
            if should_be_sensitive:
                total_sensitive += 1
                
                # 如果当前不是敏感字段，需要修复
                if not is_sensitive:
                    print(f"[FIX] 修复：{slug}.{key} - 标记为敏感并加密")
                    
                    # 加密值（如果当前是明文）
                    if value and not value.startswith('eyJ') and len(value) < 100:
                        # 看起来是明文，加密它
                        encrypted_value = crypto.encrypt(value)
                        field['value'] = encrypted_value
                        print(f"   [OK] 已加密：{key} = {value[:3]}... -> {encrypted_value[:20]}...")
                    
                    # 更新字段属性
                    field['isSensitive'] = True
                    field['type'] = 'password' if 'password' in key.lower() else 'token'
                    
                    fixed_count += 1
    
    # 保存修复后的数据
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 修复完成！")
    print(f"   - 共发现敏感字段：{total_sensitive} 个")
    print(f"   - 已修复：{fixed_count} 个")
    print(f"   - 备份文件：{backup_file}")


if __name__ == "__main__":
    fix_credentials()
