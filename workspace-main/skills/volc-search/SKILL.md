---
name: volc-search
description: |
  火山融合信息搜索API - 支持网页搜索、图片搜索、搜索结果总结。
  
  触发命令：
  - 搜索 xxx
  - 火山搜索 xxx
  - volc search xxx
  
  当用户需要进行网络搜索时使用此技能。
---

# 火山融合信息搜索

使用火山引擎融合信息搜索API进行网页搜索、图片搜索和搜索结果总结。

## 脚本路径

`C:\Users\luzhe\.openclaw\workspace-main\skills\volc-search\scripts\volc_search.py`

## 功能特性

- 🔍 **网页搜索**：返回搜索结果列表（标题、URL、摘要）
- 📝 **搜索总结**：使用大模型对搜索结果进行总结
- 🖼️ **图片搜索**：搜索相关图片
- 🔐 **API 认证**：使用火山融合信息搜索 API Key 进行认证

## 使用方法

### 命令行使用

```bash
# 网页搜索（默认 5 条结果）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\volc-search\scripts\volc_search.py" "搜索关键词"

# 指定结果数量
python "C:\Users\luzhe\.openclaw\workspace-main\skills\volc-search\scripts\volc_search.py" "搜索关键词" 10

# 搜索总结版
python "C:\Users\luzhe\.openclaw\workspace-main\skills\volc-search\scripts\volc_search.py" "搜索关键词" 5 summary

# 图片搜索
python "C:\Users\luzhe\.openclaw\workspace-main\skills\volc-search\scripts\volc_search.py" "搜索关键词" 3 image
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 1 | 搜索关键词 | - |
| 2 | 返回结果数量 | 5 |
| 3 | 搜索类型 | web (可选: web, web_summary, image) |

### 搜索类型说明

- `web`: 网页搜索，返回搜索结果列表
- `web_summary`: 搜索总结版，返回搜索结果及LLM总结
- `image`: 图片搜索，返回相关图片

## API 认证

使用 API Key 方式进行认证：
- URL: https://open.feedcoopapi.com/search_api/web_search
- Header: `Authorization: Bearer <API_KEY>`

API Key 存储在密码箱中，使用命令 `查 volcsearch 的 api_key` 获取。

## 注意事项

- 免费额度：web搜索和web搜索总结版各5000次
- 限流：默认 5 QPS
- 搜索总结版会消耗更多token

## 相关文件

- `scripts/volc_search.py` - 主搜索脚本
