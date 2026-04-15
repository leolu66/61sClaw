#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOL 财务系统行程导入模块
从 FOL 系统获取"我的申请单"并转换为行程信息
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# 添加父目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from trip_parser import TripSegment


@dataclass
class FOLApplication:
    """FOL 申请单数据结构"""
    form_no: str           # 单号
    form_name: str         # 表单名称
    project: str           # 项目名称
    description: str       # 描述
    submit_time: str       # 提交时间
    status: str            # 单据状态
    # 行程详情字段
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    departure_city: Optional[str] = None
    destination_city: Optional[str] = None
    transport: Optional[str] = None


class FOLImporter:
    """FOL 行程导入器"""
    
    # 城市映射表（用于从描述中提取城市）
    CITY_KEYWORDS = {
        '北京': '北京',
        '上海': '上海',
        '广州': '广州',
        '深圳': '深圳',
        '南京': '南京',
        '杭州': '杭州',
        '成都': '成都',
        '重庆': '重庆',
        '西安': '西安',
        '武汉': '武汉',
        '天津': '天津',
        '苏州': '苏州',
        '长沙': '长沙',
    }
    
    def __init__(self):
        self.applications: List[FOLApplication] = []
    
    def parse_application_list(self, text_content: str) -> List[FOLApplication]:
        """
        从文本内容解析申请单列表
        
        Args:
            text_content: 从 FOL 系统获取的申请单列表文本
            
        Returns:
            FOLApplication 列表
        """
        applications = []
        
        # 解析表格行数据
        # 匹配模式: 序号 表单名称 单号 报销人 提单人 描述 项目名称 部门名称 单据金额 审核金额 核算体系名称 提交时间 单据状态 当前审批
        lines = text_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('表单名称'):
                continue
            
            # 尝试匹配申请单行
            # 格式: 1 国内差旅申请单 1-SQ12026002686 陆震 陆震 从北京到广州回驻地订票补单 集团市场拓展项目-联通 商业发展部 0.00 0.00 2026-03-10 16:43:29 完成
            parts = line.split()
            if len(parts) >= 10:
                try:
                    # 提取基本信息
                    form_no = self._extract_form_no(line)
                    form_name = self._extract_form_name(line)
                    project = self._extract_project(line)
                    description = self._extract_description(line)
                    submit_time = self._extract_submit_time(line)
                    status = self._extract_status(line)
                    
                    if form_no:
                        app = FOLApplication(
                            form_no=form_no,
                            form_name=form_name or '未知表单',
                            project=project or '未知项目',
                            description=description or '',
                            submit_time=submit_time or '',
                            status=status or '未知状态'
                        )
                        applications.append(app)
                except Exception as e:
                    print(f"⚠️ 解析行失败: {line[:50]}... - {e}")
                    continue
        
        return applications
    
    def _extract_form_no(self, line: str) -> Optional[str]:
        """提取单号"""
        # 匹配模式: 1-SQ12026002686
        match = re.search(r'(\d+-SQ\d+)', line)
        return match.group(1) if match else None
    
    def _extract_form_name(self, line: str) -> Optional[str]:
        """提取表单名称"""
        # 常见表单名称
        form_names = ['国内差旅申请单', '国际差旅申请单', '费用报销单', '借款单']
        for name in form_names:
            if name in line:
                return name
        return None
    
    def _extract_project(self, line: str) -> Optional[str]:
        """提取项目名称"""
        # 匹配模式: 集团市场拓展项目-联通
        match = re.search(r'(集团[^\s]+项目[^\s]*)', line)
        return match.group(1) if match else None
    
    def _extract_description(self, line: str) -> Optional[str]:
        """提取描述"""
        # 描述通常在部门名称之后，金额之前
        # 简化处理：提取单号后的中文字符串
        match = re.search(r'\d+-SQ\d+\s+\S+\s+\S+\s+([^\d]{3,30})\s+集团', line)
        return match.group(1).strip() if match else None
    
    def _extract_submit_time(self, line: str) -> Optional[str]:
        """提取提交时间"""
        # 匹配模式: 2026-03-10 16:43:29
        match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
        return match.group(1) if match else None
    
    def _extract_status(self, line: str) -> Optional[str]:
        """提取单据状态"""
        # 匹配状态: 完成、审批中、待提交等
        statuses = ['完成', '审批中', '待提交', '已驳回']
        for status in statuses:
            if status in line:
                return status
        return None
    
    def parse_application_detail(self, detail_text: str) -> Dict:
        """
        从申请单详情文本解析行程信息
        
        Args:
            detail_text: 申请单详情页面的文本内容
            
        Returns:
            行程信息字典
        """
        info = {
            'start_date': None,
            'end_date': None,
            'departure_city': None,
            'destination_city': None,
            'transport': None,
        }
        
        # 提取出发日期
        match = re.search(r'出发日期\s*[:：]\s*(\d{4}-\d{2}-\d{2})', detail_text)
        if match:
            info['start_date'] = match.group(1)
        
        # 提取结束日期
        match = re.search(r'结束日期\s*[:：]\s*(\d{4}-\d{2}-\d{2})', detail_text)
        if match:
            info['end_date'] = match.group(1)
        
        # 提取出发地
        match = re.search(r'出发地\s*[:：]\s*([^\s]+)', detail_text)
        if match:
            info['departure_city'] = match.group(1).replace('市', '')
        
        # 提取出差地
        match = re.search(r'出差地\s*[:：]\s*([^\s]+)', detail_text)
        if match:
            info['destination_city'] = match.group(1).replace('市', '')
        
        # 提取交通工具
        match = re.search(r'交通工具\s*[:：]\s*([^\s]+)', detail_text)
        if match:
            transport = match.group(1)
            # 标准化交通工具名称
            if '飞机' in transport:
                info['transport'] = '飞机'
            elif '火车' in transport or '高铁' in transport:
                info['transport'] = '火车'
            elif '汽车' in transport:
                info['transport'] = '汽车'
            else:
                info['transport'] = transport
        
        return info
    
    def to_trip_segment(self, app: FOLApplication, detail_info: Dict = None) -> Optional[TripSegment]:
        """
        将 FOL 申请单转换为 TripSegment
        
        Args:
            app: FOL 申请单
            detail_info: 详情信息（可选）
            
        Returns:
            TripSegment 或 None
        """
        if detail_info:
            # 使用详情信息
            start_date_str = detail_info.get('start_date')
            end_date_str = detail_info.get('end_date')
            departure = detail_info.get('departure_city')
            destination = detail_info.get('destination_city')
            transport = detail_info.get('transport')
        else:
            # 从描述中推断
            start_date_str, end_date_str = self._infer_dates(app.submit_time)
            departure, destination = self._infer_cities(app.description)
            transport = self._infer_transport(app.description)
        
        if not all([start_date_str, end_date_str, departure, destination]):
            return None
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            return TripSegment(
                departure_city=departure,
                destination_city=destination,
                start_date=start_date,
                end_date=end_date,
                transport_mode=transport,
                form_no=app.form_no
            )
        except Exception as e:
            print(f"⚠️ 转换行程失败: {e}")
            return None
    
    def _infer_dates(self, submit_time: str) -> Tuple[Optional[str], Optional[str]]:
        """从提交时间推断行程日期（简化处理）"""
        if not submit_time:
            return None, None
        
        try:
            # 提取日期部分
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', submit_time)
            if date_match:
                submit_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                # 假设行程在提交后1-7天
                start_date = submit_date.strftime('%Y-%m-%d')
                end_date = (submit_date + __import__('datetime').timedelta(days=5)).strftime('%Y-%m-%d')
                return start_date, end_date
        except:
            pass
        
        return None, None
    
    def _infer_cities(self, description: str) -> Tuple[Optional[str], Optional[str]]:
        """从描述中推断出发地和目的地"""
        if not description:
            return None, None
        
        # 匹配 "从X到Y" 模式
        match = re.search(r'从(\S+?)[到至](\S+)', description)
        if match:
            departure = match.group(1).replace('市', '').replace('省', '')
            destination = match.group(2).replace('市', '').replace('省', '')
            return departure, destination
        
        # 尝试匹配城市关键词
        cities_found = []
        for city in self.CITY_KEYWORDS.keys():
            if city in description:
                cities_found.append(self.CITY_KEYWORDS[city])
        
        if len(cities_found) >= 2:
            return cities_found[0], cities_found[1]
        
        return None, None
    
    def _infer_transport(self, description: str) -> Optional[str]:
        """从描述中推断交通工具"""
        if not description:
            return None
        
        if '飞机' in description or '航班' in description or '航空' in description:
            return '飞机'
        elif '高铁' in description or '动车' in description:
            return '高铁'
        elif '火车' in description:
            return '火车'
        
        return None


