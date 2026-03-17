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

# 技能源目录 - 本地工作区
SKILLS_SOURCE_DIR = r'C:\Users\luzhe\.openclaw\workspace-main\skills'

# 各分类的源目录
SOURCE_DIRS = {
    'public': r'C:\Users\luzhe\.openclaw\skills',  # 全局技能库
    'shared': r'C:\Users\luzhe\.openclaw\workspace-feishu-agent\skills',  # feishu-agent
    'private': r'C:\Users\luzhe\.openclaw\workspace-main\skills',  # general-agent
}

# 分类配置文件路径
CATEGORIES_FILE = Path(__file__).parent.parent / 'skill-categories.json'

# 推送历史记录文件
PUSH_HISTORY_FILE = Path(__file__).parent.parent / 'push_history.json'


def load_push_history() -> dict:
    """加载推送历史记录"""
    if PUSH_HISTORY_FILE.exists():
        with open(PUSH_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_push_history(history: dict):
    """保存推送历史记录"""
    with open(PUSH_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def record_push(skill_name: str, target: str):
    """记录技能推送时间"""
    history = load_push_history()
    key = f"{skill_name}->{target}"
    history[key] = {
        'skill': skill_name,
        'target': target,
        'pushed_at': datetime.now().isoformat()
    }
    save_push_history(history)


def get_last_push_time(skill_name: str, target: str) -> str:
    """获取技能上次推送时间"""
    history = load_push_history()
    key = f"{skill_name}->{target}"
    return history.get(key, {}).get('pushed_at')


from datetime import datetime


def load_skill_categories() -> dict:
    """加载技能分类配置"""
    if CATEGORIES_FILE.exists():
        with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_skill_target(skill_name: str) -> str:
    """根据技能分类获取目标路径
    
    Returns:
        'public': 推送到全局技能库
        'shared': 推送到 feishu-agent
        'private': 推送到 general-agent
        None: 未找到分类
    """
    categories = load_skill_categories()
    cats = categories.get('categories', {})
    
    for cat_name, cat_info in cats.items():
        if skill_name in cat_info.get('skills', []):
            return cat_name
    
    return None


def push_all_by_category(target: str = None) -> list:
    """根据发布范围推送所有技能
    
    Args:
        target: 指定目标 (feishu-agent/general-agent)，如果不指定则根据分类推送
    
    Returns:
        推送结果列表
    """
    categories = load_skill_categories()
    cats = categories.get('categories', {})
    
    results = []
    
    # 如果指定了目标，只推送属于该目标的技能
    if target == 'feishu-agent':
        # shared -> feishu-agent
        skills = cats.get('shared', {}).get('skills', [])
        actual_target = 'feishu-agent'
    elif target == 'general-agent':
        # private -> general-agent
        skills = cats.get('private', {}).get('skills', [])
        actual_target = 'general-agent'
    elif target == 'public':
        # public -> 全局技能库
        skills = cats.get('public', {}).get('skills', [])
        actual_target = 'public'
    else:
        # 推送所有分类
        skills = []
        for cat_info in cats.values():
            skills.extend(cat_info.get('skills', []))
        actual_target = None
    
    for skill_name in skills:
        print(f"\n=== 推送 {skill_name} ===")
        result = push_skill(skill_name, actual_target if actual_target else None)
        results.append({'skill': skill_name, 'result': result, 'category': actual_target})
    
    return results


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
    # public 目标：全局技能库
    if target == 'public':
        global_skills = r'C:\Users\luzhe\.openclaw\skills'
        return os.path.exists(global_skills)
    
    if target not in AGENT_WORKSPACES:
        print(f"未知的目标Agent: {target}")
        print(f"支持的目标: {', '.join(AGENT_WORKSPACES.keys())}, public")
        return False
    
    workspace = AGENT_WORKSPACES[target]
    return os.path.exists(workspace)


def get_latest_mtime(skill_path: Path) -> float:
    """获取技能目录下所有文件的最大修改时间"""
    latest = 0
    if skill_path.exists() and skill_path.is_dir():
        for file_path in skill_path.rglob('*'):
            if file_path.is_file():
                mtime = file_path.stat().st_mtime
                if mtime > latest:
                    latest = mtime
    return latest


def compare_skill_versions(source_path: Path, target_path: Path, skill_name: str = None, target: str = None, use_history: bool = True) -> dict:
    """
    比较源技能和目标技能的版本
    
    比较优先级：
    1. 如果有推送历史，比较源技能更新时间 vs 上次推送时间
    2. 否则比较源技能 vs 目标技能的更新时间
    
    Returns:
        {
            'needs_push': True/False,
            'source_time': float,
            'target_time': float,
            'reason': str
        }
    """
    source_time = get_latest_mtime(source_path)
    
    # 如果目标不存在，需要推送
    if not target_path.exists():
        return {
            'needs_push': True,
            'source_time': source_time,
            'target_time': 0,
            'reason': '目标技能不存在'
        }
    
    # 如果不使用历史时间比较，直接比较源和目标的文件时间
    if not use_history:
        target_time = get_latest_mtime(target_path)
        if source_time > target_time:
            return {
                'needs_push': True,
                'source_time': source_time,
                'target_time': target_time,
                'reason': f'源文件比目标文件新，强制推送'
            }
        else:
            return {
                'needs_push': False,
                'source_time': source_time,
                'target_time': target_time,
                'reason': f'目标文件已是最新'
            }
    
    # 优先使用上次推送时间进行比较（仅批量推送时启用）
    if use_history and skill_name and target:
        last_push_time_str = get_last_push_time(skill_name, target)
        if last_push_time_str:
            try:
                last_push_time = datetime.fromisoformat(last_push_time_str).timestamp()
                if source_time > last_push_time:
                    return {
                        'needs_push': True,
                        'source_time': source_time,
                        'target_time': last_push_time,
                        'reason': f'源技能在上次推送后有更新'
                    }
                else:
                    return {
                        'needs_push': False,
                        'source_time': source_time,
                        'target_time': last_push_time,
                        'reason': f'源技能自上次推送后无更新'
                    }
            except:
                pass
    
    # 回退到比较目标技能时间
    target_time = get_latest_mtime(target_path)
    
    if source_time > target_time:
        return {
            'needs_push': True,
            'source_time': source_time,
            'target_time': target_time,
            'reason': f'源技能更新 (源: {source_time:.0f} > 目标: {target_time:.0f})'
        }
    else:
        return {
            'needs_push': False,
            'source_time': source_time,
            'target_time': target_time,
            'reason': f'目标技能已是最新'
        }


def push_skill(skill_name: str, target: str = None, force: bool = False, use_history: bool = True) -> bool:
    """推送技能到目标 Agent
    
    Args:
        skill_name: 技能名称
        target: 目标 Agent
        force: 是否强制推送（忽略版本比较）
    """
    
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
    
    # 4. 确定目标路径
    source_path = Path(SKILLS_SOURCE_DIR) / skill_name
    
    if target == 'public':
        # 推送到全局技能库
        target_skills_dir = Path(r'C:\Users\luzhe\.openclaw\skills') / skill_name
    else:
        target_workspace = AGENT_WORKSPACES[target]
        target_skills_dir = Path(target_workspace) / 'skills' / skill_name
    
    # 5. 比较版本（除非强制推送）
    
    if not force:
        print(f"📋 比较技能版本...")
        version_info = compare_skill_versions(source_path, target_skills_dir, skill_name, target, use_history)
        print(f"   {version_info['reason']}")
        
        if not version_info['needs_push']:
            print(f"⏭️  跳过推送（目标已是最新）")
            return None  # 返回 None 表示无需推送
    
    # 5. 复制技能到目标 workspace/skills/
    print(f"📋 复制技能到目标 workspace...")
    
    # 如果目标 skills 目录已存在，先删除
    if target_skills_dir.exists():
        shutil.rmtree(target_skills_dir)
    
    # 复制整个技能目录
    shutil.copytree(source_path, target_skills_dir)
    print(f"✅ 技能已复制到: {target_skills_dir}")
    
    # 记录推送时间
    if target:
        record_push(skill_name, target)
        print(f"📝 已记录推送时间")
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description='推送技能到目标 Agent')
    parser.add_argument('skill_name', nargs='?', help='技能名称（可选，不指定则根据分类推送）')
    parser.add_argument('target', nargs='?', help='目标 Agent（可选）')
    parser.add_argument('-f', '--force', action='store_true', help='强制推送（忽略版本比较）')
    parser.add_argument('-a', '--all', action='store_true', help='推送所有技能')
    
    args = parser.parse_args()
    
    # 推送所有技能
    if args.all:
        target = args.target if args.target else None
        print(f"🚀 开始推送所有技能到指定目标...")
        print("=" * 50)
        
        results = push_all_by_category(target)
        
        pushed = sum(1 for r in results if r['result'])
        skipped = sum(1 for r in results if r['result'] is None)
        print(f"\n✅ 推送完成: {pushed} 成功, {skipped} 跳过")
        return
    
    # 不指定技能名称，根据分类推送到对应目标
    if not args.skill_name:
        target = args.target if args.target else None
        print(f"🚀 根据发布范围推送所有技能...")
        print("=" * 50)
        
        results = []
        
        # 推送到全局技能库 (public)
        print("\n>>> 推送到全局技能库 (公共技能)...")
        public_results = push_all_by_category('public')
        
        # 推送到 feishu-agent (shared)
        print("\n>>> 推送到 feishu-agent (共享技能)...")
        shared_results = push_all_by_category('feishu-agent')
        
        # 按分类统计 - 只显示公共技能和共享技能
        public_pushed = [r['skill'] for r in public_results if r['result']]
        public_skipped = [r['skill'] for r in public_results if r['result'] is None]
        shared_pushed = [r['skill'] for r in shared_results if r['result']]
        shared_skipped = [r['skill'] for r in shared_results if r['result'] is None]
        
        print("\n" + "=" * 50)
        print("📊 推送结果汇总")
        print("=" * 50)
        
        # 公共技能
        if public_pushed:
            print(f"\n✅ 公共技能已更新 ({len(public_pushed)} 个):")
            for s in public_pushed:
                print(f"   - {s}")
        
        if public_skipped:
            print(f"\n⏭️ 公共技能跳过 ({len(public_skipped)} 个):")
            for s in public_skipped[:5]:
                print(f"   - {s}")
            if len(public_skipped) > 5:
                print(f"   ... 等共 {len(public_skipped)} 个")
        
        # 共享技能
        if shared_pushed:
            print(f"\n✅ 共享技能已更新 ({len(shared_pushed)} 个):")
            for s in shared_pushed:
                print(f"   - {s}")
        
        if shared_skipped:
            print(f"\n⏭️ 共享技能跳过 ({len(shared_skipped)} 个):")
            for s in shared_skipped[:5]:
                print(f"   - {s}")
            if len(shared_skipped) > 5:
                print(f"   ... 等共 {len(shared_skipped)} 个")
        
        return
    
    skill_name = args.skill_name
    target = args.target
    
    # 如果指定了技能但没指定目标，根据分类自动确定目标
    if not target:
        cat = get_skill_target(skill_name)
        if cat == 'public':
            target = 'public'
        elif cat == 'shared':
            target = 'feishu-agent'
        elif cat == 'private':
            target = 'general-agent'
        else:
            print(f"⚠️  未找到技能分类，默认推送到 general-agent")
            target = 'general-agent'
        print(f"📌 根据分类 '{cat}' 自动确定目标: {target}")
    
    print(f"🚀 开始推送技能 '{skill_name}' 到 '{target}'")
    print("=" * 50)
    
    try:
        # 指定技能名称时，强制推送（不检查版本）
        result = push_skill(skill_name, target, force=True, use_history=False)
        
        if result is None:
            # 无需推送
            print("\n⏭️ 推送已跳过")
        elif result and isinstance(result, dict):
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
