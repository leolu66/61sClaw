#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import io

# 设置环境变量
os.environ['XTC_EXCHANGE_PASSWORD'] = 'Luzh1103!'

# 修复 stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 导入并运行主脚本
sys.argv = ['', '--limit', '10']
import subprocess
result = subprocess.run(
    [sys.executable, r'C:\Users\luzhe\.openclaw\workspace-main\skills\exchange-email-reader\scripts\read_emails.py', '--limit', '10'],
    env={**os.environ, 'XTC_EXCHANGE_PASSWORD': 'Luzh1103!'},
    capture_output=True,
    encoding='utf-8',
    errors='replace'
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
