#!/usr/bin/env python3
"""
同步各Agent技能到GitHub仓库
将各workspace的技能合并到workspace-main/skills用于GitHub提交
"""

import os
import shutil
import argparse
from pathlib import Path

# Agent配置
AGENTS = [
    {"name": "main", "path": r"C:\Users\luzhe\.openclaw\workspace-main", "skills_dir": "skills"},
    {"name": "entertainment", "path": r"C:\Users\luzhe\.openclaw\workspace-entertainment", "skills_dir": "skills"},
]

GITHUB_SKILLS_DIR = Path(r"C:\Users\luzhe\.openclaw\workspace-main\skills")

def sync_skills(dry_run=False):
    """同步技能到GitHub目录"""
    conflicts = []
    synced = []
    skipped = []
    
    print("=== Skills Sync to GitHub ===\n")
    
    for agent in AGENTS:
        agent_skills_path = Path(agent["path"]) / agent["skills_dir"]
        
        if not agent_skills_path.exists():
            print(f"[{agent['name']}] No skills directory found, skipping...")
            continue
        
        print(f"[{agent['name']}] Scanning skills...")
        
        for skill_dir in agent_skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_name = skill_dir.name
            source_path = skill_dir
            target_path = GITHUB_SKILLS_DIR / skill_name
            source_marker = target_path / ".skill-source"
            
            # 检查是否已存在
            if target_path.exists():
                # 检查来源
                existing_agent = "unknown"
                if source_marker.exists():
                    existing_agent = source_marker.read_text().strip()
                
                if existing_agent == agent["name"]:
                    print(f"  [SKIP] {skill_name} (already from {agent['name']})")
                    skipped.append({"skill": skill_name, "agent": agent["name"]})
                else:
                    # 冲突！
                    print(f"  [CONFLICT] {skill_name} exists from '{existing_agent}', current from '{agent['name']}'")
                    conflicts.append({
                        "skill": skill_name,
                        "existing_agent": existing_agent,
                        "new_agent": agent["name"]
                    })
            else:
                # 新技能
                if dry_run:
                    print(f"  [ADD] {skill_name} (would add from {agent['name']})")
                else:
                    shutil.copytree(source_path, target_path)
                    source_marker.write_text(agent["name"])
                    print(f"  [ADD] {skill_name} (from {agent['name']})")
                synced.append({"skill": skill_name, "agent": agent["name"], "action": "add"})
    
    print(f"\n=== Sync Summary ===")
    print(f"Synced: {len(synced)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Conflicts: {len(conflicts)}")
    
    if conflicts:
        print("\n!!! CONFLICTS DETECTED - Manual resolution required !!!\n")
        for c in conflicts:
            print(f"Skill: {c['skill']}")
            print(f"  Existing from: {c['existing_agent']}")
            print(f"  New from:      {c['new_agent']}")
            print()
    
    return {
        "synced": synced,
        "skipped": skipped,
        "conflicts": conflicts,
        "has_conflicts": len(conflicts) > 0
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync skills to GitHub")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    args = parser.parse_args()
    
    result = sync_skills(dry_run=args.dry_run)
    exit(1 if result["has_conflicts"] else 0)
