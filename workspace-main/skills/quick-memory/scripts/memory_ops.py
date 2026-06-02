#!/usr/bin/env python3
"""
Quick Memory - 记忆文件操作脚本
提供记忆文件的列出、读取、搜索、保存和统计功能。

用法:
    python scripts/memory_ops.py save --file content.md    # 保存一条记忆
    python scripts/memory_ops.py list [--limit N]          # 列出最新N条
    python scripts/memory_ops.py list --from YYYY-MM-DD --to YYYY-MM-DD
    python scripts/memory_ops.py search <关键词> [--limit N]
    python scripts/memory_ops.py stats                     # 统计信息
    python scripts/memory_ops.py read <文件名>              # 读取单条
"""

import sys
import os
import json
import re
import io
from pathlib import Path
from datetime import datetime, date
from typing import Optional

# 强制 UTF-8 输出（解决 Windows GBK 编码问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ── 路径 & 配置 ──────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_MEMORY_DIR = SKILL_DIR / "memory"
CONFIG_PATH = SCRIPT_DIR / "config.json"

# 加载配置
config = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

MEMORY_DIR = Path(config.get("memory_dir", "./memory"))
if not MEMORY_DIR.is_absolute():
    MEMORY_DIR = (SKILL_DIR / MEMORY_DIR).resolve()
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_LIMIT = config.get("default_list_limit", 10)

# ── 辅助函数 ──────────────────────────────────────────────────

def parse_meta(content: str) -> dict:
    """解析 YAML frontmatter"""
    meta = {}
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if m:
        yaml_block = m.group(1)
        for line in yaml_block.strip().split('\n'):
            if ':' in line:
                key, _, val = line.partition(':')
                key = key.strip()
                val = val.strip()
                if val.startswith('[') and val.endswith(']'):
                    val = [t.strip().strip('"\'') for t in val[1:-1].split(',')]
                elif val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                meta[key] = val
    return meta

def get_memory_files() -> list[Path]:
    """返回按修改时间倒序排列的记忆文件列表"""
    files = sorted(
        MEMORY_DIR.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    return files

def get_memory_files_by_date(from_date: Optional[str] = None, to_date: Optional[str] = None) -> list[Path]:
    """按日期范围筛选记忆文件"""
    files = get_memory_files()
    if not from_date and not to_date:
        return files
    
    def get_file_date(f: Path) -> Optional[str]:
        content = f.read_text(encoding="utf-8", errors="replace")
        meta = parse_meta(content)
        return meta.get("date", "").split()[0]  # "2026-06-02 10:08" -> "2026-06-02"
    
    result = []
    for f in files:
        fd = get_file_date(f)
        if not fd:
            continue
        if from_date and fd < from_date:
            continue
        if to_date and fd > to_date:
            continue
        result.append(f)
    return result

def format_short(f: Path, meta: dict, content: str) -> str:
    """格式化一条记忆为短行"""
    cate = meta.get("category", "📄")
    cate_icon = {
        "灵感": "💡", "待办": "📝", "笔记": "📖",
        "备忘": "📌", "想法": "🤔"
    }.get(cate, "📄")
    title = meta.get("title", f.name)
    dt = meta.get("date", "")
    tags = meta.get("tags", [])
    if isinstance(tags, list):
        tags_str = " ".join(f"#{t}" for t in tags)
    else:
        tags_str = ""
    return f"{cate_icon} **{title}** ({dt}) {tags_str}"

# ── 命令实现 ──────────────────────────────────────────────────

def cmd_list(args: list[str]):
    """列出记忆文件"""
    limit = DEFAULT_LIMIT
    from_date = None
    to_date = None
    
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] == "--from" and i + 1 < len(args):
            from_date = args[i + 1]
            i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            to_date = args[i + 1]
            i += 2
        else:
            i += 1
    
    files = get_memory_files_by_date(from_date, to_date)
    
    count = 0
    for f in files[:limit]:
        content = f.read_text(encoding="utf-8", errors="replace")
        meta = parse_meta(content)
        print(format_short(f, meta, content))
        count += 1
    
    total = len(files)
    if count < total:
        print(f"\n--- 共 {total} 条，显示前 {count} 条 ---")
    else:
        print(f"\n--- 共 {total} 条 ---")

    # 输出 JSON 供脚本调用
    result_path = SCRIPT_DIR / "_last_result.json"
    with open(result_path, "w", encoding="utf-8") as rf:
        json.dump({
            "total": total,
            "shown": count,
            "files": [str(f.relative_to(MEMORY_DIR)) for f in files[:count]]
        }, rf, ensure_ascii=False, indent=2)


