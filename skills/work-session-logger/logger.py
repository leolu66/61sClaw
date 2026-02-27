#!/usr/bin/env python3
"""
工作会话日志记录器
用于自动生成结构化的工作日志文件
"""

import os
import re
from datetime import datetime
from pathlib import Path


def get_next_log_filename(summary: str = "", log_dir: str = r"D:\\anthropic\\工作日志") -> tuple:
    """
    生成下一个工作日志文件名
    
    Args:
        summary: 简短概述（2-4个关键词，用+连接）
        log_dir: 日志存放目录
    
    Returns:
        (filepath, filename): 完整路径和文件名
    """
    # 确保目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 扫描现有文件，找到当天的最大序号
    max_seq = 0
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.startswith(today) and filename.endswith('.md'):
                try:
                    parts = filename.replace('.md', '').split('-')
                    if len(parts) >= 4:
                        seq = int(parts[3])
                        max_seq = max(max_seq, seq)
                except (ValueError, IndexError):
                    continue
    
    # 生成新序号（3位数字，补零）
    next_seq = max_seq + 1
    
    # 清理概述字符串，确保文件名安全
    if summary:
        # 移除非法字符
        safe_summary = re.sub(r'[\\/*?:"<>|]', '', summary)
        # 空格替换为+
        safe_summary = safe_summary.replace(' ', '+')
        # 限制长度，避免文件名过长
        if len(safe_summary) > 50:
            safe_summary = safe_summary[:50]
        filename = f"{today}-{next_seq:03d}-{safe_summary}.md"
    else:
        filename = f"{today}-{next_seq:03d}.md"
    
    filepath = os.path.join(log_dir, filename)
    return filepath, filename, next_seq


def generate_log_template(
    seq: int,
    summary: str,
    start_time: str = None,
    end_time: str = None,
    tasks: list = None,
    problems: list = None,
    decisions: list = None,
    notes: str = None
) -> str:
    """
    生成日志内容模板
    
    Args:
        seq: 日志序号
        summary: 工作概述
        start_time: 开始时间 (HH:MM格式)
        end_time: 结束时间 (HH:MM格式)
        tasks: 任务列表
        problems: 问题列表
        decisions: 决策列表
        notes: 备注
    
    Returns:
        日志内容字符串
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    if not start_time:
        start_time = now.strftime("%H:%M")
    if not end_time:
        end_time = now.strftime("%H:%M")
    
    # 计算时长
    try:
        start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
        duration = end_dt - start_dt
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        duration_str = f"{hours}小时{minutes}分钟"
    except:
        duration_str = "未知"
    
    # 构建任务部分
    tasks_section = ""
    if tasks:
        for i, task in enumerate(tasks, 1):
            task_name = task.get('name', f'任务{i}')
            description = task.get('description', '')
            process = task.get('process', [])
            tools = task.get('tools', [])
            
            process_str = '\n'.join([f"{j+1}. {step}" for j, step in enumerate(process)]) if process else "1. 完成"
            tools_str = '\n'.join([f"- `{tool['name']}`：{tool['purpose']}" for tool in tools]) if tools else "- 未使用特定工具"
            
            tasks_section += f"""
### 任务{i}：{task_name}

**描述**：{description}

**执行过程**：
{process_str}

**使用工具/技能**：
{tools_str}

"""
    else:
        tasks_section = "### 任务1：完成工作内容\n\n**描述**：本次会话的主要工作内容\n\n**执行过程**：\n1. 步骤一\n2. 步骤二\n\n"
    
    # 构建问题部分
    problems_section = ""
    if problems:
        problems_section = "| 问题描述 | 原因分析 | 解决方案 | 结果 |\n|---------|---------|---------|------|\n"
        for p in problems:
            problems_section += f"| {p.get('desc', '-')} | {p.get('cause', '-')} | {p.get('solution', '-')} | {p.get('result', '已解决')} |\n"
    else:
        problems_section = "| 问题描述 | 原因分析 | 解决方案 | 结果 |\n|---------|---------|---------|------|\n| - | - | - | - |\n"
    
    # 构建决策部分
    decisions_section = ""
    if decisions:
        for i, d in enumerate(decisions, 1):
            decisions_section += f"- **决策{i}**：{d}\n"
    else:
        decisions_section = "- 无重大决策\n"
    
    # 构建备注
    notes_section = notes if notes else "- 无\n"
    
    template = f"""# 工作日志 #{seq:03d}

## 基本信息

| 项目 | 内容 |
|------|------|
| 日志编号 | #{seq:03d} |
| 日期 | {date_str} |
| 开始时间 | {start_time} |
| 结束时间 | {end_time} |
| 会话时长 | {duration_str} |

## 工作内容概述

{summary}

## 完成的任务

{tasks_section}
## 关键决策与成果

{decisions_section}
## 遇到的问题与解决方案

{problems_section}
## 备注

{notes_section}---

*日志生成时间：{now.strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    return template


def create_log(
    summary: str,
    log_dir: str = r"D:\\anthropic\\工作日志",
    start_time: str = None,
    end_time: str = None,
    tasks: list = None,
    problems: list = None,
    decisions: list = None,
    notes: str = None
) -> str:
    """
    创建并保存工作日志
    
    Args:
        summary: 简短概述（2-4个关键词，用+连接）
        log_dir: 日志存放目录
        start_time: 开始时间 (HH:MM)
        end_time: 结束时间 (HH:MM)
        tasks: 任务列表
        problems: 问题列表
        decisions: 决策列表
        notes: 备注
    
    Returns:
        生成的文件路径
    """
    # 生成文件名
    filepath, filename, seq = get_next_log_filename(summary, log_dir)
    
    # 生成日志内容
    content = generate_log_template(
        seq=seq,
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        tasks=tasks,
        problems=problems,
        decisions=decisions,
        notes=notes
    )
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


# 示例用法
if __name__ == '__main__':
    # 示例：创建一个测试日志
    filepath = create_log(
        summary="修复MCP+访问邮件+写日志",
        start_time="09:30",
        end_time="10:45",
        tasks=[
            {
                'name': '修复MCP连接问题',
                'description': '用户反映MCP服务器无法连接，需要诊断并修复',
                'process': [
                    '检查MCP配置文件，发现端口配置错误',
                    '修改配置文件中的端口号',
                    '重启MCP服务，验证连接正常'
                ],
                'tools': [
                    {'name': 'ReadFile', 'purpose': '读取配置文件'},
                    {'name': 'StrReplaceFile', 'purpose': '修改配置'},
                    {'name': 'Shell', 'purpose': '重启服务'}
                ]
            }
        ],
        problems=[
            {
                'desc': 'MCP连接超时',
                'cause': '端口被占用',
                'solution': '修改配置文件，更换端口',
                'result': '已解决'
            }
        ],
        decisions=[
            '将MCP服务端口从8080改为3000，避免与其他服务冲突'
        ],
        notes='后续需要监控MCP服务稳定性'
    )
    
    print(f"日志已创建: {filepath}")
