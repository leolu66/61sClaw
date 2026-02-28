import re
from pathlib import Path

log_dir = Path("logs/daily")

print("测试文件名解析：")
print("=" * 60)

for file_path in sorted(log_dir.iterdir()):
    filename = file_path.name
    if not filename.endswith('.md'):
        continue

    name_without_ext = filename.replace('.md', '')
    print(f"\n文件名: {filename}")

    # 使用正则表达式提取日期
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})', name_without_ext)
    if match:
        year, month, day = match.groups()
        print(f"  日期: {year}-{month}-{day}")
        print(f"  匹配: ✅")
    else:
        print(f"  匹配: ❌")
