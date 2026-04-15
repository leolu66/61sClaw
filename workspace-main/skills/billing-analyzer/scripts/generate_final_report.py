#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate full billing report with table notes
Usage: python generate_full_report_with_notes.py [csv_file]
"""
import subprocess, sys, os

csv_file = sys.argv[1] if len(sys.argv) > 1 else "billing_2026-02-01_2026-02-27.csv"

print("="*60)
print("Generating full report with table notes...")
print("="*60)

# Step 1: Generate base report
print("\n1. Base report...")
subprocess.run([sys.executable, "billing_analyzer.py", csv_file], check=True)

# Step 2: Generate deep insights
print("\n2. Deep insights...")
subprocess.run([sys.executable, "billing_analyzer_deep.py", csv_file], check=True)

# Step 3: Add notes to the deep report
print("\n3. Adding table notes...")
deep_report = csv_file.replace('.csv', '_深度分析.md')
if os.path.exists(deep_report):
    with open(deep_report, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add 3 notes
    content = content.replace(
        '| **glm-4.7** | 4.91 | 0.6 | 39 | 12.59 | 1.07 | 4.59 | 🟡 良好 |',
        '| **glm-4.7** | 4.91 | 0.6 | 39 | 12.59 | 1.07 | 4.59 | 🟡 良好 |\n\n> **注：** 下表仅列出费用 Top 5 模型，完整模型列表见深度洞察章节。'
    )
    content = content.replace(
        '| **成本优化空间** | 40.9% | 对比行业平均 |',
        '| **成本优化空间** | 40.9% | 对比行业平均 |\n\n> **注：** 效率分析展示了整体成本效益，行业平均约 7 元/百万 Tokens。'
    )
    content = content.replace(
        '| 特殊复杂推理任务 | Claude/GPT | 能力最强，按需使用 |',
        '| 特殊复杂推理任务 | Claude/GPT | 能力最强，按需使用 |\n\n> **注：** 根据任务类型选择合适的模型，可节省 30-50% 成本。'
    )
    
    with open(deep_report, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'   Notes added to {deep_report}')
    
    # Step 4: Open the report
    print("\n4. Opening report...")
    os.startfile(deep_report)
    print(f'   Opened: {deep_report}')
else:
    print(f'   ERROR: {deep_report} not found')

print("\n" + "="*60)
print("Done!")
print("="*60)
