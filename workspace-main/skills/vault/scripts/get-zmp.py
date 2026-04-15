import json
import os

# 获取 OpenClaw 根目录（脚本所在目录的父目录的父目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
openclaw_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
vault_dir = os.path.join(openclaw_dir, 'vault')

with open(os.path.join(vault_dir, 'credentials.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

zmp = data['credentials'].get('zmp', {})
print("ZMP 系统:")
for field in zmp.get('fields', []):
    print(f"  {field['label']}: {field['value']}")
