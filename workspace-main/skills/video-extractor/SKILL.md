---
name: video-extractor
description: Extract text transcripts from Chinese video platforms (头条/Toutiao, 抖音/Douyin, 快手/Kuaishou, B站/Bilibili, 西瓜视频, 小红书, 微博视频, etc.). Use when asked to "提取视频内容", "转文字", "转录视频", "get transcript", "extract video text", or given a video URL from a Chinese platform for content extraction.
---

# Video Extractor

## Quick Start

```bash
D:\anaconda3\python.exe skills/video-extractor/scripts/extract.py <video-url>
```

## Workflow

### Step 1: Extract raw transcript

```bash
D:\anaconda3\python.exe skills/video-extractor/scripts/extract.py --model small <video-url>
```

Options:
- `--model tiny` — fastest, lowest accuracy
- `--model base` — fast, okay accuracy
- `--model small` (default) — good balance

### Step 2: LLM cleanup (agent responsibility)

Read the saved file, then use the current LLM to clean it up and overwrite:

```
Read output/<视频标题>.txt
→ 加标点符号
→ 转简体中文
→ 纠正明显的 Whisper 识别错误（同音/近音字）
→ Write 覆盖原文件
```

## How It Works

| Step | Method | Fallback |
|------|--------|----------|
| 1. Video info | yt-dlp fetches title + duration | — |
| 2. Subtitles | yt-dlp downloads subtitles | → Step 3 if none |
| 3. Audio + STT | yt-dlp audio → Whisper (Chinese, `small`) | Exit with error |
| 4. Cleanup | **Agent runs LLM to fix: 繁体→简体, 加标点, 纠错** | — |

## Platform Coverage

头条/Toutiao, 抖音/Douyin, 快手/Kuaishou, B站/Bilibili, 西瓜视频/Xigua,
好看视频, 小红书/Xiaohongshu, 微博/Weibo, 视频号/WeChat Channels

(Any site yt-dlp supports)

## Requirements

Anaconda Python packages:
- `yt-dlp` (`pip install yt-dlp`)
- `openai-whisper` (`pip install openai-whisper`)

System:
- `ffmpeg` — on PATH or at `D:\ffmpeg-8.1.1\bin\ffmpeg.EXE`

## Scripts

### `scripts/extract.py`

```
usage: extract.py [-h] [--model {tiny,base,small,medium,large}] url
```

## Output

Saved to `output/<视频标题>.txt`. Format: header (title, URL, timestamp) + raw transcript body.

Temporary audio files in `%TEMP%` are auto-cleaned after transcription.
