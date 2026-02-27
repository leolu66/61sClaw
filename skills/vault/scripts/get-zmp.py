import json

with open(r'C:\Users\luzhe\.openclaw\vault\credentials.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

zmp = data['credentials'].get('zmp', {})
print("ZMP 系统:")
for field in zmp.get('fields', []):
    print(f"  {field['label']}: {field['value']}")
