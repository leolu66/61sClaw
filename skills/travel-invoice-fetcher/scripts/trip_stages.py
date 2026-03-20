# -*- coding: utf-8 -*-
from typing import Dict, List, Optional

LOCATION_MAP = {
    # 南京
    "家": {"city": "南京", "detail": "长阳花园/世纪花园", "type": "home"},
    "南京南站": {"city": "南京", "type": "high_speed_station"},
    "南京站": {"city": "南京", "type": "high_speed_station"},
    "禄口机场": {"city": "南京", "type": "airport"},
    
    # 北京
    "宿舍": {"city": "北京", "detail": "一品亦庄", "type": "dorm"},
    "公司": {"city": "北京", "detail": "丽泽天地", "metro": "西局站", "type": "office"},
    "北京南站": {"city": "北京", "type": "high_speed_station"},
    "大兴机场": {"city": "北京", "type": "airport"},
    "草桥站": {"city": "北京", "type": "metro_transfer"},
    "西局站": {"city": "北京", "type": "metro_station"},
}

def generate_trip_stages(departure_city: str, destination_city: str, transport: str = "高铁") -> Dict:
    if departure_city == "南京":
        dep_station = "南京南站"
    else:
        dep_station = f"{departure_city}站"
        
    if destination_city == "北京":
        dest_station = "北京南站"
        dest_metro = "草桥站"
        dest_dorm = "宿舍"
    else:
        dest_station = f"{destination_city}站"
        dest_metro = "地铁站"
        dest_dorm = f"宿舍"
    
    long_transport = "高铁" if "高铁" in transport or "火车" in transport else "飞机"
    
    outward = [
        {"stage": 1, "from": "家", "to": "地铁站", "transport": "打车"},
        {"stage": 2, "from": "地铁站", "to": dep_station, "transport": "地铁"},
        {"stage": 3, "from": dep_station, "to": dest_station, "transport": long_transport},
        {"stage": 4, "from": dest_station, "to": dest_metro, "transport": "地铁"},
        {"stage": 5, "from": dest_metro, "to": dest_dorm, "transport": "打车"},
    ]
    
    return_stages = [
        {"stage": 1, "from": dest_dorm, "to": dest_metro, "transport": "打车"},
        {"stage": 2, "from": dest_metro, "to": dest_station, "transport": "地铁"},
        {"stage": 3, "from": dest_station, "to": dep_station, "transport": long_transport},
        {"stage": 4, "from": dep_station, "to": "地铁站", "transport": "地铁"},
        {"stage": 5, "from": "地铁站", "to": "家", "transport": "打车"},
    ]
    
    return {
        "departure_city": departure_city,
        "destination_city": destination_city,
        "transport": transport,
        "outward": outward,
        "return": return_stages
    }

if __name__ == "__main__":
    import json
    result = generate_trip_stages("南京", "北京", "高铁")
    print(json.dumps(result, ensure_ascii=False, indent=2))
