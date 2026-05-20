import re, os, glob, sys
from datetime import datetime
from collections import defaultdict

output_dir = r"C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\output"
cutoff = datetime(2026, 4, 26)

# 1. 筛选日期后的文件
files = []
for f in sorted(glob.glob(os.path.join(output_dir, "*.md"))):
    basename = os.path.basename(f)
    # 跳过非日期命名的文件
    match = re.match(r'^(\d{8})_(\d{4})\.md$', basename)
    if not match:
        continue
    dt = datetime.strptime(match.group(1), "%Y%m%d")
    if dt >= cutoff:
        files.append(f)

print(f"文件数: {len(files)} (from {files[0]} to {files[-1]})")
print()

# 2. 提取标题
all_titles = []  # (title, url, source, date_str)
current_source = ""
current_date = ""

for fpath in files:
    basename = os.path.basename(fpath)
    current_date = basename[:8]
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        continue

    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        
        # 检测来源标题: ## 🎓 MIT Tech Review AI 等
        if line.startswith('## ') or line.startswith('### '):
            # 提取来源名称
            clean = re.sub(r'^#+\s*[\U0001F000-\U0001FFFF\U00002500-\U000027BF\u2600-\u27BF\u2B50\u2700-\u27BF\u2100-\u214F]?\s*', '', line)
            clean = re.sub(r'^#+\s*\d️⃣?\s*', '', clean)
            clean = re.sub(r'^#+\s*', '', clean).strip()
            if clean and not clean.startswith('>') and clean not in ('深度总结', '采集汇总', 'RSS 国际 AI 快讯'):
                current_source = clean
        
        # 检测表格中的标题行: | 1 | [Title](url) | summary | time |
        match = re.match(r'^\|\s*\d+\s*\|\s*\[(.+?)\]\((.+?)\)', line)
        if match:
            title = match.group(1).strip()
            url = match.group(2).strip()
            all_titles.append((title, url, current_source, current_date))
            continue

        # RSS 表格: | 1 | [Title](url) | time |
        match2 = re.match(r'^\|\s*\d+\s*\|\s*\[(.+?)\]\((.+?)\)\s*\|\s*(.+?)\s*\|', line)
        if match2 and not any(t[1] == match2.group(2).strip() for t in all_titles[-3:]):
            continue  # already caught above

# 3. 按来源归类，按日期排序
by_source = defaultdict(list)
for title, url, source, date_str in all_titles:
    if not source:
        source = "未分类"
    by_source[source].append((date_str, title, url))

# 输出
print(f"总标题数: {len(all_titles)}")
print()

for source in sorted(by_source.keys()):
    items = by_source[source]
    print(f"## {source} ({len(items)}条)")
    print()
    for date_str, title, url in sorted(items, key=lambda x: x[0], reverse=True):
        print(f"  [{date_str}] {title}")
    print()
