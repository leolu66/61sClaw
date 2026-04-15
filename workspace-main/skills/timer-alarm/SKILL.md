---
name: timer-alarm
description: |
  定时器和闹钟管理工具。支持设置倒计时（如15分钟）、指定时间闹钟（如18:00）、
  以及重复闹钟（如每天上午10点）。可为闹钟设置提示文本，支持TTS语音播报。
  
  触发指令：
  - "设置15分钟闹钟"
  - "设置18:00的闹钟"
  - "设置每天上午10点的闹钟"
  - "设置倒计时"
  - "查看所有闹钟"
  - "取消闹钟"
---

# 定时器与闹钟 (Timer & Alarm)

管理定时器和闹钟，支持倒计时、指定时间闹钟、重复闹钟，并可配置TTS语音提醒。

## 功能特性

- **倒计时**：设置N分钟后提醒（如15分钟、30分钟）
- **指定时间闹钟**：设置在具体时间提醒（如18:00、明天早上8点）
- **重复闹钟**：设置每天/每周重复提醒（如每天上午10点、每周一早上9点）
- **自定义提示**：为每个闹钟设置提醒文本
- **TTS语音播报**：闹钟响起时自动朗读提示文本（如果系统支持）

## 使用方法

### 设置倒计时

```bash
python scripts/timer.py --countdown 15 --message "休息一下吧"
```

或简写：
```bash
python scripts/timer.py -c 15 -m "休息一下吧"
```

### 设置指定时间闹钟

```bash
python scripts/timer.py --time "18:00" --message "该下班了"
python scripts/timer.py --time "2026-03-06 08:00" --message "明天早上开会"
```

### 设置重复闹钟

```bash
# 每天重复
python scripts/timer.py --time "10:00" --repeat daily --message "每日站会"

# 每周重复（周一到周五）
python scripts/timer.py --time "09:00" --repeat weekdays --message "开始工作"

# 每周重复（指定星期几）
python scripts/timer.py --time "14:00" --repeat monday,wednesday,friday --message "团队会议"
```

### 查看所有闹钟

```bash
python scripts/timer.py --list
```

### 取消闹钟

```bash
# 取消指定ID的闹钟
python scripts/timer.py --cancel <alarm_id>

# 取消所有闹钟
python scripts/timer.py --cancel-all
```

## 配置说明

配置文件 `config.json`：

```json
{
  "tts_enabled": true,
  "tts_voice": "default",
  "alarm_sound": "default",
  "snooze_minutes": 5
}
```

- `tts_enabled`: 是否启用TTS语音播报
- `tts_voice`: TTS语音类型（如果系统支持多种语音）
- `alarm_sound`: 闹钟提示音
- `snooze_minutes`: 贪睡时间（分钟）

## 闹钟存储

闹钟信息保存在 `data/alarms.json` 中，包括：
- 闹钟ID
- 触发时间
- 重复规则
- 提示文本
- 是否启用

## 触发词

- "设置15分钟闹钟"
- "设置18:00的闹钟"
- "设置每天上午10点的闹钟"
- "设置倒计时"
- "查看所有闹钟"
- "取消闹钟"

## 技术说明

- 使用后台进程监控闹钟时间
- 支持系统通知和TTS语音双重提醒
- 闹钟时间到达时，如果系统支持，会自动朗读提示文本

## 相关文件

- `scripts/timer.py` - 主脚本
- `scripts/alarm_manager.py` - 闹钟管理器
- `scripts/tts_player.py` - TTS语音播放器
- `config.json` - 配置文件

## 开发规范参考

创建技能时请参考 `skills/SKILL_DO.md` 中的完整规范。

### 文件路径规范（重要）

#### 原则 1：技能自包含
**所有技能默认只能在自己的工作空间内读写文件**。
- 使用相对路径（相对于技能目录）
- 默认输出到技能自己的工作空间
- 确保技能分享后仍可用

```python
# [OK] 正确：使用相对路径，保存在技能目录内
output_dir = Path(__file__).parent / "output"

# [ERROR] 错误：使用绝对路径或硬编码路径
output_dir = "D:\\projects\\workspace\\output"
```

#### 原则 2：外部协作需配置
**如果技能需要在工作空间外读写文件，必须通过配置文件设置路径**。
- 不硬编码外部路径
- 通过配置文件或环境变量传入
- 配置项名称清晰（如 `shared_dir`, `output_path`）

```python
# [OK] 正确：从配置文件读取路径
import json
config = json.load(open("config.json"))
shared_dir = config.get("shared_output_dir")

# [ERROR] 错误：硬编码共享路径
shared_dir = "D:\\projects\\workspace\\shared\\output"
```

#### 示例配置

```json
{
  "output_dir": "./output",
  "shared_dir": "D:\\projects\\workspace\\shared\\output"
}
```
