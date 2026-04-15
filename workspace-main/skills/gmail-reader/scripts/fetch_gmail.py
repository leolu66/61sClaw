#!/usr/bin/env python3
"""
Gmail IMAP Reader
读取 Gmail 邮件并输出 JSON 格式
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def decode_str(s):
    """解码邮件头中的编码字符串"""
    if not s:
        return ""
    decoded_parts = decode_header(s)
    result = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result += part.decode(charset or 'utf-8', errors='replace')
            except:
                result += part.decode('utf-8', errors='replace')
        else:
            result += part
    return result


def get_email_body(msg):
    """提取邮件正文"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # 跳过附件
            if "attachment" in content_disposition:
                continue
            
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                except:
                    pass
            elif content_type == "text/html" and not body:
                try:
                    html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    # 简单清理 HTML 标签
                    body = re.sub(r'<[^>]+>', ' ', html)
                    body = re.sub(r'\s+', ' ', body).strip()
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except:
            body = str(msg.get_payload())
    
    return body[:5000]  # 限制长度


def fetch_emails(limit=10, unread_only=False, search_query=None, email_id=None):
    """从 Gmail 获取邮件"""
    
    # 获取环境变量
    gmail_email = os.getenv('GMAIL_EMAIL')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_email or not gmail_password:
        print(json.dumps({
            "error": "Missing credentials",
            "message": "Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables"
        }, ensure_ascii=False))
        sys.exit(1)
    
    try:
        import imaplib
    except ImportError:
        print(json.dumps({
            "error": "Missing module",
            "message": "imaplib is required. Run: pip install imaplib"
        }, ensure_ascii=False))
        sys.exit(1)
    
    try:
        # 连接 Gmail IMAP 服务器
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(gmail_email, gmail_password)
        
        # 选择收件箱
        mail.select('inbox')
        
        emails = []
        
        if email_id:
            # 获取指定邮件
            status, msg_data = mail.fetch(email_id.encode(), '(RFC822)')
            if status == 'OK':
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = message_from_bytes(response_part[1])
                        emails.append(parse_email(msg, email_id))
        else:
            # 构建搜索条件
            search_criteria = 'ALL'
            if unread_only:
                search_criteria = 'UNSEEN'
            if search_query:
                # 简单的搜索支持
                search_criteria = f'(OR SUBJECT "{search_query}" FROM "{search_query}")'
            
            # 搜索邮件
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                print(json.dumps({
                    "error": "Search failed",
                    "message": "Could not search emails"
                }, ensure_ascii=False))
                return []
            
            # 获取邮件 ID 列表
            email_ids = messages[0].split()
            
            # 限制数量（最新的在前）
            email_ids = email_ids[-limit:]
            email_ids.reverse()
            
            # 获取每封邮件
            for eid in email_ids:
                status, msg_data = mail.fetch(eid, '(RFC822)')
                if status == 'OK':
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = message_from_bytes(response_part[1])
                            emails.append(parse_email(msg, eid.decode()))
        
        mail.close()
        mail.logout()
        
        return emails
        
    except imaplib.IMAP4.error as e:
        print(json.dumps({
            "error": "IMAP error",
            "message": str(e),
            "hint": "Check if IMAP is enabled in Gmail settings and app password is correct"
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "error": "Unexpected error",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


def parse_email(msg, email_id):
    """解析邮件内容"""
    subject = decode_str(msg.get('Subject', ''))
    from_addr = decode_str(msg.get('From', ''))
    date_str = msg.get('Date', '')
    
    # 解析日期
    try:
        # 尝试解析常见日期格式
        date_match = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})', date_str)
        if date_match:
            day, month_str, year, hour, minute, second = date_match.groups()
            months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                     'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
            date_obj = datetime(int(year), months[month_str], int(day), int(hour), int(minute), int(second))
            date_formatted = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_formatted = date_str
    except:
        date_formatted = date_str
    
    # 获取正文
    body = get_email_body(msg)
    
    # 检查是否已读（通过 FLAGS）
    is_read = '\\Seen' in str(msg.get('Flags', ''))
    
    return {
        "id": email_id,
        "subject": subject or "(无主题)",
        "from": from_addr,
        "date": date_formatted,
        "body": body,
        "is_read": is_read
    }


def main():
    parser = argparse.ArgumentParser(description='Gmail IMAP Reader')
    parser.add_argument('--limit', type=int, default=10, help='Number of emails to fetch (default: 10)')
    parser.add_argument('--unread', action='store_true', help='Fetch only unread emails')
    parser.add_argument('--search', type=str, help='Search query for emails')
    parser.add_argument('--id', type=str, help='Fetch specific email by ID')
    
    args = parser.parse_args()
    
    emails = fetch_emails(
        limit=args.limit,
        unread_only=args.unread,
        search_query=args.search,
        email_id=args.id
    )
    
    # 输出 JSON
    print(json.dumps(emails, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
