#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exchange 邮箱邮件读取脚本
使用 exchangelib 库通过 EWS 协议读取邮件
"""

import argparse
import json
import sys
import io
from datetime import datetime, timedelta
from exchangelib import Credentials, Account, Configuration, DELEGATE, Message
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import subprocess

# 邮箱配置（优先从环境变量读取，否则从 vault 获取）
EMAIL = os.environ.get("XTC_EXCHANGE_EMAIL", "0027025600@iwhalecloud.com")
USERNAME = os.environ.get("XTC_EXCHANGE_USERNAME", "0027025600")
PASSWORD = os.environ.get("XTC_EXCHANGE_PASSWORD", "")
SERVER = os.environ.get("XTC_EXCHANGE_SERVER", "mail.iwhalecloud.com")

# 如果环境变量没有密码，尝试从 vault 获取
if not PASSWORD:
    try:
        result = subprocess.run(
            ["python", os.path.join(os.path.dirname(__file__), "..", "..", "vault", "scripts", "__main__.py"), "query", "email"],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8'
        )
        if result.returncode == 0 and result.stdout.strip():
            PASSWORD = result.stdout.strip()
    except Exception as e:
        print(f"从 vault 获取密码失败: {e}", file=sys.stderr)

if not PASSWORD:
    raise ValueError('请设置环境变量 XTC_EXCHANGE_PASSWORD 或在 vault 中保存邮箱密码')

def get_account():
    """建立 Exchange 连接"""
    try:
        # 禁用 SSL 验证（某些企业环境需要）
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        credentials = Credentials(username=USERNAME, password=PASSWORD)

        # 尝试自动发现
        try:
            account = Account(
                primary_smtp_address=EMAIL,
                credentials=credentials,
                autodiscover=True,
                access_type=DELEGATE
            )
            return account
        except Exception as e:
            print(f"自动发现失败，尝试手动配置: {e}", file=sys.stderr)

        # 手动配置 EWS 端点
        config = Configuration(
            server=SERVER,
            credentials=credentials
        )

        account = Account(
            primary_smtp_address=EMAIL,
            config=config,
            access_type=DELEGATE
        )
        return account

    except Exception as e:
        print(f"连接邮箱失败: {e}", file=sys.stderr)
        sys.exit(1)

def get_folder(account, folder_name):
    """获取指定文件夹"""
    folder_map = {
        'inbox': account.inbox,
        'sentitems': account.sent,
        'drafts': account.drafts,
        'deleteditems': account.trash,
    }

    folder_lower = folder_name.lower()
    if folder_lower in folder_map:
        return folder_map[folder_lower]

    # 尝试遍历所有文件夹查找
    for folder in account.root.walk():
        if folder.name.lower() == folder_lower:
            return folder

    return account.inbox  # 默认返回收件箱

def safe_str(text, max_length=None):
    """安全处理字符串编码"""
    if text is None:
        return ""
    # 保留所有字符，只移除控制字符（除了换行符）
    result = ''.join(char for char in str(text) if ord(char) >= 32 or char in ['\n', '\r', '\t'])
    if max_length and len(result) > max_length:
        result = result[:max_length] + "..."
    return result

def read_emails(limit=10, unread_only=False, folder_name='inbox', search_keyword=None, full_body=False):
    """读取邮件列表
    Args:
        limit: 最大返回邮件数量
        unread_only: 是否只返回未读邮件
        folder_name: 文件夹名称
        search_keyword: 搜索关键词
        full_body: 是否返回完整正文（默认False只返回200字符预览）
    
    注意：当 unread_only=True 且未读数量为0时，也会返回最近7封邮件
    """
    account = get_account()
    folder = get_folder(account, folder_name)

    # 先获取所有邮件（用于判断未读数量）
    all_items = folder.all().order_by('-datetime_received')
    
    # 获取未读邮件
    unread_items = folder.filter(is_read=False).order_by('-datetime_received')
    unread_count = unread_items.count()
    
    if unread_only:
        # 如果有未读邮件，返回未读的
        if unread_count > 0:
            items = unread_items[:limit]
        else:
            # 未读为0时，返回最近7封
            items = all_items[:7]
    else:
        # 非未读模式，返回最近的
        items = all_items[:limit]

    # 搜索关键词
    if search_keyword:
        items = items.filter(subject__contains=search_keyword)

    emails = []
    for item in items:
        if isinstance(item, Message):
            # 获取正文
            body = item.text_body or item.body or ""
            if full_body:
                body_content = safe_str(body)
            else:
                body_content = safe_str(body, max_length=200) if body else "(无内容)"

            email_data = {
                "subject": safe_str(item.subject) or "(无主题)",
                "sender": safe_str(item.sender.email_address) if item.sender else "Unknown",
                "sender_name": safe_str(item.sender.name) if item.sender else "Unknown",
                "received": item.datetime_received.strftime("%Y-%m-%d %H:%M:%S") if item.datetime_received else "Unknown",
                "is_read": item.is_read,
                "body": body_content,
                "body_preview": safe_str(body, max_length=200) if body and not full_body else "(无内容)"
            }
            emails.append(email_data)

    return emails

def main():
    parser = argparse.ArgumentParser(description='读取 Exchange 邮箱邮件')
    parser.add_argument('--limit', type=int, default=10, help='读取邮件数量（默认 10）')
    parser.add_argument('--unread', action='store_true', help='只读取未读邮件')
    parser.add_argument('--folder', type=str, default='inbox', help='邮件文件夹（默认 inbox）')
    parser.add_argument('--search', type=str, help='搜索关键词')
    parser.add_argument('--full', action='store_true', help='返回完整邮件正文（默认只返回预览）')

    args = parser.parse_args()

    try:
        emails = read_emails(
            limit=args.limit,
            unread_only=args.unread,
            folder_name=args.folder,
            search_keyword=args.search,
            full_body=args.full
        )
        print(json.dumps(emails, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"读取邮件失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
