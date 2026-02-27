---
name: weather-skill
description: 使用和风天气 API 查询实时天气和天气预报。当用户询问天气信息（如"北京今天天气怎么样"、"查询上海未来7天天气"、"深圳明天会下雨吗"）时使用此技能。支持通过城市名称或 Location ID 查询。
---

# 天气查询 Skill

使用和风天气 API 查询中国及全球城市的实时天气和天气预报。

## 脚本路径

`C:\Users\luzhe\.openclaw\workspace-main\skills\weather-skill\scripts\weather.py`

## API Key

Skill 已预配置 API Key，可直接使用。

如需使用其他 Key，可通过以下方式设置：

### 方式 1: 环境变量

```bash
# Windows
set WEATHER_API_KEY=你的APIKey

# Linux/Mac
export WEATHER_API_KEY=你的APIKey
```

### 方式 2: 修改脚本

编辑 `scripts/weather.py` 修改默认 Key：

```python
API_KEY = os.environ.get("WEATHER_API_KEY", "你的APIKey")
```

## 快速使用

设置环境变量后即可查询：

### 查询实时天气

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\weather-skill\scripts\weather.py" 北京
```

### 查询天气预报

```bash
# 3天预报（默认）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\weather-skill\scripts\weather.py" 上海 -t forecast

# 7天预报
python "C:\Users\luzhe\.openclaw\workspace-main\skills\weather-skill\scripts\weather.py" 广州 -t forecast -d 7
```

### 查询全部信息

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\weather-skill\scripts\weather.py" 深圳 -t all
```

### 获取原始 JSON 数据

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\weather-skill\scripts\weather.py" 北京 --raw
```

## Python 调用

```python
import subprocess
import json

# 查询实时天气
result = subprocess.run(
    ["python", "C:\\Users\\luzhe\\.openclaw\\workspace-main\\skills\\weather-skill\\scripts\\weather.py", "北京"],
    capture_output=True, text=True
)
print(result.stdout)

# 查询7天预报
result = subprocess.run(
    ["python", "C:\\Users\\luzhe\\.openclaw\\workspace-main\\skills\\weather-skill\\scripts\\weather.py", "上海", "-t", "forecast", "-d", "7"],
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
