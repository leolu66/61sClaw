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

## 飞书渠道配置

### 已配置的飞书应用

| 应用 | appId | 用途 |
|------|-------|------|
| default | cli_a915882c43b8dccb | 主应用（默认） |
| openclawd | cli_a900853b21385cb5 | feishu-agent 绑定 |

### 有效的发送目标

| 类型 | ID | 说明 | 状态 |
|------|-----|------|------|
| 用户私聊 | `ou_1ff98dde85af548188b059cfcb464208` | 六一（oc_xbot 私聊） | ✅ 有效 |
| 群聊 | `oc_8faba0172387fceedf00c927e00ccfef` | 工作群 | ✅ 有效 |
| ~~用户~~ | ~~`ou_6296b58fee28100a7b01c0b8d0fb631f`~~ | ~~（旧ID）~~ | ❌ cross app 错误 |

### 发送命令示例

```bash
# 发送到私聊（六一）
openclaw message send --channel feishu --account default \
  --message "通知内容" \
  --target "user:ou_1ff98dde85af548188b059cfcb464208"

# 发送到群聊
openclaw message send --channel feishu --account default \
  --message "通知内容" \
  --target "chat:oc_8faba0172387fceedf00c927e00ccfef"
```

> **注意**：`--account` 参数指定使用哪个飞书应用，默认是 `default`

---

## 触发指令

### 快速指令格式
- `/小飞 xxx` → 将 xxx 发送到飞书（发送给默认用户）

> 默认用户 ID: `ou_1ff98dde85af548188b059cfcb464208`（六一 - oc_xbot 私聊）
> 默认群聊 ID: `oc_8faba0172387fceedf00c927e00ccfef`

### 代码调用格式

#### 前置条件

1. 飞书机器人已配置（在 openclaw.json 中配置）
2. 拥有 `im:message:send_as_bot` 权限

#### 使用方法

使用 `openclaw message send` CLI 命令发送通知：

```bash
# 发送到用户（oc_xbot 私聊）
openclaw message send --channel feishu --message "通知内容" --target "user:ou_1ff98dde85af548188b059cfcb464208"

# 发送到群聊
openclaw message send --channel feishu --message "通知内容" --target "chat:oc_8faba0172387fceedf00c927e00ccfef"
```

> 注意：此方式为纯通知推送，不会触发 AI 回复

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
