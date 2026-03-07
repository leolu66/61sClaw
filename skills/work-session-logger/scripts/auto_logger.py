#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作会话日志记录器 V6
按任务粒度总结
"""
import os
import json
import re
import io
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# 核心任务关键词
CORE_TASKS = [
    '技能分类', '技能推送', '技能清理', 'OC_XBot', 
    '法定假日', '工作日志', '模型配置', 'Cron任务'
]


def get_workspace_dir():
    """获取当前工作区根目录"""
    # __file__ = skills/work-session-logger/scripts/auto_logger.py
    # 需要向上4层才能到达 workspace-main
    return Path(__file__).parent.parent.parent.parent


def get_all_sessions():
    sessions_dir = Path(os.path.expanduser("~/.openclaw/agents"))
    all_sessions = []
    for agent_dir in sessions_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        sessions_file = agent_dir / "sessions" / "sessions.json"
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, info in data.items():
                        updated_at = info.get('updatedAt', 0)
                        all_sessions.append((key, info, updated_at, agent_dir.name))
            except:
                pass
    all_sessions.sort(key=lambda x: x[2], reverse=True)
    return all_sessions


def get_current_agent_session():
    sessions = get_all_sessions()
    if sessions:
        return sessions[0]
    return None


def read_messages(session_file: Path, limit: int = 50):
    if not session_file.exists():
        return []
    messages = []
    # 过滤掉包含脚本输出的污染消息
    skip_patterns = ['[INFO]', '[OK]', '[ERROR]', 'auto_logger.py', 'Successfully replaced', 'Get-ChildItem', 'Traceback']
    
    with open(session_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[-limit:]:
            try:
                data = json.loads(line)
                msg = data.get('message', {})
                if msg:
                    # 检查是否包含污染关键词
                    msg_str = json.dumps(msg, ensure_ascii=False)
                    if any(k in msg_str for k in skip_patterns):
                        continue
                    messages.append({'message': msg})
            except:
                pass
    return messages


def extract_tasks(messages: list) -> list:
    """提取核心任务关键词"""
    tasks = []
    all_text = ''
    
    for msg in messages:
        # 消息结构: {message: {role, content, ...}}
        message = msg.get('message', {})
        content = message.get('content', [])
        
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    text = c.get('text', '') or c.get('thinking', '')
                    if text:
                        all_text += text + ' '
    
    # 只匹配核心任务
    for task in CORE_TASKS:
        if task in all_text:
            if task not in tasks:
                tasks.append(task)
    
    return tasks


def get_next_filename(log_dir: str, tasks: list) -> str:
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    max_seq = 0
    for f in os.listdir(log_dir):
        if f.startswith(today) and f.endswith('.md'):
            try:
                seq = int(f.split('-')[3][:3])
                max_seq = max(max_seq, seq)
            except:
                pass
    
    next_seq = max_seq + 1
    
    if tasks:
        # 最多显示3个任务，后面加"等"表示更多
        if len(tasks) > 3:
            summary = '、'.join(tasks[:3]) + '等'
        else:
            summary = '、'.join(tasks)
        summary = summary[:25]
    else:
        summary = '会话工作'
    
    summary = re.sub(r'[\\/*?:"<>|]', '', summary).replace(' ', '+')
    filename = f"{today}-{next_seq:03d}-{summary}.md"
    return os.path.join(log_dir, filename)


def clean_message_text(text: str) -> str:
    """清理消息文本，过滤系统元数据和日志输出"""
    import re
    # 移除 ANSI 转义序列 [32;1m 等
    text = re.sub(r'\[(\d+(;\d+)*)m', '', text)
    # 移除 JSON 元数据块
    text = re.sub(r'\{[\s\S]*?"message_id"[\s\S]*?\}', '', text)
    text = re.sub(r'Conversation info.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'Sender.*?```', '', text, flags=re.DOTALL)
    # 移除时间戳格式 [Sat 2026-03-07 19:25 GMT+8]
    text = re.sub(r'\[.*?GMT.*?\]', '', text)
    # 移除日志输出 [INFO] [OK] [ERROR] 等
    text = re.sub(r'\[(?:INFO|OK|ERROR|WARN|Debug)\].*?(?:\n|$)', '', text)
    # 移除 Traceback 错误堆栈
    text = re.sub(r'Traceback.*', '', text, flags=re.DOTALL)
    # 移除 === 分隔符
    text = re.sub(r'={3,}.*?={3,}', '', text, flags=re.DOTALL)
    # 移除 # 工作日志 标题和表格
    text = re.sub(r'#.*?工作日志.*?\n', '', text)
    text = re.sub(r'\|.*?\|.*?\n', '', text)
    # 移除文件路径
    text = re.sub(r'C:\\\\.*?\.py', '', text)
    text = re.sub(r'Get-ChildItem.*', '', text)
    text = re.sub(r'Select-String.*', '', text)
    # 移除 Keys: 等调试信息
    text = re.sub(r'Keys:.*', '', text)
    # 移除 python 相关
    text = re.sub(r'python.*', '', text)
    # 移除 json 数据块
    text = re.sub(r'json\s*\{', '{', text)
    # 移除 unicode 错误
    text = re.sub(r'UnicodeEncodeError.*', '', text)
    # 移除多余标记
    text = re.sub(r'---', '', text)
    # 移除 emoji 装饰和多余符号
    text = re.sub(r'🎨|💼|📧|📂|🤔|🎯|🧹|📊|✂️|📦|💡|🌤️|⏰|🎮|♟️|📝', '', text)
    # 移除多余的换行
    text = re.sub(r'\n+', ' ', text).strip()
    return text


def extract_task_details(messages: list) -> list:
    """从消息中提取任务详情"""
    tasks = []
    
    for msg in messages:
        # 消息结构: {type, id, parentId, timestamp, message}
        message = msg.get('message', {})
        role = message.get('role', '')
        content = message.get('content', [])
        
        # 提取所有文本内容
        texts = []
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    text = c.get('text', '')
                    if text:
                        texts.append(text)
        
        # 如果没有内容，继续
        if not texts:
            continue
            
        # 合并所有文本
        full_text = ' '.join(texts)
        cleaned = clean_message_text(full_text)
        
        # 跳过太短或包含日志/代码特征的
        skip_patterns = ['[INFO]', '[OK]', '[ERROR]', 'Traceback', 'python', 'File "']
        if any(p in cleaned for p in skip_patterns):
            continue
        if 10 < len(cleaned) < 400:
            tasks.append(cleaned[:150])
    
    # 如果没有提取到，返回默认
    if not tasks:
        return ["处理会话请求"]
    
    return tasks[:5]  # 最多5条


def generate_log_content(tasks: list, session_name: str, messages: list) -> str:
    """生成结构化日志内容"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    # 简化任务列表，只显示关键词
    task_list = ", ".join(tasks) if tasks else "常规会话任务"
    
    content = f"""# 工作日志

## 基本信息

| 项目 | 内容 |
|------|------|
| 日期 | {date_str} |
| 时间 | {time_str} |
| 会话 | {session_name} |

## 工作内容概述

本次会话的主要工作：{task_list}

## 完成的任务

### 任务1：{task_list}

**描述**：处理相关任务

## 关键决策与成果

- 无重大决策

## 遇到的问题与解决方案

| 问题描述 | 原因分析 | 解决方案 | 结果 |
|---------|---------|---------|------|
| - | - | - | - |

## 备注

- 无

---

*自动生成于 {now.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return content


def main():
    print("[INFO] Finding current agent session...")
    
    session = get_current_agent_session()
    if not session:
        print("[ERROR] No session found")
        return
    
    key, info, _, agent_name = session
    session_file = Path(info.get('sessionFile', ''))
    
    print(f"[INFO] Agent: {agent_name}")
    
    messages = read_messages(session_file, 30)
    print(f"[INFO] Got {len(messages)} messages")
    
    tasks = extract_tasks(messages)
    print(f"[INFO] Tasks: {tasks}")
    
    workspace_dir = get_workspace_dir()
    log_dir = str(workspace_dir / "logs" / "daily")
    filepath = get_next_filename(log_dir, tasks)
    
    content = generate_log_content(tasks, agent_name, messages)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Log saved: {filepath}")


if __name__ == '__main__':
    main()
