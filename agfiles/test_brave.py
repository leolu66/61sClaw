import requests
print("starting...")
r = requests.post(
    'https://api.search.brave.com/res/v1/web/search',
    headers={
        'X-Subscription-Token': 'BSAVcG_OLy94oPAQmb3ZpymklKZejXs',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    },
    json={'q': 'AI', 'count': 3}
)
print("status:", r.status_code)
data = r.json()
print("results:", len(data.get('web', {}).get('results', [])))
