---
name: audio-control
description: 音频设备控制技能 - 控制播放设备和麦克风的静音、音量等功能。当用户说"音频控制"、"静音"、"取消静音"、"麦克风静音"、"查看音频设备"时触发。
triggers:
  - 音频控制
  - 静音
  - 取消静音
  - 麦克风静音
  - 查看音频设备
  - 控制音量
version: 1.0
---

# Audio Control - 音频设备控制

控制 Windows 音频播放设备和麦克风。

## 前提条件

### 安装 AudioDeviceCmdlets 模块

首次使用需要安装 PowerShell 模块：

```powershell
Install-Module -Name AudioDeviceCmdlets -Force -Scope CurrentUser
```

安装后即可使用以下所有功能。

## 功能

### 1. 查看音频设备状态

```powershell
.\audio_control.ps1 -Action status
```

显示当前播放设备和麦克风的音量、静音状态。

### 2. 静音控制

```powershell
# 静音播放设备
.\audio_control.ps1 -Action mute

# 取消静音
.\audio_control.ps1 -Action unmute

# 静音麦克风
.\audio_control.ps1 -Action mic-mute

# 取消麦克风静音
.\audio_control.ps1 -Action mic-unmute
```

### 3. 查看设备列表

```powershell
.\audio_control.ps1 -Action list
```

## 触发示例

| 用户指令 | 执行操作 |
|----------|----------|
| "查看音频设备" | 执行 list 命令 |
| "音频状态" | 执行 status 命令 |
| "静音" | 执行 mute 命令 |
| "取消静音" | 执行 unmute 命令 |
| "麦克风静音" | 执行 mic-mute 命令 |
| "关闭麦克风" | 执行 mic-mute 命令 |

## 输出格式

### 状态查询

```
=== Audio Status ===

Playback Device: Speakers (Realtek High Definition Audio)
Volume: 75%
Muted: False

Microphone: Microphone (USB Audio Device)
Muted: False
```

### 设备列表

```
=== Audio Devices ===

Playback Devices:
  1. Speakers (Realtek) [Default]
  2. Bluetooth Speaker
  3. NVIDIA Virtual Audio Device

Recording Devices:
  1. Microphone (USB Audio Device) [Default]
  2. Internal Microphone
```

## 替代方案

如果 PowerShell 模块安装失败，可使用以下替代工具：

### 1. SoundSwitch（推荐）
- 快速切换默认音频设备
- 支持快捷键
- 下载: https://github.com/Belphemur/SoundSwitch

### 2. NirCmd
- 命令行工具
- 用法: `nircmd.exe mutesysvolume 2`

### 3. 系统快捷键
- 静音: `Win + Alt + M` 或 `Fn + F4`
- 音量调节: `Win + Alt + 上/下箭头`

## 文件

- `scripts/audio_control.ps1` - PowerShell 控制脚本
- `scripts/audio_control.py` - Python 备用脚本（需要 pycaw）
