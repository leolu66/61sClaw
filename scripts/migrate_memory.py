#!/usr/bin/env python3
"""
整理 MEMORY.md，将日期开头的记录移到 memory/ 目录
"""

import re
from pathlib import Path

# 读取 MEMORY.md
memory_md = Path("MEMORY.md")
content = memory_md.read_text(encoding="utf-8")

# 找到所有日期记录
pattern = r'---\n\n### (\d{4}-\d{2}-\d{2}) \| (.+?)\n\n(.+?)(?=---\n\n###|\Z)'
matches = list(re.finditer(pattern, content, re.DOTALL))

print(f"找到 {len(matches)} 个日期记录")

# 保存每个记录到单独文件
for match in matches:
    date = match.group(1)
    title = match.group(2)
    body = match.group(3)
    
    # 创建文件
    filename = f"memory/{date}.md"
    filepath = Path(filename)
    
    # 如果文件已存在，追加内容
    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        new_content = existing + f"\n---\n\n## {title}\n\n{body}"
    else:
        new_content = f"# {date} 记忆\n\n## {title}\n\n{body}"
    
    filepath.write_text(new_content, encoding="utf-8")
    print(f"已保存: {filename}")

# 从 MEMORY.md 移除日期记录
# 保留核心原则部分，移除日期记录
new_memory_content = re.sub(pattern, '', content, flags=re.DOTALL)

# 清理多余的空行
new_memory_content = re.sub(r'\n{4,}', '\n\n\n', new_memory_content)

# 添加引用说明
replacement_text = """---

## 错误反思（避免重复犯错）

> 每日错误记录已迁移到 `memory/YYYY-MM-DD.md` 文件中
> 
> 使用 `memory_search` 可以搜索所有历史错误记录

---

## 技能开发经验

> **创建技能时请参考 `skills/SKILL_DO.md` 中的完整规范。**
> 
> 详细的技能开发案例已迁移到 `memory/YYYY-MM-DD.md` 文件中

---

## 用户与环境理解"""

# 找到并替换
new_memory_content = re.sub(
    r'---\n\n## 错误反思.*?## 用户与环境理解',
    replacement_text,
    new_memory_content,
    flags=re.DOTALL
)

# 写回 MEMORY.md
memory_md.write_text(new_memory_content, encoding="utf-8")
print("已更新 MEMORY.md")
