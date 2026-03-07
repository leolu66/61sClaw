# Learnings

Self-improvement log for tracking corrections, knowledge gaps, and best practices.

## Format

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description

### Details
Full context

### Suggested Action
Specific fix

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file
- Tags: tag1, tag2
- See Also: LRN-...

---
```

## Entries

## [LRN-20260308-001] best_practice

**Logged**: 2026-03-08T00:26:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
Windows 控制台编码问题：使用 --raw 参数获取 JSON 避免乱码

### Details
执行 weather-skill 查询天气时，Python 脚本输出显示为乱码（如"[����] ����Ԥ��"）。
这是由于 Windows 控制台默认使用 GBK 编码，而 Python 脚本输出 UTF-8 导致的。

解决方案：使用 `--raw` 参数获取原始 JSON 数据，然后由调用方解析和格式化输出。

### Suggested Action
1. 对于可能遇到编码问题的脚本，优先使用 JSON/原始数据模式
2. 在 OpenClaw 中解析 JSON 并格式化输出，避免依赖脚本的标准输出

### Metadata
- Source: error
- Related Files: skills/weather-skill/scripts/weather.py
- Tags: encoding, windows, utf-8, json
- See Also: 

---

## [LRN-20260308-002] knowledge_gap

**Logged**: 2026-03-08T00:32:00+08:00
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
Self-Improvement 技能是被动技能，无自动触发词，需手动记录或配置 hooks 自动检测

### Details
**误解：** 以为 self-improving-agent 技能像其他技能一样有触发词（如"记录这个学习"自动触发）

**实际情况：**
1. **无触发词设计** - 该技能是被动技能，通过场景识别主动记录，不是关键词触发
2. **手动记录模式**（当前）：
   - 用户说"记录这个学习"→ 助手执行写入操作（手动指令）
   - 需要用户提供具体内容
3. **自动检测模式**（需配置 hooks）：
   - UserPromptSubmit hook：每次用户消息后提醒评估
   - PostToolUse hook：命令失败后自动检测
   - 代价：每次对话消耗 50-100 tokens

**使用方式对比：**
| 模式 | 触发方式 | 开销 | 适用场景 |
|------|---------|------|---------|
| 手动 | 用户明确说"记录..." | 无 | 当前推荐 |
| 自动 | hooks 检测 | 50-100 tokens/次 | 高频使用后期 |

**记录类型：**
- LEARNINGS.md - 学习、修正、最佳实践
- ERRORS.md - 错误、失败
- FEATURE_REQUESTS.md - 功能请求

### Suggested Action
1. 当前保持手动记录模式，避免不必要的 token 消耗
2. 高频使用时（每天多次记录）再考虑配置 hooks
3. 在 AGENTS.md 中添加说明，提醒未来自己该技能的使用方式

### Metadata
- Source: conversation
- Related Files: .learnings/LEARNINGS.md, .learnings/ERRORS.md, .learnings/FEATURE_REQUESTS.md, skills/self-improving-agent/SKILL.md
- Tags: self-improvement, skill-usage, hooks, trigger-mechanism
- See Also: LRN-20260308-001

---

