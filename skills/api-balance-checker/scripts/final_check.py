"""
API Balance Checker - 最终版
"""
import requests
import json
import sys

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

def query_whalecloud():
    """查询WhaleCloud API余额"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 尝试获取用户信息
    url = "https://lab.iwhalecloud.com/api/user/info"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")

        print(f"Response text: {resp.text}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data
            except:
                pass
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    query_whalecloud()
