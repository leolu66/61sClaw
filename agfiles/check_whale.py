# -*- coding: utf-8 -*-
import requests
import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# 从环境变量读取 API Key
api_key = os.environ.get("XTC_WHALECLOUD_API_KEY", "")
if not api_key:
    raise ValueError('请设置环境变量 XTC_WHALECLOUD_API_KEY')

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

# 尝试不同的API端点
endpoints = [
    "https://lab.iwhalecloud.com/api/v1/user/balance",
    "https://lab.iwhalecloud.com/gpt-proxy/api/v1/user/balance",
    "https://lab.iwhalecloud.com/openai/v1/user/balance",
]

results = []

for url in endpoints:
    try:
        r = requests.get(url, headers=headers, timeout=30)
        results.append(f"{url}: {r.status_code} - {r.text[:500]}")
    except Exception as e:
        results.append(f"{url}: Error - {e}")

# 写入文件
with open("C:/Users/luzhe/.openclaw/workspace-main/whale_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
print("Done")
