---
name: ai-news-fetcher
description: 获取国内权威AI科技网站的最新新闻，并以带摘要的卡片形式展示。当用户询问"获取AI新闻"、"最新AI资讯"、"科技新闻"、"AI动态"、"有什么AI新闻"时使用此skill。支持从机器之心、量子位、InfoQ等国内主流AI媒体获取新闻。
---

# AI新闻获取器

用于获取国内权威AI科技网站的最新新闻。

## 脚本路径

`C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py`

## 支持的网站

- 机器之心 (jiqizhixin.com)
- 量子位 (qbitai.com)
- InfoQ中国 (infoq.cn)
- 智东西 (zhidx.com)
- AI科技评论 (leiphone.com)

## 使用方法

### 直接运行获取所有新闻

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py"
```

### 常用参数

- `--limit N`: 每个网站获取N条新闻（默认5条）
- `--sources 网站名1,网站名2`: 指定特定网站
- `--output 文件.md`: 保存到文件

### 示例命令

```bash
# 获取每个网站10条新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --limit 10

# 只获取机器之心和量子位的新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --sources 机器之心,量子位

# 保存到文件
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\scripts\fetch_ai_news.py" --output ai_news.md
```

## 输出格式

输出为Markdown格式的卡片，包含：
- 新闻标题
- 来源网站
- 发布时间
- 内容摘要（200字内）
- 原文链接

## 依赖安装

首次使用前需要安装依赖：

```bash
pip install requests beautifulsoup4
```
