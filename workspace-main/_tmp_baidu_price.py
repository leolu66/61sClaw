import urllib.request, re, json

req = urllib.request.Request('https://ai.baidu.com/tech/search/s/general', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='replace')

# Find the renderData JSON
m = re.search(r'window\._renderData\s*=\s*({.*?});', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    result = data.get('result', {})
    # Look for anything search-related
    text = json.dumps(result, ensure_ascii=False)
    # Find sections mentioning search / 搜索
    idx = text.find('搜索')
    while idx != -1:
        ctx = text[max(0,idx-200):idx+500]
        if any(kw in ctx for kw in ['价格', '免费', 'QPS', '调用', '套餐', '付费', '计费']):
            print('--- Found ---')
            print(ctx[:500])
            print()
        idx = text.find('搜索', idx+1)

# Also search for "search" case-insensitive
text_lower = text.lower()
idx = text_lower.find('search')
while idx != -1:
    ctx = text[max(0,idx-200):idx+400]
    if any(kw in ctx.lower() for kw in ['price', 'free', 'qps', 'plan', 'pricing']):
        print('--- Found EN ---')
        print(ctx[:400])
        print()
    idx = text_lower.find('search', idx+1)
