#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能推送脚本 - 将指定技能推送到目标 Agent

用法:
    python push_skill.py <技能名称> <目标Agent>
    
示例:
    python push_skill.py holiday-checker feishu-agent
    python push_skill.py weather-skill general-agent
"""

import os
import sys
import shutil
import json
from pathlib import Path

# 设置 UTF-8 输出（Windows 控制台）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 目标 Agent 工作空间映射
AGENT_WORKSPACES = {
    'feishu-agent': r'C:\Users\luzhe\.openclaw\workspace-feishu-agent',
    'general-agent': r'C:\Users\luzhe\.openclaw\workspace-main',
    # Claude Code 预留，后面实现
    # 'claude-code': r'...'
}

# 技能源目录
SKILLS_SOURCE_DIR = r'C:\Users\luzhe\.openclaw\skills'


def load_skill_info(skill_name: str) -> dict:
    """读取技能的 SKILL.md 获取技能信息"""
    skill_path = Path(SKILLS_SOURCE_DIR) / skill_name / 'SKILL.md'
    
    if not skill_path.exists():
        raise FileNotFoundError(f"技能不存在: {skill_name}")
    
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单解析：提取 name 和 description
    info = {'name': skill_name, 'description': '', 'usage': ''}
    
    # 解析 YAML 头部
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_part = parts[1]
            # 提取 name
            for line in yaml_part.split('\n'):
                if line.startswith('name:'):
                    info['name'] = line.split(':', 1)[1].strip()
            # 提取 description (可能是多行，用 | 或 > )
            if 'description:' in yaml_part:
                desc_start = yaml_part.find('description:')
                # 找到 description 后面的内容
                desc_line = yaml_part[desc_start:].split('\n')[0]
                if '|' in desc_line or '>' in desc_line:
                    # 多行描述，提取到 --- 之前
                    desc_content_start = yaml_part.find('\n', desc_start)
                    desc_content_end = yaml_part.find('---', desc_start)
                    if desc_content_end == -1:
                        desc_content_end = len(yaml_part)
                    desc_text = yaml_part[desc_content_start:desc_content_end].strip()
                    # 清理缩进
                    lines = desc_text.split('\n')
                    cleaned_lines = [line.strip() for line in lines if line.strip()]
                    info['description'] = ' '.join(cleaned_lines)
                else:
                    # 单行描述
                    info['description'] = desc_line.split(':', 1)[1].strip()
    
    # 解析使用说明
    if '### 基本用法' in content:
        usage_start = content.find('### 基本用法')
        usage_section = content[usage_start:usage_start+500]
        if 'python scripts/' in usage_section:
            cmd_start = usage_section.find('python scripts/')
            cmd_end = usage_section.find('\n', cmd_start)
            info['usage'] = usage_section[cmd_start:cmd_end].strip()
    elif '```bash' in content:
        # 尝试从第一个 bash 代码块获取
        bash_start = content.find('```bash')
        if bash_start != -1:
            bash_end = content.find('```', bash_start + 6)
            bash_section = content[bash_start:bash_end]
            if 'python' in bash_section:
                for line in bash_section.split('\n'):
                    if 'python' in line and not line.strip().startswith('#'):
                        info['usage'] = line.strip()
                        break
    
    if not info['description']:
        info['description'] = '暂无描述'
    if not info['usage']:
        info['usage'] = f'请参考 SKILL.md 文件'
    
    return info


def check_skill_exists(skill_name: str) -> bool:
    """检查源技能是否存在"""
    skill_path = Path(SKILLS_SOURCE_DIR) / skill_name
    return skill_path.exists() and skill_path.is_dir()


def check_workspace_exists(target: str) -> bool:
    """检查目标 Agent workspace 是否存在"""
    if target not in AGENT_WORKSPACES:
        print(f"未知的目标Agent: {target}")
        print(f"支持的目标: {', '.join(AGENT_WORKSPACES.keys())}")
        return False
    
    workspace = AGENT_WORKSPACES[target]
    return os.path.exists(workspace)


def push_skill(skill_name: str, target: str) -> bool:
    """推送技能到目标 Agent"""
    
    # 1. 检查源技能是否存在
    print(f"📋 检查技能 '{skill_name}'...")
    if not check_skill_exists(skill_name):
        print(f"❌ 技能不存在: {skill_name}")
        return False
    print(f"✅ 技能存在")
    
    # 2. 检查目标 Agent workspace 是否存在
    print(f"📋 检查目标 workspace '{target}'...")
    if not check_workspace_exists(target):
        return False
    print(f"✅ Workspace 存在")
    
    # 3. Claude Code 预留
    if target == 'claude-code':
        print("⏳ Claude Code 推送功能开发中...")
        return False
    
    # 4. 复制技能到目标 workspace/skills/
    source_path = Path(SKILLS_SOURCE_DIR) / skill_name
    target_workspace = AGENT_WORKSPACES[target]
    target_skills_dir = Path(target_workspace) / 'skills' / skill_name
    
    print(f"📋 复制技能到目标 workspace...")
    
    # 如果目标 skills 目录已存在，先删除
    if target_skills_dir.exists():
        shutil.rmtree(target_skills_dir)
    
    # 复制整个技能目录
    shutil.copytree(source_path, target_skills_dir)
    print(f"✅ 技能已复制到: {target_skills_dir}")
    
    # 5. 返回技能信息（用于发送通知）
    skill_info = load_skill_info(skill_name)
    
    return skill_info


def send_notification(skill_info: dict, target: str):
    """发送通知到目标 Agent"""
    from datetime import datetime
    
    skill_name = skill_info['name']
    skill_description = skill_info['description']
    usage_instructions = skill_info['usage']
    
    message = f"""🎉 新技能推送！

技能名称：{skill_name}
功能说明：{skill_description}

使用方式：
{usage_instructions}

有问题随时问我～"""
    
    print(f"\n📤 通知消息内容:")
    print("-" * 40)
    print(message)
    print("-" * 40)
    
    # 注意：实际的 message 发送由主 Agent 完成，这里只打印
    # 如果需要自动发送，可以使用 openclaw 的 message 工具
    return message


def main():
    if len(sys.argv) != 3:
        print("用法: python push_skill.py <技能名称> <目标Agent>")
        print(f"支持的目標: {', '.join(AGENT_WORKSPACES.keys())}")
        sys.exit(1)
    
    skill_name = sys.argv[1]
    target = sys.argv[2]
    
    print(f"🚀 开始推送技能 '{skill_name}' 到 '{target}'")
    print("=" * 50)
    
    try:
        # 执行推送
        result = push_skill(skill_name, target)
        
        if result and isinstance(result, dict):
            # 发送通知
            send_notification(result, target)
            print("\n✅ 推送完成!")
        else:
            print("\n❌ 推送失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
