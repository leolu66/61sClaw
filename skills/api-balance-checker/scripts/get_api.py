"""
API Balance Checker - 保存响应到文件
"""
import requests

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

url = "https://lab.iwhalecloud.com/api/user/info"

resp = requests.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")

with open("C:/Users/luzhe/Pictures/whalecloud_api_response.txt", "w", encoding="utf-8") as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Headers: {dict(resp.headers)}\n")
    f.write(f"Content:\n{resp.text}")
