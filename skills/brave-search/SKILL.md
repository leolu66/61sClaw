---
name: brave-search
description: |
  使用 Brave Search API 进行网页搜索。
  
  触发命令：
  - Brave Search xxx
  - web search xxx
  
  当用户需要进行网络搜索时使用此技能。注意：需要开启 VPN 才能访问 Brave Search API。
---

# Brave Search 网页搜索

使用 Brave Search API 进行快速、准确的网页搜索。

## 脚本路径

`C:\Users\luzhe\.openclaw\workspace-main\skills\brave-search\scripts\brave_search.py`

## 功能特性

- 🔍 **快速搜索**：返回标题、URL 和摘要
- 🌐 **多语言支持**：支持中英文搜索
- 📄 **结果可定制**：可设置返回结果数量
- 🔐 **API 认证**：使用 Brave Search API Key 进行认证

## 使用方法

### 命令行使用

```bash
# 基本搜索（默认 5 条结果）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\brave-search\scripts\brave_search.py" "搜索关键词"

# 指定结果数量
python "C:\Users\luzhe\.openclaw\workspace-main\skills\brave-search\scripts\brave_search.py" "搜索关键词" 10

# 指定语言和国家
python "C:\Users\luzhe\.openclaw\workspace-main\skills\brave-search\scripts\brave_search.py" "搜索关键词" 5 CN zh-hans
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 1 | 搜索关键词 | "OpenClaw" |
| 2 | 返回结果数量 | 5 |
| 3 | 国家代码 | CN |
| 4 | 语言代码 | zh-hans |

### 支持的语言代码

- `zh-hans` - 简体中文
- `zh-hant` - 繁体中文
- `en` - 英语
- `ja` - 日语
- `ko` - 韩语
- 以及其他 50+ 种语言

## 注意事项

⚠️ **VPN 要求**：Brave Search API 需要翻墙才能访问，请确保开启 VPN。

## 相关文件

- `scripts/brave_search.py` - 主搜索脚本
- `scripts/config.json` - 配置文件（API Key 等）
