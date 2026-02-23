---
name: music-player
description: 使用 PotPlayer 播放本地音乐文件。当用户说"播放音乐"、"播放歌曲"、"用PotPlayer播放"、"播放[音乐文件路径]"时触发此技能。支持播放 MP3、FLAC、WAV 等常见音频格式。
---

# 音乐播放器

使用 PotPlayer 播放本地音乐文件。

## 使用方法

### 播放音乐

运行脚本播放指定音乐文件：

```bash
python scripts/play_music.py "<音乐文件路径>"
```

示例：
```bash
python scripts/play_music.py "C:\Users\luzhe\Music\song.mp3"
python scripts/play_music.py "D:\Music\周杰伦\稻香.mp3"
```

## 支持的格式

- MP3
- FLAC
- WAV
- AAC
- OGG
- WMA
- 其他 PotPlayer 支持的音频格式

## 注意事项

- PotPlayer 路径固定为：`C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe`
- 如果 PotPlayer 未安装在此路径，需要修改脚本中的路径
- 支持中文路径
