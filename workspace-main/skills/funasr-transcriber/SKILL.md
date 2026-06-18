---
name: "funasr-transcriber"
description: "本地语音转文字，基于达摩院 FunASR。支持中英文转录、时间戳、说话人分离。触发词：转录音频、语音识别、语音转文字"
---

# FunASR 语音转录

## 需求说明（SRS）

### 触发条件
- "转录音频"、"转录这段录音"、"语音转文字"
- "用 FunASR 识别这个音频"、"语音识别这个文件"

### 功能描述
使用本地部署的阿里达摩院 FunASR（MIT 开源）进行语音转文字，支持：
- 中文/英文/日文/韩文/粤语等 50+ 语言
- 自动 VAD 语音分段
- 说话人分离（多人对话自动标注说话人）
- 情感检测
- 输出带时间戳的结构化文本

### 输入/输出
- **输入**: 本地音频/视频文件（wav/mp3/m4a/flac/mp4/mkv/avi 等）或音频 URL；视频自动用 ffmpeg 提取音轨
- **输出**: 带时间戳和说话人标签的转录文本

### 依赖条件
- Python >= 3.8，funasr、torch、torchaudio 已安装
- 模型首次使用自动从 ModelScope 下载（~1GB）
- 无 GPU 时自动使用 CPU

### 边界情况
- 音频不存在时提示错误
- 识别失败时输出错误信息

---

## 使用方法

### 基本转录

```bash
python scripts/transcribe.py "音频文件.wav"
```

### 翻录模式

| 参数 | 模型 | 特点 | 适用 |
|------|------|------|------|
| `--detailed`（默认） | Fun-ASR-Nano 800M | 带标点、高精度 | 需要精读的内容 |
| `--fast` | SenseVoiceSmall 234M | 速度快 8-10x，无标点 | 长视频快速扫读 |

### 其他参数

| 参数 | 作用 |
|------|------|
| `--no-timestamps` | 不显示时间戳 |
| `--no-speaker` | 不区分说话人（如单人口播） |
| `-o 文件.txt` | 保存结果到文本文件 |

### 常用场景

```bash
# 快速翻录长视频（10倍实时速度）
python scripts/transcribe.py "lecture.mp4" --fast -o notes.txt

# 详细翻录（带标点，默认）
python scripts/transcribe.py "meeting.wav"

# 单人口播
python scripts/transcribe.py "podcast.mp3" --no-speaker -o result.txt

# URL 音频
python scripts/transcribe.py "https://example.com/audio.wav"
```

## 系统音频录制（B站/网页视频等）

```bash
# 录制120秒 + 标题 + 专有名词纠正
python scripts/capture_transcribe.py -d 120 --fast -t "Loop Engineering详解" --terms "Loop Engineering,Claude Code,Boris" -o notes.txt

# 详细翻录（带标点）
python scripts/capture_transcribe.py -d 420 --detailed -t "视频标题" --terms "术语1,术语2"

# 手动控制时长（Enter 停止）
python scripts/capture_transcribe.py -d 0 --fast
```

**工作流程：** 3秒倒计时（启动视频）→ WASAPI Loopback 录制（进度条）→ FunASR 转录 → 输出带标题和术语

| 参数 | 作用 |
|------|------|
| `-d 秒数` | 录制时长，0=手动Enter停止 |
| `-t "标题"` | 视频标题，输出时标注在顶部 |
| `--terms "词1,词2"` | 专有名词，用于自动纠正常见转录错误 |
| `--fast` | 快速翻录 |
| `--detailed` | 详细翻录（默认） |
| `--window` | 弹新终端窗口运行（显示实时进度条） |

## 脚本路径

`skills/funasr-transcriber/scripts/transcribe.py`  
`skills/funasr-transcriber/scripts/capture_transcribe.py`

## 模型参考

详见 `references/models.md`

## 部署信息

- 安装路径: `D:\FunASR\`
- 模型缓存: `C:\Users\luzhe\.cache\modelscope\`
- 默认模型: SenseVoiceSmall (234M)

---

## DoD 检查表

**开发日期**: 2026-06-19
**状态**: 完成
