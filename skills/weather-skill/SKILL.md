---
name: weather-skill
description: 使用和风天气 API 查询实时天气和天气预报。当用户询问天气信息（如"北京今天天气怎么样"、"查询上海未来7天天气"、"深圳明天会下雨吗"）时使用此技能。支持通过城市名称或 Location ID 查询。
---

# 天气查询 Skill

使用和风天气 API 查询中国及全球城市的实时天气和天气预报。

## 脚本路径

`scripts/weather.py`（相对于技能目录）

## API Key

需要设置和风天气 API Key。支持两种环境变量名称（兼容配置）：

```bash
# 优先使用 XTC_WEATHER_API_KEY（推荐）
export XTC_WEATHER_API_KEY=你的APIKey

# 或者使用 WEATHER_API_KEY
export WEATHER_API_KEY=你的APIKey
```

### 在 OpenClaw 中配置

在 `~/.openclaw/config.json` 中添加：

```json
{
  "env": {
    "XTC_WEATHER_API_KEY": "你的APIKey"
  }
}
```

获取 API Key: https://dev.qweather.com/

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
