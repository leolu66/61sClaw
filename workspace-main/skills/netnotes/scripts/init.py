#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetNotes 初始化脚本 - 创建目录结构和数据库
"""

from pathlib import Path
import sys

def init():
    """初始化NetNotes环境"""
    base_dir = Path(__file__).parent.parent
    
    # 创建笔记本目录
    notebooks_dir = base_dir / "notebooks"
    categories = ["AI", "运营商", "管理", "社会生活", "技术其他", "其他"]
    
    print("[NetNotes] 创建笔记本目录...")
    for category in categories:
        category_dir = notebooks_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {category}")
    
    # 创建数据目录
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [OK] data/")
    
    # 初始化数据库
    print("\n[NetNotes] 初始化数据库...")
    sys.path.insert(0, str(Path(__file__).parent))
    from database import ArticleDatabase
    
    db = ArticleDatabase(data_dir / "netnotes.db")
    stats = db.get_statistics()
    print(f"  [OK] 数据库已就绪 (当前 {stats['total']} 篇文章)")
    
    print("\n[NetNotes] 初始化完成！")
    print(f"\n使用方式:")
    print(f"  保存文章: python scripts/main.py <URL>")
    print(f"  查看列表: python scripts/manager.py list")
    print(f"  搜索文章: python scripts/manager.py search <关键词>")
    print(f"  统计信息: python scripts/manager.py stats")

if __name__ == "__main__":
    init()
