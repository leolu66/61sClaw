#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    instruction = """请分析账单文件 D:\\projects\\workspace\\shared\\input\\billing_2026-02-09_2026-03-04.csv

任务要求：
1. 读取 CSV 账单文件
2. 分析消费数据（按模型、按日期、按类型等维度）
3. 生成可视化图表（如果有绘图能力）
4. 生成完整的账单分析报告

输出要求：
- 输出目录: D:\\projects\\workspace\\shared\\output\\billing-report-20260305\\
- 报告文件: report.md（包含分析结论和图表）
- 数据文件: analysis.json（包含统计数据）

完成后请说明：
1. 分析了哪些维度
2. 有什么关键发现
3. 生成了哪些文件"""
    
    print("[发送账单分析任务] 给 Claude Code...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["claude", "-p", instruction, "--permission-mode", "acceptEdits"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600,  # 10分钟超时
            cwd="D:\\projects\\workspace\\shared"
        )
        
        print(f"返回码: {result.returncode}")
        print()
        
        if result.stdout:
            print("【Claude Code 输出】")
            print(result.stdout[:3000])
        
        if result.stderr:
            print("\n【错误输出】")
            print(result.stderr[:500])
        
        print("=" * 60)
        
    except Exception as e:
        print(f"[错误] {e}")

if __name__ == "__main__":
    main()