def cmd_search(args: list[str]):
    """搜索记忆（关键词全文搜索）"""
    query = None
    limit = DEFAULT_LIMIT
    
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif not args[i].startswith("--"):
            query = args[i]
            i += 1
        else:
            i += 1
    
    if not query:
        print("请提供搜索关键词", file=sys.stderr)
        sys.exit(1)
    
    files = get_memory_files()
    results = []
    
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if query.lower() in content.lower():
            meta = parse_meta(content)
            results.append((f, meta, content))
    
    for f, meta, content in results[:limit]:
        print(format_short(f, meta, content))
    
    total = len(results)
    if total > limit:
        print(f"\n--- 找到 {total} 条，显示前 {limit} 条 ---")
    else:
        print(f"\n--- 找到 {total} 条 ---")

    # 输出 JSON 供脚本调用
    result_path = SCRIPT_DIR / "_last_result.json"
    with open(result_path, "w", encoding="utf-8") as rf:
        json.dump({
            "total": total,
            "shown": min(total, limit),
            "files": [str(f.relative_to(MEMORY_DIR)) for f, _, _ in results[:limit]],
            "query": query
        }, rf, ensure_ascii=False, indent=2)


def cmd_stats(args: list[str]):
    """统计信息"""
    files = get_memory_files()
    total = len(files)
    
    # 分类统计
    categories = {}
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        meta = parse_meta(content)
        cat = meta.get("category", "未分类")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"📊 记忆统计")
    print(f"├─ 总数: {total} 条")
    print(f"├─ 记忆目录: {MEMORY_DIR}")
    print(f"└─ 分类: ")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   ├─ {cat}: {count} 条")
    
    # 输出 JSON
    result_path = SCRIPT_DIR / "_last_result.json"
    with open(result_path, "w", encoding="utf-8") as rf:
        json.dump({
            "total": total,
            "categories": categories,
            "memory_dir": str(MEMORY_DIR)
        }, rf, ensure_ascii=False, indent=2)


def cmd_read(args: list[str]):
    """读取单条记忆"""
    if not args:
        print("请指定文件名", file=sys.stderr)
        sys.exit(1)
    
    fname = args[0]
    fpath = MEMORY_DIR / fname
    if not fpath.exists():
        # 尝试模糊匹配
        matches = list(MEMORY_DIR.glob(f"*{fname}*"))
        if matches:
            fpath = matches[0]
        else:
            print(f"未找到: {fname}", file=sys.stderr)
            sys.exit(1)
    
    content = fpath.read_text(encoding="utf-8", errors="replace")
    print(content)


def cmd_save(args: list[str]):
    """保存记忆（从标准输入或文件读取内容）"""
    content = None
    
    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            filepath = Path(args[i + 1])
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
            i += 2
        elif args[i] == "--content" and i + 1 < len(args):
            content = args[i + 1]
            i += 2
        else:
            i += 1
    
    if not content:
        content = sys.stdin.read().strip()
    
    if not content:
        print("请提供要保存的内容", file=sys.stderr)
        sys.exit(1)
    
    # 生成文件名
    now = datetime.now()
    fname = now.strftime("%Y-%m-%d_%H%M%S.md")
    fpath = MEMORY_DIR / fname
    
    # 如果内容不包含frontmatter，添加基本frontmatter
    if not content.startswith("---"):
        content = f"""---
id: {now.strftime("%Y%m%d-%H%M")}-auto
date: {now.strftime("%Y-%m-%d %H:%M")}
category: 未分类
tags: []
title: 快速记录
---

{content}
"""
    
    fpath.write_text(content, encoding="utf-8")
    # 尝试相对路径显示，失败则显示完整路径
    try:
        display_path = fpath.relative_to(SKILL_DIR)
    except ValueError:
        display_path = fpath
    print(f"✅ 已保存: {display_path}")


# ── 主入口 ──────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        "list": cmd_list,
        "search": cmd_search,
        "stats": cmd_stats,
        "read": cmd_read,
        "save": cmd_save,
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"未知命令: {command}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
