# -*- coding: utf-8 -*-
import re

with open('whale_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

text = re.sub(r'<[^>]+>', ' ', content)
text = re.sub(r'\s+', ' ', text)

# 查找关键数据
print('=== 页面内容 ===')
print(text[:3000])
