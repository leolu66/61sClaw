import json

with open(r'skills\ai-news-fetcher\output\chunk_3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total items: {len(data)}")
for i, item in enumerate(data):
    print(f"[{i}] {item['title'][:55]} | {item['date']}")