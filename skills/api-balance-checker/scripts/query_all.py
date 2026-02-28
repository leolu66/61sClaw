#!/usr/bin/env python3
"""
全部查询 - 查询全部平台余额（WhaleCloud + 智谱AI + Moonshot）
"""
import subprocess
import sys
import os

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
query_script = os.path.join(script_dir, "query_balance.py")

# 查询全部平台
platforms = ["whalecloud", "zhipu", "moonshot"]

print("=" * 60)
print("全部查询 - WhaleCloud + 智谱AI + Moonshot")
print("=" * 60)

# 调用主查询脚本
subprocess.run([sys.executable, query_script] + platforms)
