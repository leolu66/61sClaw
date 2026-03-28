# Edge TTS 技能

> ⚠️ **已弃用 (Deprecated)**
> 
> 此技能已不再维护。原因：
> - 需要网络连接
> - 依赖第三方库
> 
> **推荐使用**: `windows-tts` - Windows 系统自带 TTS（完全免费，离线可用，无需额外依赖）

---

使用微软 Edge TTS（免费）将文字转换为语音。

## 使用方法

```
edge-tts 你好，我是小天才
edge-tts "今天天气真好" --voice zh-CN-XiaoxiaoNeural
```

## 参数

- `text` - 要转换的文字（必填）
- `--voice` - 声音名称（可选，默认使用 zh-CN-XiaoxiaoNeural）

## 中文声音

- `zh-CN-XiaoxiaoNeural` - 晓晓，女声，温柔自然（默认）
- `zh-CN-YunxiNeural` - 云希，男声，年轻活泼
- `zh-CN-YunjianNeural` - 云健，男声，沉稳专业
- `zh-CN-XiaoyiNeural` - 晓伊，女声，甜美可爱
- `zh-CN-YunyangNeural` - 云扬，男声，新闻播报风格

## 英文声音

- `en-US-AriaNeural` - Aria，女声
- `en-US-GuyNeural` - Guy，男声
- `en-GB-SoniaNeural` - Sonia，女声（英式）

## 依赖

- Python 3.8+
- edge-tts 库

## 安装依赖

```bash
pip install edge-tts
```
