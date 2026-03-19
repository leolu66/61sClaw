---
name: summarize
description: |
  文本摘要技能 - 使用 OpenClaw AI 模型对文本、URL、文件进行智能归纳总结。
  支持多种输入方式：直接文本、网页URL、本地文件、YouTube链接。
triggers:
  - "总结"
  - "摘要"
  - "归纳"
  - "summarize"
version: 2.0.0
---

# 文本摘要技能

使用 OpenClaw AI 模型对内容进行智能归纳总结，无需外部 API。

## 触发方式

| 用户说 | 动作 |
|--------|------|
| "总结一下这篇文章" | 总结当前上下文或指定内容 |
| "摘要：https://example.com" | 总结网页内容 |
| "归纳这个文件" | 总结文件内容 |
| "总结视频：https://youtu.be/xxx" | 总结 YouTube 视频内容 |

## 使用方法

### 1. 总结文本

> 👤 请总结以下内容：人工智能正在改变我们的生活方式...
>
> 🤖 【摘要】人工智能通过自动化、个性化推荐和智能助手等方式，正在深刻改变人们的工作、学习和日常生活...

### 2. 总结网页

> 👤 总结这个网页：https://example.com/article
>
> 🤖 正在获取网页内容...> 🤖 【摘要】该文章主要讨论了...

### 3. 总结文件

> 👤 总结一下这个文件：/path/to/document.pdf
>
> 🤖 正在读取文件...> 🤖 【摘要】文档主要包含...

### 4. 总结视频

> 👤 总结这个视频：https://youtu.be/dQw4w9WgXcQ
>
> 🤖 正在获取视频字幕...> 🤖 【摘要】视频主要内容...

## 功能特点

- **本地 AI 模型**: 使用 OpenClaw 内置 AI，无需外部 API Key
- **多格式支持**: 文本、网页、PDF、图片、音频、YouTube
- **智能提取**: 自动识别核心观点和关键信息
- **长度可调**: 支持简短、中等、详细三种摘要长度

## CLI 命令

```bash
# 总结文本
python scripts/summarize_cli.py text "要总结的文本内容"

# 总结网页
python scripts/summarize_cli.py url "https://example.com"

# 总结文件
python scripts/summarize_cli.py file "/path/to/file.pdf"

# 总结 YouTube 视频
python scripts/summarize_cli.py youtube "https://youtu.be/xxx"

# 指定摘要长度
python scripts/summarize_cli.py text "内容" --length short    # 简短
python scripts/summarize_cli.py text "内容" --length medium   # 中等（默认）
python scripts/summarize_cli.py text "内容" --length long     # 详细
```

## 依赖

- Python 3.7+
- requests（网页抓取）
- PyPDF2（PDF 读取）
- youtube-transcript-api（YouTube 字幕）

## 与 v1.0 的区别

| 特性 | v1.0 (旧版) | v2.0 (新版) |
|------|------------|------------|
| AI 模型 | 外部 API (OpenAI/Claude等) | OpenClaw 内置模型 |
| API Key | 需要配置 | 无需配置 |
| 成本 | 按量付费 | 免费 |
| 隐私 | 数据发送到外部 | 本地处理 |

## License

MIT
