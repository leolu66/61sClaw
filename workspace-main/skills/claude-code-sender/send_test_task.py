#!/usr/bin/env python3
"""
直接发送测试任务给 Claude Code
"""
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from claude_node_sdk import ClaudeNodeSDK

def main():
    # 创建 SDK 实例
    sdk = ClaudeNodeSDK("claude", workspace="D:\\projects\\workspace\\shared")
    
    # 任务指令
    instruction = """在 D:\\projects\\workspace\\shared\\output\\task-test-003\\ 目录下创建一个测试报告文件 report.md，内容包含：
1. 测试标题：多智能体协作联调测试
2. 测试时间：2026-03-05 12:10
3. 执行节点：Claude
4. 测试结果：成功
5. 备注：这是通过 claude-code-sender SDK 直接发送的测试任务

执行完成后，请创建 result.json 文件说明完成情况。"""
    
    print("[发送任务] 正在发送任务给 Claude Code...")
    print(f"[指令] {instruction[:100]}...")
    print()
    
    # 发送任务
    result = sdk.send_task(
        instruction=instruction,
        output_dir="D:\\projects\\workspace\\shared\\output\\task-test-003",
        max_turns=5
    )
    
    print("=" * 50)
    print("任务发送结果:")
    print(f"  成功: {result.get('success', False)}")
    print(f"  返回码: {result.get('returncode', 'N/A')}")
    
    if result.get('error'):
        print(f"  错误: {result['error']}")
    
    if result.get('text'):
        print(f"\n输出内容:\n{result['text'][:500]}...")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
