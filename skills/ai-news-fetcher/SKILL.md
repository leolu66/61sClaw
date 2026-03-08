---
name: ai-news-fetcher
description: 获取国内权威AI科技网站的最新新闻，并以带摘要的卡片形式展示。当用户询问"获取AI新闻"、"最新AI资讯"、"科技新闻"、"AI动态"、"有什么AI新闻"时使用此skill。支持从机器之心、量子位、InfoQ等国内主流AI媒体获取新闻。
---

# AI新闻获取器

用于获取国内权威AI科技网站的最新新闻。

## 脚本路径

`C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py`

## 支持的网站

- 量子位 (qbitai.com)
- InfoQ中国 (infoq.cn)
- 智东西 (zhidx.com)
- AI科技评论 (leiphone.com)
- 36氪 (36kr.com)
- AiBase (news.aibase.cn)
- 极客公园 (geekpark.net)

## 使用方法

### 直接运行获取所有新闻

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py"
```

**缓存机制：**
- 默认自动保存到 `logs/daily/ai-news-YYYYMMDD-HH.md`
- 4小时内重复查询会直接从缓存读取，不会重新抓取
- 新闻标题已添加链接，方便点击查看详情

### 常用参数

- `--limit N`: 每个网站获取N条新闻（默认5条）
- `--sources 网站名1,网站名2`: 指定特定网站
- `--output 文件.md`: 额外保存到指定文件
- `--no-cache`: 强制刷新，忽略缓存
- `--cache-hours N`: 设置缓存有效期（默认4小时）

### 示例命令

```bash
# 获取每个网站10条新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --limit 10

# 只获取量子位和InfoQ的新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --sources 量子位,InfoQ

# 强制刷新（忽略缓存）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --no-cache

# 保存到指定文件（同时仍会缓存）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --output ai_news.md
```

## 输出格式

输出为Markdown格式，包含：

### 1. 结果汇总表格
| 来源 | 获取数量 | 链接 |
| ---------- | -------- | ------- |
| 量子位 | 5条 | [qbitai.com](https://www.qbitai.com) |
| InfoQ | 5条 | [infoq.cn](https://www.infoq.cn) |
| ... | ... | ... |

### 2. 每个来源的详细表格
| 序号 | 标题 | 摘要 | 更新时间 |
| ---- | ---- | ---- | -------- |
| 1 | [新闻标题](链接) | 摘要内容... | 7小时前 |
| 2 | [新闻标题](链接) | 摘要内容... | 昨天 |

**特点：**
- 标题带可点击链接
- 摘要限制30字，超出用...截断
- 表格形式清晰易读

## 依赖安装

首次使用前需要安装依赖：

```bash
pip install requests beautifulsoup4 playwright
playwright install chromium
```

**注意：**
- `requests` 和 `beautifulsoup4` 用于大部分静态网站
- `playwright` 用于需要 JavaScript 动态渲染的网站（如 InfoQ）
