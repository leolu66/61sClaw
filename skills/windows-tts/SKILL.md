# Windows TTS 技能

使用 Windows 系统自带的 SAPI5 语音合成引擎（完全离线，无需网络）。

## 使用方法

```
windows-tts 你好，我是小天才
windows-tts "今天天气真好" --voice Huihui
```

## 参数

- `text` - 要转换的文字（必填）
- `--voice` - 声音名称（可选，默认使用系统默认声音）
- `--rate` - 语速（-10 到 10，默认 0）
- `--volume` - 音量（0 到 100，默认 100）
- `--output` - 输出为音频文件（WAV 格式）

## 中文声音

Windows 10/11 通常内置以下中文声音：

- `Huihui` - 慧慧，女声（默认）
- `Kangkang` - 康康，男声
- `Yaoyao` - 瑶瑶，女声

## 列出可用声音

```
python tts.py --list-voices
```

## 特点

- ✅ 完全离线，无需网络
- ✅ 无需安装额外依赖（使用系统内置 SAPI5）
- ✅ 响应速度快
- ✅ 支持保存为 WAV 文件

## 依赖

- Windows 操作系统
- Python 3.x
- pywin32（通常已安装）
