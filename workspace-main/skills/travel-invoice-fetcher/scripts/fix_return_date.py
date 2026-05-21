import re

with open('expense_report_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除所有 return_date="", 行（包括前面的空格和换行）
content = re.sub(r'\s+return_date="",\s*\n', '\n', content)

# 删除 Excel 生成中的 return_date 列
content = content.replace("ws.cell(row=row, column=4, value=item.return_date)", "# 返回日期列已删除")

with open('expense_report_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
