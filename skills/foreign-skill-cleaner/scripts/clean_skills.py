#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国外技能批量清理工具
批量移除指定的不适合国内使用的技能
"""
import io
import sys
# 修复Windows控制台中文编码问题
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import json
import shutil
import argparse
from pathlib import Path

def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if not config_path:
        config_path = Path(__file__).parent.parent / "config.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_skills_to_remove(config: dict) -> list:
    """获取需要移除的技能列表"""
    return config.get("skills_to_remove", [])

def clean_skill(skill_name: str, skills_root: str, dry_run: bool = False) -> tuple[bool, str]:
    """
    清理单个技能
    返回 (是否成功, 结果信息)
    """
    skill_path = Path(skills_root) / skill_name
    
    if not skill_path.exists():
        return True, f"✅ 技能 {skill_name} 不存在，跳过"
    
    if not skill_path.is_dir():
        return True, f"✅ {skill_name} 不是目录，跳过"
    
    try:
        if dry_run:
            return True, f"🔍 [模拟] 将移除技能 {skill_name} ({skill_path})"
        
        shutil.rmtree(skill_path)
        return True, f"✅ 已成功移除技能 {skill_name}"
    except Exception as e:
        return False, f"❌ 移除技能 {skill_name} 失败：{str(e)}"

def main():
    parser = argparse.ArgumentParser(description="批量清理不适合国内使用的技能")
    parser.add_argument("--config", "-c", help="配置文件路径，默认使用同目录下的config.json")
    parser.add_argument("--dry-run", "-d", action="store_true", help="模拟运行，不实际删除")
    parser.add_argument("--list", "-l", action="store_true", help="只列出待清理的技能列表，不执行删除")
    parser.add_argument("--add", "-a", help="添加新的技能到清理列表")
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    skills_to_remove = get_skills_to_remove(config)
    skills_root = config.get("skills_root", str(Path.home() / ".openclaw" / "workspace-main" / "skills"))
    dry_run = args.dry_run or config.get("dry_run", False)

    # 只列出列表
    if args.list:
        print("📋 待清理的技能列表：")
        for i, skill in enumerate(skills_to_remove, 1):
            print(f"{i:2d}. {skill}")
        print(f"\n总计：{len(skills_to_remove)} 个技能")
        return

    # 添加新技能到列表
    if args.add:
        if args.add not in skills_to_remove:
            skills_to_remove.append(args.add)
            config["skills_to_remove"] = skills_to_remove
            config_path = args.config or Path(__file__).parent.parent / "config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ 已添加技能 {args.add} 到清理列表")
        else:
            print(f"ℹ️ 技能 {args.add} 已经在清理列表中")
        return

    # 执行清理
    print(f"🚀 开始批量清理技能，共 {len(skills_to_remove)} 个待处理...")
    print(f"📂 技能根目录：{skills_root}")
    if dry_run:
        print("⚠️  模拟模式，不会实际删除文件")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    for skill in skills_to_remove:
        ok, msg = clean_skill(skill, skills_root, dry_run)
        print(msg)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    print("-" * 60)
    print(f"📊 清理完成：成功 {success_count} 个，失败 {fail_count} 个")
    if not dry_run and fail_count == 0:
        print("🎉 所有不需要的国外技能已清理完成！")
        print("ℹ️  提示：重启OpenClaw网关后，技能列表会自动更新")

if __name__ == "__main__":
    main()
