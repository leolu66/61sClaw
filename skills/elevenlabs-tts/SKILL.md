# ElevenLabs TTS 技能

使用 ElevenLabs API 将文字转换为语音。

## 使用方法

```
 elevenlabs-tts 你好，我是小天才
 elevenlabs-tts "今天天气真好" --voice Rachel
```

## 参数

- `text` - 要转换的文字（必填）
- `--voice` - 声音 ID（可选，默认使用 Rachel）
- `--model` - 模型 ID（可选，默认使用 eleven_multilingual_v2）

## 常用声音

- `Rachel` - 女声，温和自然
- `Adam` - 男声，沉稳专业
- `Bella` - 女声，年轻活泼
- `Antoni` - 男声，温暖友好
- `Elli` - 女声，成熟知性

## 配置

在环境变量中设置 API Key：

```powershell
$env:ELEVENLABS_API_KEY="sk_620a2645e37da0f8a04024ee2c2d43ecda53fa3d0d2c52e3"
```

## 依赖

- Python 3.8+
- requests 库

## 安装依赖

```bash
pip install requests
```
