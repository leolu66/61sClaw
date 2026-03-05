#!/usr/bin/env python3
"""
直接发送测试任务给 Claude Code - 简化版
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    # 任务指令
    instruction = """在 D:\\projects\\workspace\\shared\\output\\task-test-003\\ 目录下创建一个测试报告文件 report.md，内容包含：
1. 测试标题：多智能体协作联调测试
2. 测试时间：2026-03-05 12:10
3. 执行节点：Claude
4. 测试结果：成功
5. 备注：这是通过 claude-code-sender SDK 直接发送的测试任务

执行完成后，请创建 result.json 文件说明完成情况。"""
    
    print("[发送任务] 正在发送任务给 Claude Code...")
    print("[指令] 创建测试报告文件...")
    print()
    
    # 构建命令
    args = ["claude", "-p", instruction]
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=300,
            cwd="D:\\projects\\workspace\\shared"
        )
        
        print("=" * 50)
        print("任务执行结果:")
        print(f"  返回码: {result.returncode}")
        print()
        
        if result.stdout:
            print("输出内容:")
            print(result.stdout[:1000])
        
        if result.stderr:
            print("\n错误输出:")
            print(result.stderr[:500])
        
        print("=" * 50)
        
    except FileNotFoundError:
        print("[错误] 未找到 claude 命令，请先安装: npm install -g @anthropic-ai/claude-code")
    except subprocess.TimeoutExpired:
        print("[错误] 请求超时")
    except Exception as e:
        print(f"[错误] 执行错误: {e}")

if __name__ == "__main__":
    main()
