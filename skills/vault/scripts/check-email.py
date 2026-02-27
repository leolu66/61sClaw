import json

with open(r'C:\Users\luzhe\.openclaw\vault\credentials.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

email = data['credentials'].get('email', {})
print("Email 凭据字段:")
for field in email.get('fields', []):
    print(f"  key={field['key']}, label={field['label']}, type={field['type']}, value={field['value']}")
