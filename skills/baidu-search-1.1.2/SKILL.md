---
name: baidu-search
description: |
  使用百度 AI 搜索引擎 (BDSE) 进行网页搜索。
  
  触发命令：
  - 搜索 xxx
  - 百度一下 xxx
  - 百度搜索 xxx
  
  当用户需要进行网络搜索时使用此技能。无需 VPN，适合中文搜索。
metadata: { "openclaw": { "emoji": "🔍︎",  "requires": { "bins": ["python3"], "env":["BAIDU_API_KEY"]},"primaryEnv":"BAIDU_API_KEY" } }
---

# Baidu Search

使用百度 AI 搜索引擎进行网页搜索。

## 优先级说明

**此技能为默认优先搜索服务**。当用户说"搜索 xxx"时，优先使用百度搜索。

## 功能特性

- 🔍 **中文优化**：百度搜索，对中文内容支持更好
- 🚀 **无需 VPN**：国内直接访问，无需翻墙
- 📄 **结果可定制**：可设置返回结果数量和时间范围
- 💰 **免费额度**：每日赠送 1000 次搜索额度

## 使用方法

### 命令行使用

```bash
# 基本搜索（默认 10 条结果）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\baidu-search-1.1.2\scripts\search.py" '{"query":"搜索关键词"}'

# 指定结果数量
python "C:\Users\luzhe\.openclaw\workspace-main\skills\baidu-search-1.1.2\scripts\search.py" '{"query":"搜索关键词","count":5}'

# 指定时间范围（pd=过去24小时, pw=过去7天, pm=过去31天, py=过去365天）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\baidu-search-1.1.2\scripts\search.py" '{"query":"搜索关键词","freshness":"pd"}'
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| query | 搜索关键词 | 必填 |
| count | 返回结果数量 | 10 |
| freshness | 时间范围 | 无限制 |

## 服务配额

| 能力名称 | 赠送额度 | 计费方式 | 基础定价 | 速率限制 |
|---------|---------|---------|---------|---------|
| 百度搜索 | 1000 次/日 | 按量后付费 | 0.036 元/次 | 3 QPS |
| 智能搜索生成 | 100 次/日 | 按量后付费 | 0.036 元/次 | 3 QPS |

## 相关文件

- `scripts/search.py` - 主搜索脚本
- `SKILL.md` - 技能说明文档