def test_importer():
    """测试导入器"""
    importer = FOLImporter()
    
    # 测试数据
    test_content = """
1 国内差旅申请单 1-SQ12026002686 陆震 陆震 从北京到广州回驻地订票补单 集团市场拓展项目-联通 商业发展部 0.00 0.00 2026-03-10 16:43:29 完成
2 国内差旅申请单 1-SQ12026002685 陆震 陆震 联通广院方案讨论和编写 集团市场拓展项目-联通 商业发展部 2,000.00 0.00 2026-03-10 16:41:00 完成
3 国内差旅申请单 1-SQ12026001948 陆震 陆震 首代工作 集团市场拓展项目-联通 商业发展部 480.00 0.00 2026-02-21 10:05:59 完成
"""
    
    apps = importer.parse_application_list(test_content)
    print(f"解析到 {len(apps)} 条申请单")
    
    for app in apps:
        print(f"\n单号: {app.form_no}")
        print(f"  项目: {app.project}")
        print(f"  描述: {app.description}")
        print(f"  时间: {app.submit_time}")
        
        # 转换为行程
        segment = importer.to_trip_segment(app)
        if segment:
            print(f"  行程: {segment.departure_city} -> {segment.destination_city}")
            print(f"  日期: {segment.start_date.strftime('%Y-%m-%d')} 至 {segment.end_date.strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    test_importer()
