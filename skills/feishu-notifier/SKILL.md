---
name: feishu-notifier
description: |
  飞书消息推送工具 - 主动向用户发送通知消息。
  支持向飞书用户或群聊发送文本消息、卡片消息等。
  当需要主动通知用户（如任务完成、提醒、告警等）时使用此技能。
  支持 `/小飞 xxx` 指令格式快速发送消息到飞书。
---

# 飞书通知器

向飞书用户或群聊主动发送通知消息。

## 触发指令

### 快速指令格式
- `/小飞 xxx` → 将 xxx 发送到飞书（发送给默认用户）

> 默认用户 ID: `ou_6296b58fee28100a7b01c0b8d0fb631f`（六一）

### 代码调用格式

#### 前置条件

1. 飞书机器人已配置（在 openclaw.json 中配置）
2. 拥有 `im:message:send_as_bot` 权限

#### 使用方法

### 发送文本消息

```python
from message import message

# 发送到用户（需要用户的 open_id）
message(
    action="send",
    channel="feishu",
    message="通知内容",
    target="user:ou_xxxxx"  # 用户 open_id
)

# 发送到群聊
message(
    action="send",
    channel="feishu",
    message="通知内容",
    target="chat:oc_xxxxx"  # 群聊 ID
)
```

### 获取用户 ID

用户在飞书中向机器人发送消息时，对话的 `sender_id` 就是用户的 open_id。

格式：`ou_xxxxxxxxxxxxxxxxxxxxxxxx`

## 触发示例

- "发送通知给六一"
- "推送消息：任务已完成"
- "提醒用户 xxx"

## 适用场景

- 定时任务完成通知
- 重要邮件提醒
- API 余额告警
- 工作流程提醒
