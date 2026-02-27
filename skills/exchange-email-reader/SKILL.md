---
name: exchange-email-reader
description: 读取 Microsoft Exchange/Outlook 邮箱中的最新邮件。使用 exchangelib 库通过 EWS 协议访问企业邮箱，支持读取收件箱、未读邮件、搜索邮件等功能。当用户询问"查看我的邮件"、"读取最新邮件"、"获取邮箱内容"时使用此技能。
---

# Exchange 邮箱读取工具

使用 Python 的 `exchangelib` 库通过 EWS (Exchange Web Services) 协议读取企业 Exchange 邮箱邮件。

## 依赖安装

```bash
pip install exchangelib
```

## 配置信息

邮箱配置（默认已预设）：
- 邮箱服务器：`mail.iwhalecloud.com`
- 邮箱地址：`0027025600@iwhalecloud.com`
- 密码：`Luzh1103!`

## 使用脚本

使用 `scripts/read_emails.py` 脚本读取邮件：

```bash
python scripts/read_emails.py [选项]
```

### 参数

- `--limit N`：读取最近 N 封邮件（默认 10）
- `--unread`：只读取未读邮件
- `--folder FOLDER`：指定文件夹（默认 Inbox，可选：Inbox, SentItems, Drafts, DeletedItems）
- `--search KEYWORD`：搜索包含关键词的邮件

### 示例

```bash
# 读取最近 5 封邮件
python scripts/read_emails.py --limit 5

# 读取未读邮件
python scripts/read_emails.py --unread

# 搜索包含"会议"的邮件
python scripts/read_emails.py --search "会议"

# 读取已发送邮件
python scripts/read_emails.py --folder SentItems --limit 5
```

## 输出格式

脚本输出 JSON 格式的邮件列表：

```json
[
  {
    "subject": "邮件主题",
    "sender": "发件人邮箱",
    "sender_name": "发件人姓名",
    "received": "2026-02-13 14:30:00",
    "is_read": false,
    "body_preview": "邮件正文前 200 字..."
  }
]
```

## 工作流程

1. 用户请求读取邮件时，询问具体需求（最近几封、未读、搜索等）
2. 构建相应的命令行参数
3. 执行 `scripts/read_emails.py` 脚本
4. 解析 JSON 输出并展示给用户

## 故障排除

- **连接失败**：检查网络是否可访问 `mail.iwhalecloud.com`
- **认证失败**：确认用户名密码正确，可能需要使用 `0027025600` 而不是完整邮箱地址
- **SSL 错误**：企业邮箱可能需要特定的 SSL 配置
