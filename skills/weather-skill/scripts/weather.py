#!/usr/bin/env python3
"""
和风天气 API 查询脚本
文档: https://dev.qweather.com/docs/
"""

import argparse
import gzip
import json
import sys
import urllib.request
import urllib.parse
from urllib.error import HTTPError, URLError

# API 配置
# 支持多种环境变量名称，兼容不同配置方式
import os
API_KEY = os.environ.get("XTC_WEATHER_API_KEY") or os.environ.get("WEATHER_API_KEY", "")
BASE_URL = "https://devapi.qweather.com/v7/weather"
GEO_URL = "https://geoapi.qweather.com/v2/city/lookup"


def make_request(url: str, params: dict) -> dict:
    """发送 HTTP 请求并返回 JSON 响应"""
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    # 创建请求对象，添加 gzip 支持
    req = urllib.request.Request(
        full_url,
        headers={
            "Accept-Encoding": "gzip",
            "User-Agent": "weather-skill/1.0"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            # 检查是否是 gzip 压缩
            if response.headers.get('Content-Encoding') == 'gzip':
                data = gzip.decompress(response.read()).decode('utf-8')
            else:
                data = response.read().decode('utf-8')
            return json.loads(data)
    except HTTPError as e:
        return {"error": f"HTTP Error: {e.code} - {e.reason}"}
    except URLError as e:
        return {"error": f"URL Error: {e.reason}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": str(e)}


def lookup_location(city_name: str) -> str:
    """根据城市名称查询 Location ID"""
    params = {
        "location": city_name,
        "key": API_KEY,
        "range": "cn"
    }
    
    result = make_request(GEO_URL, params)
    
    if "error" in result:
        return None
    
    if result.get("code") != "200":
        return None
    
    locations = result.get("location", [])
    if not locations:
        return None
    
    # 返回第一个匹配的城市 ID
    return locations[0].get("id")


def get_weather_now(location: str) -> dict:
    """获取实时天气"""
    url = f"{BASE_URL}/now"
    params = {
        "location": location,
        "key": API_KEY
    }
    return make_request(url, params)


def get_weather_forecast(location: str, days: int = 3) -> dict:
    """获取天气预报
    days: 3 (3天), 7 (7天), 10 (10天), 15 (15天), 30 (30天)
    """
    if days in [3, 7]:
        endpoint = f"{days}d"
    elif days in [10, 15, 30]:
        endpoint = f"{days}d"
    else:
        endpoint = "3d"
    
    url = f"{BASE_URL}/{endpoint}"
    params = {
        "location": location,
        "key": API_KEY
    }
    return make_request(url, params)


def format_weather_now(data: dict, city_name: str = "") -> str:
    """格式化实时天气输出"""
    if not API_KEY:
        return """错误: 未设置 API Key

请通过以下方式之一设置你的和风天气 API Key:

方式 1 - 设置环境变量:
  Windows: set XTC_WEATHER_API_KEY=你的APIKey
  Linux/Mac: export XTC_WEATHER_API_KEY=你的APIKey

方式 2 - 在 OpenClaw 配置文件中设置:
  在 ~/.openclaw/config.json 中添加:
  {
    "env": {
      "XTC_WEATHER_API_KEY": "你的APIKey"
    }
  }

获取 API Key: https://dev.qweather.com/"""
    
    if "error" in data:
        return f"查询失败: {data['error']}"
    
    if data.get("code") != "200":
        return f"查询失败: API 返回错误码 {data.get('code')}"
    
    now = data.get("now", {})
    
    city_str = f"[{city_name}] " if city_name else ""
    
    lines = [
        f"{city_str}实时天气",
        f"温度: {now.get('temp', '--')}°C",
        f"体感温度: {now.get('feelsLike', '--')}°C",
        f"天气: {now.get('text', '--')}",
        f"风向: {now.get('windDir', '--')}",
        f"风力: {now.get('windScale', '--')}级",
        f"风速: {now.get('windSpeed', '--')}km/h",
        f"湿度: {now.get('humidity', '--')}%",
        f"气压: {now.get('pressure', '--')}hPa",
        f"能见度: {now.get('vis', '--')}km",
        f"更新时间: {data.get('updateTime', '--')}",
    ]
    
    return "\n".join(lines)


def format_forecast(data: dict, city_name: str = "") -> str:
    """格式化天气预报输出"""
    if not API_KEY:
        return """错误: 未设置 API Key

请通过以下方式之一设置你的和风天气 API Key:

方式 1 - 设置环境变量:
  Windows: set XTC_WEATHER_API_KEY=你的APIKey
  Linux/Mac: export XTC_WEATHER_API_KEY=你的APIKey

方式 2 - 在 OpenClaw 配置文件中设置:
  在 ~/.openclaw/config.json 中添加:
  {
    "env": {
      "XTC_WEATHER_API_KEY": "你的APIKey"
    }
  }

获取 API Key: https://dev.qweather.com/"""
    
    if "error" in data:
        return f"查询失败: {data['error']}"
    
    if data.get("code") != "200":
        return f"查询失败: API 返回错误码 {data.get('code')}"
    
    daily = data.get("daily", [])
    if not daily:
        return "暂无预报数据"
    
    city_str = f"[{city_name}] " if city_name else ""
    lines = [f"{city_str}天气预报"]
    
    for day in daily:
        lines.append(
            f"\n{day.get('fxDate', '--')}:"
            f" 白天{day.get('textDay', '--')}({day.get('tempMax', '--')}°C) / "
            f"夜间{day.get('textNight', '--')}({day.get('tempMin', '--')}°C) "
            f"{day.get('windDirDay', '--')}{day.get('windScaleDay', '--')}级"
        )
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="查询天气信息")
    parser.add_argument("city", help="城市名称或 Location ID")
    parser.add_argument("-t", "--type", choices=["now", "forecast", "all"], 
                       default="now", help="查询类型: now(实时), forecast(预报), all(全部)")
    parser.add_argument("-d", "--days", type=int, choices=[3, 7, 10, 15, 30], 
                       default=3, help="预报天数")
    parser.add_argument("--raw", action="store_true", help="输出原始 JSON")
    
    args = parser.parse_args()
    
    # 判断输入的是城市名还是 Location ID
    # Location ID 是纯数字，城市名是中文或其他字符
    if args.city.isdigit():
        location = args.city
        city_name = ""
    else:
        location = lookup_location(args.city)
        if not location:
            print(f"未找到城市: {args.city}", file=sys.stderr)
            sys.exit(1)
        city_name = args.city
    
    if args.type == "now" or args.type == "all":
        result = get_weather_now(location)
        if args.raw:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_weather_now(result, city_name))
    
    if args.type == "forecast" or args.type == "all":
        if args.type == "all":
            print("\n" + "="*40 + "\n")
        result = get_weather_forecast(location, args.days)
        if args.raw:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_forecast(result, city_name))


if __name__ == "__main__":
    main()
