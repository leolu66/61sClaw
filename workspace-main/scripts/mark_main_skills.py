#!/usr/bin/env python3
"""为main workspace的技能创建来源标记"""

from pathlib import Path

SKILLS_DIR = Path(r"C:\Users\luzhe\.openclaw\workspace-main\skills")

for skill_dir in SKILLS_DIR.iterdir():
    if skill_dir.is_dir():
        marker_file = skill_dir / ".skill-source"
        if not marker_file.exists():
            marker_file.write_text("main")
            print(f"Marked: {skill_dir.name} -> main")
        else:
            print(f"Already marked: {skill_dir.name}")
