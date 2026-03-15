#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMAP 邮箱读取器
支持多账户配置、最新邮件获取和关键词搜索
"""

import argparse
import imaplib
import json
import os
import re
import sys
import io
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path

# 设置标准输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def decode_str(s):
    """解码邮件头中的编码字符串"""
    if s is None:
        return ""
    decoded_parts = decode_header(s)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or 'utf-8', errors='ignore'))
            except:
                result.append(part.decode('utf-8', errors='ignore'))
        else:
            result.append(part)
    return ''.join(result)


def get_email_body(msg):
    """获取邮件正文（用于搜索）"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
        except:
            pass
    return body


def format_date(date_str):
    """格式化日期字符串"""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def truncate_string(s, max_length=50):
    """截断字符串，超过长度显示省略号"""
    s = s.replace('\n', ' ').replace('\r', ' ')
    if len(s) > max_length:
        return s[:max_length-3] + "..."
    return s


def load_config():
    """加载配置文件"""
    # 配置文件在脚本上级目录
    config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        print("请配置 config.json 文件并设置您的邮箱账户")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        sys.exit(1)


def get_account_config(config, account_name=None):
    """获取账户配置"""
    accounts = config.get('accounts', [])
    if not accounts:
        print("❌ 配置文件中没有账户信息")
        sys.exit(1)
    
    if account_name:
        for acc in accounts:
            if acc.get('name') == account_name:
                return acc
        print(f"❌ 未找到账户: {account_name}")
        print(f"可用账户: {', '.join([acc.get('name', '未命名') for acc in accounts])}")
        sys.exit(1)
    
    return accounts[0]


def connect_imap(account):
    """连接 IMAP 服务器"""
    imap_server = account.get('imap_server')
    imap_port = account.get('imap_port', 993)
    use_ssl = account.get('ssl', True)
    email_addr = account.get('email')
    env_key = account.get('env_key')
    
    # 从环境变量获取授权码
    auth_code = os.environ.get(env_key)
    if not auth_code:
        print(f"❌ 未设置环境变量: {env_key}")
        print(f"请在 PowerShell 中运行: $env:{env_key} = 'your_auth_code'")
        sys.exit(1)
    
    try:
        if use_ssl:
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        else:
            mail = imaplib.IMAP4(imap_server, imap_port)
        
        mail.login(email_addr, auth_code)
        return mail
    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP 登录失败: {e}")
        print("请检查:")
        print("  1. 邮箱地址是否正确")
        print("  2. 授权码是否正确（不是登录密码）")
        print("  3. IMAP 服务是否已开启")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 连接邮箱服务器失败: {e}")
        sys.exit(1)


def search_emails(mail, keyword=None):
    """搜索邮件"""
    mail.select('inbox')
    
    if keyword:
        # 搜索主题或发件人包含关键词
        # IMAP 搜索语法: OR (FROM "keyword") (SUBJECT "keyword")
        _, search_data = mail.search(None, f'(OR (FROM "{keyword}") (SUBJECT "{keyword}"))')
    else:
        # 获取所有邮件
        _, search_data = mail.search(None, 'ALL')
    
    email_ids = search_data[0].split()
    return email_ids


def fetch_emails(mail, email_ids, limit=10):
    """获取邮件详情"""
    emails = []
    
    # 获取最新的 limit 封邮件
    email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
    
    for email_id in reversed(email_ids):  # 最新的在前
        try:
            _, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)
            
            # 解析邮件信息
            subject = decode_str(msg.get('Subject', ''))
            from_addr = decode_str(msg.get('From', ''))
            date_str = msg.get('Date', '')
            
            # 提取发件人名称和邮箱
            from_match = re.match(r'"?([^"<>]+)"?\s*<?([^<>]*)>?', from_addr)
            if from_match:
                from_name = from_match.group(1).strip()
                from_email = from_match.group(2).strip()
                if from_name and from_email:
                    from_display = f"{from_name} <{from_email}>"
                elif from_name:
                    from_display = from_name
                else:
                    from_display = from_email
            else:
                from_display = from_addr
            
            emails.append({
                'subject': subject or '(无主题)',
                'from': from_display,
                'date': format_date(date_str)
            })
        except Exception as e:
            print(f"⚠️  解析邮件 {email_id.decode()} 失败: {e}")
            continue
    
    return emails


def print_emails(emails, account_name):
    """打印邮件列表"""
    if not emails:
        print("📭 没有找到邮件")
        return
    
    print(f"\n📧 {account_name} - 共 {len(emails)} 封邮件\n")
    
    # 计算列宽
    from_width = max(len(truncate_string(e['from'], 30)) for e in emails)
    from_width = max(from_width, 10)
    
    subject_width = max(len(truncate_string(e['subject'], 40)) for e in emails)
    subject_width = max(subject_width, 10)
    
    date_width = 16
    
    # 打印表头
    header = f"{'发件人':<{from_width}} | {'主题':<{subject_width}} | {'日期':<{date_width}}"
    print(header)
    print("-" * len(header))
    
    # 打印邮件列表
    for email in emails:
        from_str = truncate_string(email['from'], from_width)
        subject_str = truncate_string(email['subject'], subject_width)
        date_str = email['date']
        print(f"{from_str:<{from_width}} | {subject_str:<{subject_width}} | {date_str:<{date_width}}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description='IMAP 邮箱读取器')
    parser.add_argument('--account', '-a', help='指定账户名称')
    parser.add_argument('--limit', '-l', type=int, default=10, help='读取最新 N 封邮件（默认 10）')
    parser.add_argument('--search', '-s', help='搜索关键词')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 获取账户配置
    account = get_account_config(config, args.account)
    account_name = account.get('name', '未命名账户')
    
    print(f"🔌 正在连接 {account_name}...")
    
    # 连接邮箱
    mail = connect_imap(account)
    
    try:
        # 搜索邮件
        if args.search:
            print(f"🔍 搜索关键词: {args.search}")
        
        email_ids = search_emails(mail, args.search)
        
        if not email_ids:
            if args.search:
                print(f"📭 未找到包含 '{args.search}' 的邮件")
            else:
                print("📭 邮箱中没有邮件")
            return
        
        # 获取邮件详情
        print(f"📨 找到 {len(email_ids)} 封邮件，获取最新 {args.limit} 封...")
        emails = fetch_emails(mail, email_ids, args.limit)
        
        # 打印邮件列表
        print_emails(emails, account_name)
        
    finally:
        mail.close()
        mail.logout()


if __name__ == '__main__':
    main()
