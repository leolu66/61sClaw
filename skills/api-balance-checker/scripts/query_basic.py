#!/usr/bin/env python3
"""
基本查询 - 只查询 WhaleCloud Lab（鲸云实验室）余额
"""
import subprocess
import sys
import os

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
query_script = os.path.join(script_dir, "query_balance.py")

# 只查询 whalecloud 平台
platforms = ["whalecloud"]

print("=" * 60)
print("基本查询 - WhaleCloud Lab（鲸云实验室）")
print("=" * 60)

# 调用主查询脚本
subprocess.run([sys.executable, query_script] + platforms)
