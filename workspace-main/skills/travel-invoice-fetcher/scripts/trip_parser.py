#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行程解析模块
支持从自然语言文本中提取行程信息
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TripSegment:
    """单段行程"""
    departure_city: str
    destination_city: str
    start_date: datetime
    end_date: datetime
    transport_mode: Optional[str] = None
    form_no: Optional[str] = None  # FOL申请单编号
    
    @property
    def folder_name(self) -> str:
        """生成目录名: 出发地-目的地-MMDD-MMDD"""
        start_str = self.start_date.strftime("%m%d")
        end_str = self.end_date.strftime("%m%d")
        return f"{self.departure_city}-{self.destination_city}-{start_str}-{end_str}"


class TripParser:
    """行程解析器"""
    
    # 城市名称映射（常见简称）
    CITY_ALIASES = {
        "北京": "北京",
        "京城": "北京",
        "上海": "上海",
        "魔都": "上海",
        "广州": "广州",
        "羊城": "广州",
        "深圳": "深圳",
        "南京": "南京",
        "金陵": "南京",
        "杭州": "杭州",
        "成都": "成都",
        "重庆": "重庆",
        "西安": "西安",
        "武汉": "武汉",
        "天津": "天津",
        "苏州": "苏州",
        "长沙": "长沙",
        "郑州": "郑州",
        "青岛": "青岛",
        "大连": "大连",
        "厦门": "厦门",
        "宁波": "宁波",
        "无锡": "无锡",
    }
    
    # 交通方式关键词
    TRANSPORT_KEYWORDS = {
        "高铁": "高铁",
        "动车": "高铁",
        "火车": "火车",
        "列车": "火车",
        "飞机": "飞机",
        "航班": "飞机",
        "航空": "飞机",
        "汽车": "汽车",
        "大巴": "汽车",
    }
    
    def __init__(self, year: Optional[int] = None):
        """
        初始化解析器
        
        Args:
            year: 默认年份，如果不提供则使用当前年份
        """
        self.year = year or datetime.now().year
    
    def parse(self, text: str) -> List[TripSegment]:
        """
        解析行程文本
        
        Args:
            text: 用户输入的行程描述
            
        Returns:
            TripSegment 列表
        """
        text = text.strip()
        segments = []
        
        # 检测是否有全局交通方式（如"都是飞机"）
        global_transport = self._extract_global_transport(text)
        
        # 尝试按空格分割多段行程（每段包含完整的日期和城市信息）
        # 匹配模式: X月X日到X月X日，城市A到城市B，交通工具
        trip_pattern = r'(\d{1,2}月\d{1,2}日[到至~]\d{1,2}月\d{1,2}日，[^，]+?到[^，]+(?:，[^ ]+)?)'
        trip_matches = re.findall(trip_pattern, text)
        
        if len(trip_matches) > 1:
            # 找到多段行程
            for trip_text in trip_matches:
                segment = self._parse_single_segment(trip_text, global_transport)
                if segment:
                    segments.append(segment)
            if segments:
                return segments
        
        # 尝试用逗号、分号分隔
        parts = re.split(r'[,，;；]', text)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # 跳过纯交通方式描述
                if self._is_transport_only(part):
                    continue
                segment = self._parse_single_segment(part, global_transport)
                if segment:
                    segments.append(segment)
            if segments:
                return segments
        
        # 单段行程解析
        segment = self._parse_single_segment(text, global_transport)
        if segment:
            segments.append(segment)
        
        return segments
    
    def _parse_single_segment(
        self, 
        text: str, 
        default_transport: Optional[str] = None
    ) -> Optional[TripSegment]:
        """解析单段行程"""
        
        # 提取日期范围
        date_range = self._extract_date_range(text)
        if not date_range:
            return None
        
        start_date, end_date = date_range
        
        # 提取城市
        cities = self._extract_cities(text)
        if len(cities) < 2:
            return None
        
        departure_city = cities[0]
        destination_city = cities[1]
        
        # 提取交通方式
        transport = self._extract_transport(text) or default_transport
        
        return TripSegment(
            departure_city=departure_city,
            destination_city=destination_city,
            start_date=start_date,
            end_date=end_date,
            transport_mode=transport
        )
    
    def _extract_date_range(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """提取日期范围"""
        
        # 模式1: X月X日到X月X日 / X月X日-X月X日 / X月X日~X月X日
        pattern1 = r'(\d{1,2})月(\d{1,2})日?\s*[-到至~]\s*(\d{1,2})月(\d{1,2})日?'
        match = re.search(pattern1, text)
        if match:
            start_month, start_day, end_month, end_day = map(int, match.groups())
            start_date = datetime(self.year, start_month, start_day)
            end_date = datetime(self.year, end_month, end_day)
            return (start_date, end_date)
        
        # 模式2: X月X日-X日（同月简写）
        pattern2 = r'(\d{1,2})月(\d{1,2})日?\s*[-到至~]\s*(\d{1,2})日?'
        match = re.search(pattern2, text)
        if match:
            month, start_day, end_day = map(int, match.groups())
            start_date = datetime(self.year, month, start_day)
            end_date = datetime(self.year, month, end_day)
            return (start_date, end_date)
        
        # 模式3: YYYY-MM-DD 到 YYYY-MM-DD
        pattern3 = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s*[-到至~]\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        match = re.search(pattern3, text)
        if match:
            groups = list(map(int, match.groups()))
            start_date = datetime(groups[0], groups[1], groups[2])
            end_date = datetime(groups[3], groups[4], groups[5])
            return (start_date, end_date)
        
        # 模式4: MM-DD 到 MM-DD
        pattern4 = r'(\d{1,2})[-/](\d{1,2})\s*[-到至~]\s*(\d{1,2})[-/](\d{1,2})'
        match = re.search(pattern4, text)
        if match:
            start_month, start_day, end_month, end_day = map(int, match.groups())
            start_date = datetime(self.year, start_month, start_day)
            end_date = datetime(self.year, end_month, end_day)
            return (start_date, end_date)
        
        # 模式5: 单个日期（出发日期=结束日期）
        single_date = self._parse_single_date(text)
        if single_date:
            return (single_date, single_date)
        
        return None
    
    def _parse_single_date(self, text: str) -> Optional[datetime]:
        """解析单个日期"""
        
        # X月X日
        pattern1 = r'(\d{1,2})月(\d{1,2})日?'
        match = re.search(pattern1, text)
        if match:
            month, day = map(int, match.groups())
            return datetime(self.year, month, day)
        
        # YYYY-MM-DD
        pattern2 = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        match = re.search(pattern2, text)
        if match:
            year, month, day = map(int, match.groups())
            return datetime(year, month, day)
        
        # MM-DD
        pattern3 = r'(?<!\d)(\d{1,2})[-/](\d{1,2})(?!\d)'
        match = re.search(pattern3, text)
        if match:
            month, day = map(int, match.groups())
            return datetime(self.year, month, day)
        
        return None
    
    def _extract_cities(self, text: str) -> List[str]:
        """提取城市名称"""
        cities = []
        
        # 先尝试匹配 "X到Y" 或 "X至Y" 格式（明确的方向性）
        # 支持：广州到南京、广州市到南京市、广州至南京等
        direction_pattern = r'([\u4e00-\u9fa5]{2,10}?)\s*(?:到|至|去|前往)\s*([\u4e00-\u9fa5]{2,10}?)(?:市|县|区|省)?(?:[，,；;]|$)'
        match = re.search(direction_pattern, text)
        if match:
            departure = match.group(1).replace('市', '').replace('省', '')
            destination = match.group(2).replace('市', '').replace('省', '')
            return [departure, destination]
        
        # 按优先级匹配城市（原有逻辑）
        for city in sorted(self.CITY_ALIASES.keys(), key=len, reverse=True):
            if city in text and city not in cities:
                # 检查是否是其他词的一部分
                idx = text.find(city)
                if idx >= 0:
                    cities.append(self.CITY_ALIASES[city])
        
        # 去重并保持顺序
        seen = set()
        unique_cities = []
        for city in cities:
            if city not in seen:
                seen.add(city)
                unique_cities.append(city)
        
        return unique_cities
    
    def _extract_transport(self, text: str) -> Optional[str]:
        """提取交通方式"""
        for keyword, transport in self.TRANSPORT_KEYWORDS.items():
            if keyword in text:
                return transport
        return None
    
    def _extract_global_transport(self, text: str) -> Optional[str]:
        """提取全局交通方式（如"都是飞机"）"""
        pattern = r'都[是|用|坐|乘](.+?)[，,；;。]'
        match = re.search(pattern, text)
        if match:
            transport_text = match.group(1)
            return self._extract_transport(transport_text)
        
        # 检查句尾
        if text.endswith("都是飞机") or text.endswith("都是高铁"):
            return self._extract_transport(text[-4:])
        
        return None
    
    def _is_transport_only(self, text: str) -> bool:
        """检查是否仅为交通方式描述"""
        transport_only_patterns = [
            r'^都[是|用|坐|乘]',
            r'^[都全].*?[飞机高铁火车]',
        ]
        for pattern in transport_only_patterns:
            if re.search(pattern, text):
                return True
        return False


def test_parser():
    """测试解析器"""
    parser = TripParser(year=2025)
    
    test_cases = [
        "2月8日到3月16日，南京到北京，高铁",
        "3月1日-3月5日上海出差，3月10日-3月15日深圳出差，都是飞机",
        "2025-02-08到2025-03-16，南京到北京",
        "02-08到03-16，南京到北京，火车",
        "3月1日到5日上海出差，都是高铁",
    ]
    
    for text in test_cases:
        print(f"\n输入: {text}")
        segments = parser.parse(text)
        for seg in segments:
            print(f"  行程: {seg.departure_city} -> {seg.destination_city}")
            print(f"  日期: {seg.start_date.strftime('%Y-%m-%d')} 到 {seg.end_date.strftime('%Y-%m-%d')}")
            print(f"  交通: {seg.transport_mode or '未指定'}")
            print(f"  目录: {seg.folder_name}")


if __name__ == "__main__":
    test_parser()
