#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vault - 密码箱技能
安全存储和查询各平台的账号、密码、API Key 等敏感信息
"""

import json
import os
import sys
import hashlib
import base64
import uuid
import subprocess
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 设置 UTF-8 编码（注释掉，避免关闭文件的问题）
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 平台别名映射（用户常用名 -> 实际 slug）
PLATFORM_ALIASES = {
    'gmail': 'google',
    'gmail 密码': 'google',
    'google 密码': 'google',
    '微软密码': 'microsoft',
    'ms': 'microsoft',
    'microsoft 密码': 'microsoft',
}

# 配置
VAULT_DIR = Path.home() / ".openclaw" / "vault"
CREDENTIALS_FILE = VAULT_DIR / "credentials.json"

# 从 Windows 凭据管理器读取主密码
def get_master_password():
    """从 Windows 凭据管理器读取主密码"""
    try:
        import win32cred
        cred = win32cred.CredRead(
            TargetName="OpenClawVaultMasterPassword",
            Type=win32cred.CRED_TYPE_GENERIC
        )
        # CredentialBlob 是 UTF-16 编码的字节串
        password = cred.get('CredentialBlob', b'').decode('utf-16-le').rstrip('\x00')
        if password:
            return password
    except Exception as e:
        pass
    
    # 降级方案：尝试环境变量
    env_password = os.getenv("VAULT_MASTER_PASSWORD")
    if env_password:
        return env_password
    
    # 最后降级：硬编码（不推荐）
    return "768211"

MASTER_PASSWORD = get_master_password()

# 尝试导入加密库
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("警告：cryptography 库未安装，将使用 base64 编码代替加密")
    print("安装方法：pip install cryptography")

# 预设平台模板
PLATFORM_TEMPLATES = {
    "zhipu": {
        "name": "智谱 AI",
        "category": "llm",
        "icon": "🤖",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "category": "llm",
        "icon": "🌙",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "volcengine": {
        "name": "火山引擎",
        "category": "cloud",
        "icon": "🌋",
        "fields": [
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": False},
            {"key": "password", "label": "登录密码", "type": "password", "isSensitive": True, "isRequired": False},
            {"key": "app_key", "label": "App Key", "type": "token", "isSensitive": True, "isRequired": False},
            {"key": "access_key_id", "label": "Access Key ID", "type": "token", "isSensitive": True, "isRequired": False},
            {"key": "secret_access_key", "label": "Secret Access Key", "type": "token", "isSensitive": True, "isRequired": False},
            {"key": "account_id", "label": "主账号 ID", "type": "text", "isSensitive": False, "isRequired": False}
        ]
    },
    "whalecloud": {
        "name": "WhaleCloud Lab",
        "category": "llm",
        "icon": "🐋",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "aliyun": {
        "name": "阿里云",
        "category": "cloud",
        "icon": "☁️",
        "fields": [
            {"key": "access_key_id", "label": "Access Key ID", "type": "token", "isSensitive": True, "isRequired": True},
            {"key": "access_key_secret", "label": "Access Key Secret", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "feishu": {
        "name": "飞书",
        "category": "api",
        "icon": "📱",
        "fields": [
            {"key": "app_id", "label": "App ID", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "app_secret", "label": "App Secret", "type": "token", "isSensitive": True, "isRequired": True},
            {"key": "bot_token", "label": "Bot Token", "type": "token", "isSensitive": True, "isRequired": False}
        ]
    },
    "github": {
        "name": "GitHub",
        "category": "code",
        "icon": "🐙",
        "fields": [
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "token", "label": "Personal Access Token", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "qiniu": {
        "name": "七牛云",
        "category": "cloud",
        "icon": "📦",
        "fields": [
            {"key": "access_key", "label": "Access Key", "type": "token", "isSensitive": True, "isRequired": True},
            {"key": "secret_key", "label": "Secret Key", "type": "token", "isSensitive": True, "isRequired": True},
            {"key": "bucket", "label": "存储空间", "type": "text", "isSensitive": False, "isRequired": False}
        ]
    },
    "brave": {
        "name": "Brave Search",
        "category": "api",
        "icon": "🔍",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "qweather": {
        "name": "和风天气",
        "category": "api",
        "icon": "🌤️",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "email": {
        "name": "公司邮箱",
        "category": "email",
        "icon": "📧",
        "fields": [
            {"key": "email", "label": "邮箱地址", "type": "email", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "邮箱密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "smtp_server", "label": "SMTP 服务器", "type": "text", "isSensitive": False, "isRequired": False},
            {"key": "imap_server", "label": "IMAP 服务器", "type": "text", "isSensitive": False, "isRequired": False}
        ]
    },
    "ngrok": {
        "name": "ngrok",
        "category": "cloud",
        "icon": "🔗",
        "fields": [
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "authtoken", "label": "Auth Token", "type": "token", "isSensitive": True, "isRequired": False}
        ]
    },
    "jianguoyun": {
        "name": "坚果云",
        "category": "cloud",
        "icon": "☁️",
        "fields": [
            {"key": "email", "label": "邮箱", "type": "email", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "app_password", "label": "应用密码", "type": "token", "isSensitive": True, "isRequired": False}
        ]
    },
    "cursor": {
        "name": "Cursor",
        "category": "code",
        "icon": "💻",
        "fields": [
            {"key": "email", "label": "邮箱", "type": "email", "isSensitive": False, "isRequired": True},
            {"key": "license_key", "label": "License Key", "type": "token", "isSensitive": True, "isRequired": True}
        ]
    },
    "gitee": {
        "name": "Gitee",
        "category": "code",
        "icon": "🐵",
        "fields": [
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "token", "label": "Private Token", "type": "token", "isSensitive": True, "isRequired": False}
        ]
    },
    "dockerhub": {
        "name": "Docker Hub",
        "category": "code",
        "icon": "🐳",
        "fields": [
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "access_token", "label": "Access Token", "type": "token", "isSensitive": True, "isRequired": False}
        ]
    },
    "cutecloud": {
        "name": "CuteCloud",
        "category": "cloud",
        "icon": "🌸",
        "fields": [
            {"key": "email", "label": "邮箱", "type": "email", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "url", "label": "控制台地址", "type": "url", "isSensitive": False, "isRequired": False}
        ]
    },
    "115": {
        "name": "115 网站",
        "category": "cloud",
        "icon": "📁",
        "fields": [
            {"key": "phone", "label": "手机号", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True}
        ]
    },
    "ollama": {
        "name": "Ollama",
        "category": "llm",
        "icon": "🦙",
        "fields": [
            {"key": "email", "label": "邮箱", "type": "email", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True}
        ]
    },
    "personal": {
        "name": "个人信息",
        "category": "other",
        "icon": "👤",
        "fields": [
            {"key": "name", "label": "姓名", "type": "text", "isSensitive": True, "isRequired": True},
            {"key": "id_number", "label": "身份证号", "type": "text", "isSensitive": True, "isRequired": True},
            {"key": "phone", "label": "手机号", "type": "text", "isSensitive": True, "isRequired": False},
            {"key": "relation", "label": "关系", "type": "text", "isSensitive": False, "isRequired": False}
        ]
    },
    "yinxiang": {
        "name": "印象笔记",
        "category": "api",
        "icon": "🐘",
        "fields": [
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True}
        ]
    },
    "appleid": {
        "name": "Apple ID",
        "category": "other",
        "icon": "🍎",
        "fields": [
            {"key": "email", "label": "Apple ID", "type": "email", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True}
        ]
    },
    "device": {
        "name": "设备密码",
        "category": "other",
        "icon": "📱",
        "fields": [
            {"key": "device_name", "label": "设备名称", "type": "text", "isSensitive": False, "isRequired": True},
            {"key": "password", "label": "锁屏密码", "type": "password", "isSensitive": True, "isRequired": True},
            {"key": "pin", "label": "PIN 码", "type": "password", "isSensitive": True, "isRequired": False},
            {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": False},
            {"key": "device_type", "label": "设备类型", "type": "text", "isSensitive": False, "isRequired": False}
        ]
    }
}


class VaultCrypto:
    """加密工具类"""
    
    def __init__(self, password: str):
        self.password = password
        self.salt = b"vault_salt_2026"  # 固定盐值（生产环境应该随机生成并保存）
        
    def _derive_key(self) -> bytes:
        """从主密码派生 256 位密钥"""
        key = hashlib.pbkdf2_hmac(
            'sha256',
            self.password.encode('utf-8'),
            self.salt,
            100000  # 迭代次数
        )
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """加密字符串"""
        if not CRYPTO_AVAILABLE:
            # 降级方案：base64 编码
            return base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')
        
        try:
            key = self._derive_key()
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)  # 96-bit nonce
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
            # 组合 nonce + ciphertext 并 base64 编码
            encrypted = base64.b64encode(nonce + ciphertext).decode('utf-8')
            return encrypted
        except Exception as e:
            print(f"加密失败：{e}")
            return base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """解密字符串"""
        if not CRYPTO_AVAILABLE:
            # 降级方案：base64 解码
            try:
                return base64.b64decode(ciphertext.encode('utf-8')).decode('utf-8')
            except:
                return ciphertext
        
        try:
            key = self._derive_key()
            data = base64.b64decode(ciphertext.encode('utf-8'))
            nonce = data[:12]
            actual_ciphertext = data[12:]
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, actual_ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"解密失败：{e}")
            # 尝试 base64 解码（兼容旧数据）
            try:
                return base64.b64decode(ciphertext.encode('utf-8')).decode('utf-8')
            except:
                return ciphertext


class Vault:
    """密码箱主类"""
    
    def __init__(self):
        self.crypto = VaultCrypto(MASTER_PASSWORD)
        self.credentials: Dict[str, Any] = {}
        self._ensure_dir()
        self._load()
    
    def _ensure_dir(self):
        """确保目录存在"""
        VAULT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load(self):
        """加载凭据文件"""
        if CREDENTIALS_FILE.exists():
            try:
                with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.credentials = data.get('credentials', {})
            except Exception as e:
                print(f"加载凭据文件失败：{e}")
                self.credentials = {}
        else:
            self.credentials = {}
            self._save()
    
    def _save(self):
        """保存凭据文件"""
        data = {
            "version": "1.0",
            "createdAt": datetime.now().isoformat(),
            "credentials": self.credentials
        }
        with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _encrypt_sensitive(self, value: str) -> str:
        """加密敏感字段"""
        if not value:
            return value
        return self.crypto.encrypt(value)
    
    def _decrypt_sensitive(self, value: str) -> str:
        """解密敏感字段"""
        if not value:
            return value
        return self.crypto.decrypt(value)
    
    def add(self, slug: str, fields: Dict[str, str], name: Optional[str] = None, 
            category: Optional[str] = None, icon: Optional[str] = None, 
            tags: Optional[List[str]] = None, notes: Optional[str] = None) -> bool:
        """添加凭据"""
        if slug in self.credentials:
            print(f"凭据 '{slug}' 已存在，使用 update 更新")
            return self.update(slug, fields)
        
        # 获取模板
        template = PLATFORM_TEMPLATES.get(slug, {})
        
        credential = {
            "id": str(uuid.uuid4()),
            "slug": slug,
            "name": name or template.get("name", slug),
            "category": category or template.get("category", "other"),
            "icon": icon or template.get("icon", "🔑"),
            "fields": [],
            "tags": tags or [],
            "notes": notes,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        # 处理字段
        template_fields = template.get("fields", [])
        for key, value in fields.items():
            # 查找字段模板
            field_template = next((f for f in template_fields if f["key"] == key), None)
            if field_template:
                field = {
                    "key": key,
                    "label": field_template.get("label", key),
                    "type": field_template.get("type", "text"),
                    "isSensitive": field_template.get("isSensitive", False),
                    "isRequired": field_template.get("isRequired", False),
                    "value": self._encrypt_sensitive(value) if field_template.get("isSensitive", False) else value
                }
            else:
                # 未知字段，默认不敏感
                field = {
                    "key": key,
                    "label": key.replace("_", " ").title(),
                    "type": "text",
                    "isSensitive": False,
                    "isRequired": False,
                    "value": value
                }
            credential["fields"].append(field)
        
        self.credentials[slug] = credential
        self._save()
        print(f"[OK] 已保存凭据：{credential['name']}")
        return True
    
    def get(self, slug: str, show_sensitive: bool = False) -> Optional[Dict]:
        """查询凭据"""
        if slug not in self.credentials:
            print(f"[ERROR] 未找到凭据：{slug}")
            return None
        
        cred = self.credentials[slug]
        result = {
            "name": cred["name"],
            "category": cred["category"],
            "icon": cred["icon"],
            "tags": cred["tags"],
            "notes": cred["notes"],
            "fields": {}
        }
        
        for field in cred["fields"]:
            if field["isSensitive"] and not show_sensitive:
                # 隐藏敏感信息
                value = "********" if field["value"] else "(空)"
            elif field["isSensitive"]:
                value = self._decrypt_sensitive(field["value"])
            else:
                value = field["value"]
            result["fields"][field["label"]] = value
        
        return result
    
    def list_all(self) -> List[Dict]:
        """列出所有平台"""
        result = []
        for slug, cred in self.credentials.items():
            result.append({
                "slug": slug,
                "name": cred["name"],
                "category": cred["category"],
                "icon": cred["icon"],
                "tags": cred["tags"],
                "createdAt": cred["createdAt"]
            })
        return sorted(result, key=lambda x: x["category"] + x["name"])
    
    def update(self, slug: str, fields: Dict[str, str]) -> bool:
        """更新凭据"""
        if slug not in self.credentials:
            print(f"[ERROR] 未找到凭据：{slug}")
            return False
        
        cred = self.credentials[slug]
        template = PLATFORM_TEMPLATES.get(slug, {})
        template_fields = template.get("fields", [])
        
        updated = False
        for key, value in fields.items():
            # 查找现有字段
            existing_field = next((f for f in cred["fields"] if f["key"] == key), None)
            if existing_field:
                # 更新现有字段
                if existing_field["isSensitive"]:
                    existing_field["value"] = self._encrypt_sensitive(value)
                else:
                    existing_field["value"] = value
                updated = True
            else:
                # 添加新字段
                field_template = next((f for f in template_fields if f["key"] == key), None)
                if field_template:
                    field = {
                        "key": key,
                        "label": field_template.get("label", key),
                        "type": field_template.get("type", "text"),
                        "isSensitive": field_template.get("isSensitive", False),
                        "isRequired": field_template.get("isRequired", False),
                        "value": self._encrypt_sensitive(value) if field_template.get("isSensitive", False) else value
                    }
                else:
                    field = {
                        "key": key,
                        "label": key.replace("_", " ").title(),
                        "type": "text",
                        "isSensitive": False,
                        "isRequired": False,
                        "value": value
                    }
                cred["fields"].append(field)
                updated = True
        
        if updated:
            cred["updatedAt"] = datetime.now().isoformat()
            self._save()
            print(f"✅ 已更新凭据：{cred['name']}")
        
        return updated
    
    def delete(self, slug: str) -> bool:
        """删除凭据"""
        if slug not in self.credentials:
            print(f"[ERROR] 未找到凭据：{slug}")
            return False
        
        name = self.credentials[slug]["name"]
        del self.credentials[slug]
        self._save()
        print(f"[OK] 已删除凭据：{name}")
        return True


def print_credential(cred: Optional[Dict]):
    """格式化输出凭据"""
    if not cred:
        return
    
    print(f"\n[INFO] {cred['name']} ({cred['category']})")
    if cred['tags']:
        print(f"   标签：{', '.join(cred['tags'])}")
    if cred['notes']:
        print(f"   备注：{cred['notes']}")
    print("\n   字段:")
    for label, value in cred['fields'].items():
        print(f"     - {label}: {value}")
    print()


def main():
    """主函数 - 支持命令行调用"""
    vault = Vault()
    
    if len(sys.argv) < 2:
        print("用法：vault <command> [args]")
        print("命令:")
        print("  list                  - 列出所有平台")
        print("  get <slug>            - 查询凭据")
        print("  get-secret <slug>     - 查询凭据（显示敏感信息）")
        print("  add <slug>            - 添加凭据（交互模式）")
        print("  update <slug> <k>=<v> - 更新凭据")
        print("  delete <slug>         - 删除凭据")
        print("  init                  - 初始化所有预设平台模板")
        return
    
    command = sys.argv[1]
    
    if command == "list":
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
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("用法：vault get <slug>")
            return
        slug = sys.argv[2]
        cred = vault.get(slug, show_sensitive=False)
        print_credential(cred)
    
    elif command == "get-secret":
        if len(sys.argv) < 3:
            print("用法：vault get-secret <slug>")
            return
        
        # 处理别名
        raw_slug = sys.argv[2]
        slug = PLATFORM_ALIASES.get(raw_slug.lower(), raw_slug)
        
        # 直接读取原始数据，匹配 key 而不是 label
        from vault import CREDENTIALS_FILE
        if CREDENTIALS_FILE.exists():
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cred = data.get('credentials', {}).get(slug)
            if cred:
                password_fields = ['password', 'pwd', 'passwd', 'pass', 'pw', 'token', 'secret', 'key']
                password_value = None
                
                for field in cred.get('fields', []):
                    field_key = field.get('key', '').lower()
                    is_sensitive = field.get('isSensitive', False)
                    value = field.get('value', '')
                    
                    # 如果是敏感字段且需要解密
                    if is_sensitive and value:
                        value = vault._decrypt_sensitive(value)
                    
                    for pw_keyword in password_fields:
                        if pw_keyword in field_key:
                            password_value = value
                            break
                    if password_value:
                        break
                
                if password_value:
                    print(password_value)
                else:
                    # 没有密码字段，输出所有字段值
                    for field in cred.get('fields', []):
                        print(field.get('value', ''))
            else:
                print(f"[ERROR] 未找到凭据：{slug}")
        else:
            print("[ERROR] 凭据文件不存在")
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("用法：vault add <slug>")
            return
        slug = sys.argv[2]
        
        # 获取模板
        template = PLATFORM_TEMPLATES.get(slug)
        if not template:
            print(f"未知平台：{slug}")
            print("可用平台:", ", ".join(PLATFORM_TEMPLATES.keys()))
            return
        
        print(f"\n添加凭据：{template['name']}")
        fields = {}
        for field in template["fields"]:
            if field["isRequired"]:
                value = input(f"输入 {field['label']}: ").strip()
                fields[field["key"]] = value
        
        vault.add(slug, fields)
    
    elif command == "update":
        if len(sys.argv) < 4:
            print("用法：vault update <slug> <key>=<value> [key=value ...]")
            return
        slug = sys.argv[2]
        fields = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                fields[key.strip()] = value.strip()
        vault.update(slug, fields)
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("用法：vault delete <slug>")
            return
        slug = sys.argv[2]
        vault.delete(slug)
    
    elif command == "init":
        print("初始化所有预设平台模板...")
        for slug in PLATFORM_TEMPLATES.keys():
            if slug not in vault.credentials:
                vault.credentials[slug] = {
                    "id": str(uuid.uuid4()),
                    "slug": slug,
                    "name": PLATFORM_TEMPLATES[slug]["name"],
                    "category": PLATFORM_TEMPLATES[slug]["category"],
                    "icon": PLATFORM_TEMPLATES[slug]["icon"],
                    "fields": [],
                    "tags": [],
                    "notes": "",
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat()
                }
        vault._save()
        print(f"[OK] 已初始化 {len(PLATFORM_TEMPLATES)} 个平台模板")
    
    else:
        print(f"未知命令：{command}")


if __name__ == "__main__":
    # 设置控制台编码为 UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
