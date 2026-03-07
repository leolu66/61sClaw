---
name: skill-pusher
description: 将指定技能推送到目标 Agent，支持飞书Agent和通用Agent
---

# skill-pusher

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "推送技能"
- "skill pusher"
- "技能推送到"

### 功能描述
将指定技能从当前 workspace 推送到目标 Agent 的 workspace，支持自动发送通知消息。

### 输入/输出
- **输入**: 
  - skill_name: 要推送的技能名称
  - target: 目标 Agent (feishu-agent / general-agent)
- **输出**: 
  - 技能复制到目标 workspace/skills/
  - 返回技能信息（用于发送通知）

### 依赖条件
- Python 3.7+
- shutil 模块（标准库）
- 目标 Agent workspace 存在

### 边界情况
- 技能不存在时提示错误
- 目标 workspace 不存在时提示错误
- 目标 workspace 已存在同名技能时覆盖
- Claude Code 推送预留入口（暂不实现）

---

## 使用方法

### 基本用法

```bash
# 推送到飞书Agent
python scripts/push_skill.py holiday-checker feishu-agent

# 推送到通用Agent
python scripts/push_skill.py timer-alarm general-agent
```

### 参数说明

| 参数 | 说明 | 可选值 |
|------|------|--------|
| skill_name | 要推送的技能名称 | .openclaw/skills/ 下的目录名 |
| target | 目标 Agent | feishu-agent, general-agent |

### 源技能目录

技能源目录位于: `C:\Users\luzhe\.openclaw\skills\`

### 目标 Agent 映射

| Agent 名称 | Workspace 路径 |
|------------|----------------|
| feishu-agent | C:\Users\luzhe\.openclaw\workspace-feishu-agent |
| general-agent | C:\Users\luzhe\.openclaw\workspace-main |

---

## 推送流程

1. **检查源技能** - 验证技能目录是否存在
2. **检查目标 workspace** - 验证目标 Agent workspace 是否存在
3. **复制技能** - 将技能目录复制到目标 workspace/skills/
4. **发送通知** - 使用 message 工具通知目标 Agent（需主 Agent 执行）

---

## Claude Code 预留

Claude Code 推送功能预留入口，暂不实现：

```python
if target == 'claude-code':
    print("Claude Code 推送功能开发中...")
    return
```

---

## 相关文件

- `scripts/push_skill.py` - 主推送脚本

---

## 注意事项

- 推送后会覆盖目标 workspace 中同名的技能
- 通知消息需要主 Agent 使用 message 工具发送
- 推送前请确保目标 workspace 存在

---

## DoD 检查表

**开发日期**: 2026-03-07
**开发者**: 小天才

### 1. SRS 文档
- [x] 触发条件明确
- [x] 功能描述完整
- [x] 输入输出说明
- [x] 依赖条件列出
- [x] 边界情况处理

### 2. 技能文件和代码
- [x] 目录结构规范
- [x] 使用相对路径
- [x] 配置外置（如需要）
- [x] 无 .skill 文件

### 3. 测试通过
- [x] 功能测试通过（推送到 general-agent）
- [x] 触发测试通过
- [x] 边界测试通过

### 4. GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露
- [x] 推送到 master 和 main

**状态**: ✅ 完成
