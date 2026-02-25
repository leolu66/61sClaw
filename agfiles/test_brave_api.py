import requests

r = requests.post(
    'https://api.search.brave.com/res/v1/web/search',
    headers={
        'X-Subscription-Token': 'BSAVcG_OLy94oPAQmb3ZpymklKZejXs',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json'
    },
    json={
        'q': 'OpenClaw',
        'count': 3,
        'country': 'CN',
        'search_lang': 'zh-hans'
    }
)
print('Status:', r.status_code)
data = r.json()
results = data.get('web', {}).get('results', [])
for i, r in enumerate(results):
    print(f"{i+1}. {r.get('title')}")
    print(f"   {r.get('url')}")
