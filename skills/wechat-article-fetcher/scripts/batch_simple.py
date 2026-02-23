import json
import random
import time
from pathlib import Path
import re
import requests
from datetime import datetime

ACCOUNTS = [
    "究模智", "智猩猩AI", "架构师", "PaperAgent", "苏哲管理咨询",
    "AI寒武纪", "苍何", "腾讯研究院", "InfoQ", "逛逛GitHub",
    "熵衍AI", "AgenticAI", "AI产品阿颖"
]

OUTPUT_DIR = Path(r"D:\anthropic\wechat\2025-02-20")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fetcher = requests.Session()
fetcher.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://weixin.sogou.com/'
})

shuffled = ACCOUNTS.copy()
random.shuffle(shuffled)

summary = {}

for idx, name in enumerate(shuffled, 1):
    print(f"[{idx}/{len(shuffled)}] Fetching: {name}")
    
    try:
        url = "https://weixin.sogou.com/weixin"
        params = {'type': '2', 'query': name, 'page': '1'}
        resp = fetcher.get(url, params=params, timeout=15)
        resp.encoding = 'utf-8'
        
        articles = []
        pattern = r'<li id="sogou_vr_[^"]*"[^>]*>.*?<div class="txt-box">.*?</li>'
        blocks = re.findall(pattern, resp.text, re.DOTALL)
        
        for block in blocks[:5]:
            article = {}
            
            m = re.search(r'<h3>.*?<a[^>]*>(.*?)</a>.*?</h3>', block, re.DOTALL)
            if m:
                article['title'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            
            m = re.search(r'<h3>.*?<a[^>]*href="([^"]*)"', block, re.DOTALL)
            if m:
                u = m.group(1)
                article['url'] = 'https://weixin.sogou.com' + u if u.startswith('/') else u
            
            m = re.search(r'<p class="txt-info">(.*?)</p>', block, re.DOTALL)
            if m:
                article['summary'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            
            m = re.search(r"timeConvert\('(\d+)'\)", block)
            if m:
                article['publish_time'] = datetime.fromtimestamp(int(m.group(1))).strftime('%Y-%m-%d %H:%M')
            
            m = re.search(r'<a id="weixin_account"[^>]*>([^<]*)</a>', block)
            article['account_name'] = m.group(1).strip() if m else name
            
            if article.get('title') and article.get('url'):
                articles.append(article)
        
        result = {'account': {'name': name, 'articles_count': len(articles)}, 'articles': articles}
        
        fname = re.sub(r'[\\\\/:*?"<>|]', '_', name) + ".json"
        fpath = OUTPUT_DIR / fname
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        summary[name] = len(articles)
        print(f"  -> {len(articles)} articles saved to {fname}")
        
    except Exception as e:
        print(f"  -> Error: {e}")
        summary[name] = 0
    
    if idx < len(shuffled):
        time.sleep(random.uniform(3, 5))

# Save summary
with open(OUTPUT_DIR / "summary.json", 'w', encoding='utf-8') as f:
    json.dump({'total': len(ACCOUNTS), 'articles': sum(summary.values()), 'details': summary}, f, ensure_ascii=False, indent=2)

print("\n" + "="*50)
print("Summary:")
for name in ACCOUNTS:
    print(f"  {name}: {summary.get(name, 0)} articles")
print(f"Total: {sum(summary.values())} articles from {len(ACCOUNTS)} accounts")
