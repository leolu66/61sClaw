---
name: potplayer-music
description: 使用 PotPlayer 64-bit 播放本地音乐文件。当用户说"播放音乐"、"放首歌"、"用PotPlayer播放"或需要播放本地音频文件时触发。支持播放指定文件、暂停、继续、停止、下一首、上一首、调节音量等操作。
---

# PotPlayer 音乐播放器

使用 PotPlayer 64-bit 播放本地音乐文件。

## 要求

- PotPlayer 64-bit 已安装（路径：`C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe`）
- 本地音乐文件路径

## 播放音乐

当用户说"播放音乐"时，执行以下流程：

1. **后台检查更新** - 在后台检查 `E:\Music\精选` 是否有新增歌曲（每天只检查一次）
2. **播放精选清单** - 播放 `E:\Music\精选.m3u`

```powershell
# 后台检查并更新播放清单（每天一次，不阻塞）
Start-Process python -ArgumentList "C:\Users\luzhe\.openclaw\workspace-main\agfiles\update_playlist.py" -WindowStyle Hidden

# 播放精选清单
& "C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe" "E:\Music\精选.m3u"
```

### 手动播放其他音乐

```powershell
# 播放指定文件
& "C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe" "音乐文件路径.mp3"

# 播放文件夹（随机播放）
& "C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe" "文件夹路径" /random

# 播放并添加到播放列表
& "C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe" "音乐文件路径.mp3" /add

# 播放 M3U 播放列表
& "C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe" "E:\Music\playlist.m3u"
```

## 播放控制

使用 `control_potplayer.ps1` 控制当前运行的 PotPlayer：

```powershell
# 下一首
powershell -ExecutionPolicy Bypass -File "C:\Users\luzhe\.openclaw\workspace-main\agfiles\control_potplayer.ps1" -Action next

# 上一首
powershell -ExecutionPolicy Bypass -File "C:\Users\luzhe\.openclaw\workspace-main\agfiles\control_potplayer.ps1" -Action prev

# 暂停/播放
powershell -ExecutionPolicy Bypass -File "C:\Users\luzhe\.openclaw\workspace-main\agfiles\control_potplayer.ps1" -Action pause

# 停止
powershell -ExecutionPolicy Bypass -File "C:\Users\luzhe\.openclaw\workspace-main\agfiles\control_potplayer.ps1" -Action stop
```

**快捷键映射：**
- 下一首：Page Down
- 上一首：Page Up
- 暂停/播放：空格
- 停止：ESC

## 精选播放清单

- **精选目录**：`E:\Music\精选`
- **播放清单**：`E:\Music\精选.m3u`
- **自动更新**：每次播放时自动检查是否有新增歌曲

### 手动更新播放清单

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\agfiles\update_playlist.py"
```

## 查找音乐文件

**用户音乐库位置：`E:\Music`（包括所有子目录）**

常见音乐文件夹位置：
- `E:\Music\` ← **用户主音乐库**
- `C:\Users\用户名\Music\`
- `D:\Music\`
- `C:\Users\用户名\Downloads\`

### 播放列表

- **播放列表文件**：`E:\Music\playlist.m3u`
- 可以直接播放 M3U 播放列表文件

### 搜索音乐文件

在 `E:\Music` 及其子目录中搜索音乐：

```powershell
# 递归查找所有音乐文件
Get-ChildItem -Path "E:\Music" -Recurse -Include *.mp3,*.flac,*.wav,*.aac,*.ogg,*.wma,*.m4a

# 按艺术家/专辑搜索
Get-ChildItem -Path "E:\Music\艺术家名" -Recurse -Include *.mp3
```

## 注意事项

- PotPlayer 必须已安装
- 如果 PotPlayer 已经在运行，新文件会添加到播放列表
- 支持格式：MP3, FLAC, WAV, AAC, OGG, WMA 等常见音频格式
