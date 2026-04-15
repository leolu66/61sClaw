import json
import os

# 获取 OpenClaw 根目录（脚本所在目录的父目录的父目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
openclaw_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
vault_dir = os.path.join(openclaw_dir, 'vault')

with open(os.path.join(vault_dir, 'credentials.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

email = data['credentials'].get('email', {})
print("Email 凭据字段:")
for field in email.get('fields', []):
    print(f"  key={field['key']}, label={field['label']}, type={field['type']}, value={field['value']}")
