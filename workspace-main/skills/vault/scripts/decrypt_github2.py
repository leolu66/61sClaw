#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, json, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\luzhe\.openclaw\workspace-main\skills\vault\scripts')
from vault import Vault

vault = Vault()

with open(r'C:\Users\luzhe\.openclaw\vault\credentials.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

github = data['credentials']['github']
for field in github['fields']:
    label = field['label']
    val = field['value']
    if field['isSensitive']:
        # Try manual base64 decode first
        try:
            decoded = base64.b64decode(val.encode('utf-8')).decode('utf-8')
            print(f'{label}: {decoded}')
        except:
            # Fall back to vault decrypt
            decrypted = vault._decrypt_sensitive(val)
            print(f'{label}: {decrypted}')
    else:
        print(f'{label}: {val}')