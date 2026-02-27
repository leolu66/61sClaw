import requests
import json
import sys

query = sys.argv[1] if len(sys.argv) > 1 else "OpenClaw"
count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

r = requests.post(
    'https://api.search.brave.com/res/v1/web/search',
    headers={
        'X-Subscription-Token': 'BSAVcG_OLy94oPAQmb3ZpymklKZejXs',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    },
    json={
        'q': query,
        'count': count,
        'country': 'CN',
        'search_lang': 'zh-hans'
    }
)

data = r.json()
results = data.get('web', {}).get('results', [])
for i, r in enumerate(results):
    print(f"{i+1}. {r.get('title', 'N/A')}")
    print(f"   {r.get('url', 'N/A')}")
    print()
