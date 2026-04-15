---
name: gmail-reader
description: 读取 Gmail 邮箱中的邮件。使用 IMAP 协议访问 Gmail，支持读取收件箱、未读邮件、搜索邮件等功能。当用户询问"查看 Gmail 邮件"、"读取 Gmail 最新邮件"、"获取 Gmail 邮箱内容"、"Gmail 未读邮件"时使用此技能。
---

# Gmail Reader

使用 IMAP 协议读取 Gmail 邮件，无需复杂的 OAuth 流程。

## 前置要求

1. **启用 Gmail IMAP 访问**
   - 登录 Gmail → 设置 → 转发和 POP/IMAP → IMAP 访问 → 启用 IMAP

2. **生成应用专用密码**（如果使用两步验证）
   - Google 账号 → 安全性 → 两步验证 → 应用专用密码
   - 选择"邮件" → 设备选择"其他" → 生成密码
   - **保存这个 16 位密码**

3. **配置环境变量**
   ```bash
   set GMAIL_EMAIL=your.email@gmail.com
   set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

## 使用方法

```bash
# 读取最新 10 封邮件
python "C:\Users\luzhe\.openclaw\workspace-main\skills\gmail-reader\scripts\fetch_gmail.py" --limit 10

# 只读取未读邮件
python "C:\Users\luzhe\.openclaw\workspace-main\skills\gmail-reader\scripts\fetch_gmail.py" --unread --limit 5

# 搜索邮件
python "C:\Users\luzhe\.openclaw\workspace-main\skills\gmail-reader\scripts\fetch_gmail.py" --search "from:boss@company.com"

# 查看邮件详情（指定邮件 ID）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\gmail-reader\scripts\fetch_gmail.py" --id 12345
```

## 输出格式

脚本输出 JSON 格式，包含以下字段：

```json
[
  {
    "id": "12345",
    "subject": "邮件主题",
    "from": "发件人 <sender@example.com>",
    "date": "2024-01-15 09:30:00",
    "body": "邮件正文内容...",
    "is_read": false
  }
]
```

## 文件路径规范

- 脚本位置: `skills/gmail-reader/scripts/fetch_gmail.py`
- 使用相对路径解析到 workspace 根目录
