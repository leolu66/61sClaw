---
name: weather-skill
description: 使用和风天气 API 查询实时天气和天气预报。当用户询问天气信息（如"北京今天天气怎么样"、"查询上海未来7天天气"、"深圳明天会下雨吗"）时使用此技能。支持通过城市名称或 Location ID 查询。
---

# 天气查询 Skill

使用和风天气 API 查询中国及全球城市的实时天气和天气预报。

## 脚本路径

`scripts/weather.py`（相对于技能目录）

## API Key

### 推荐：设置系统环境变量

使用系统环境变量配置 API Key，这样其他应用也能共享使用。

#### Windows

```powershell
# 临时（仅当前会话）
$env:XTC_WEATHER_API_KEY = "你的APIKey"

# 永久（系统环境变量）
setx XTC_WEATHER_API_KEY "你的APIKey"
```

#### Linux / Mac

```bash
# 临时（仅当前会话）
export XTC_WEATHER_API_KEY=你的APIKey

# 永久（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export XTC_WEATHER_API_KEY="你的APIKey"' >> ~/.bashrc
source ~/.bashrc
```

### 备选：在 OpenClaw 中配置

如果不想设置系统环境变量，也可以在 `~/.openclaw/config.json` 中添加：

```json
{
  "env": {
    "XTC_WEATHER_API_KEY": "你的APIKey"
  }
}
```

**注意**：此方式仅 OpenClaw 可用，其他应用无法共享。

### 获取 API Key

访问 https://dev.qweather.com/ 注册并获取免费 API Key。

## 快速使用

设置环境变量后即可查询：

### 查询实时天气

```bash
python scripts/weather.py 北京
```

### 查询天气预报

```bash
# 3天预报（默认）
python scripts/weather.py 上海 -t forecast

# 7天预报
python scripts/weather.py 广州 -t forecast -d 7
```

### 查询全部信息

```bash
python scripts/weather.py 深圳 -t all
```

### 获取原始 JSON 数据

```bash
python scripts/weather.py 北京 --raw
```

## Python 调用

```python
import subprocess
import json
import os

# 查询实时天气
script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'weather.py')
result = subprocess.run(
    ["python", script_path, "北京"],
    capture_output=True, text=True
)
print(result.stdout)

# 查询7天预报
result = subprocess.run(
    ["python", script_path, "上海", "-t", "forecast", "-d", "7"],
    capture_output=True, text=True
)
print(result.stdout)
```

## 天气现象代码

常见天气现象代码对照：
- 100: 晴
- 101: 多云
- 102: 少云
- 103: 晴间多云
- 104: 阴
- 150: 晴（夜间）
- 151: 多云（夜间）
- 300: 阵雨
- 301: 强阵雨
- 302: 雷阵雨
- 303: 强雷阵雨
- 305: 小雨
- 306: 中雨
- 307: 大雨
- 310: 暴雨
- 400: 小雪
- 401: 中雪
- 402: 大雪

完整代码表参考：https://dev.qweather.com/docs/resource/icons/

## API 说明

- 使用和风天气开发版 API
- 支持实时天气、3-30天预报
- 支持中国城市名称自动解析 Location ID
- API 文档：https://dev.qweather.com/docs/
