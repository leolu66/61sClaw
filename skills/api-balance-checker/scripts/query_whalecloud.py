#!/usr/bin/env python3
"""
 WhaleCloud 查询 - 只查询浩鲸Lab (WhaleCloud) 余额
"""
import subprocess
import sys
import os

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
query_script = os.path.join(script_dir, "query_balance.py")

# 只查询 WhaleCloud
platforms = ["whalecloud"]

print("=" * 60)
print(" WhaleCloud (浩鲸Lab) 余额查询")
print("=" * 60)

# 调用主查询脚本
subprocess.run([sys.executable, query_script] + platforms)
