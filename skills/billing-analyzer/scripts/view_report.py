# -*- coding: utf-8 -*-
"""
查看账单报告
直接显示已有的账单报告，如果不存在则提示用户需要先生成报告
"""
import os
import sys
import io
from datetime import datetime
from pathlib import Path

# 修复stdout编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def find_latest_report(report_dir):
    """
    查找最新的账单报告文件

    Args:
        report_dir: 报告目录路径

    Returns:
        (filepath, filename, mtime): 最新报告的完整路径、文件名、修改时间
    """
    if not os.path.exists(report_dir):
        return None, None, None

    # 查找所有 .md 报告文件
    md_files = []
    for filename in os.listdir(report_dir):
        if filename.endswith('.md') and filename not in ['README.md', 'readme.md']:
            filepath = os.path.join(report_dir, filename)
            mtime = os.path.getmtime(filepath)
            md_files.append((filepath, filename, mtime))

    # 按修改时间排序，取最新的
    if md_files:
        md_files.sort(key=lambda x: x[2], reverse=True)
        return md_files[0]

    return None, None, None


def format_mtime(mtime):
    """格式化修改时间"""
    dt = datetime.fromtimestamp(mtime)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def view_report():
    """查看最新账单报告"""
    # 报告目录
    script_path = os.path.abspath(__file__)
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path))))
    report_dir = os.path.join(workspace_root, 'agfiles', 'billing_report')

    print("="*60)
    print("📊 查看账单报告")
    print("="*60)

    # 查找最新报告
    filepath, filename, mtime = find_latest_report(report_dir)

    if filepath is None:
        if not os.path.exists(report_dir):
            print(f"\n❌ 报告目录不存在: {report_dir}")
        else:
            print(f"\n❌ 报告目录中没有找到账单报告文件")
        print("\n💡 提示：")
        print("   1. 请先生成账单报告：")
        print("      python billing_analyzer.py <账单文件名>")
        print("   2. 或提供账单文件路径，我可以帮你生成报告")
        print("="*60)
        return False

    # 读取报告内容
    print(f"\n📁 最新报告文件: {filename}")
    print(f"🕒 修改时间: {format_mtime(mtime)}")
    print("="*60)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        print("\n" + content)
        print("="*60)
        print(f"\n📍 报告路径: {filepath}")
        print("✅ 查看完成")

        return True

    except Exception as e:
        print(f"\n❌ 读取报告失败: {str(e)}")
        print(f"📍 文件路径: {filepath}")
        return False


def list_reports():
    """列出所有账单报告"""
    script_path = os.path.abspath(__file__)
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path))))
    report_dir = os.path.join(workspace_root, 'agfiles', 'billing_report')

    if not os.path.exists(report_dir):
        print(f"\n❌ 报告目录不存在: {report_dir}")
        return

    md_files = []
    for filename in os.listdir(report_dir):
        if filename.endswith('.md') and filename not in ['README.md', 'readme.md']:
            filepath = os.path.join(report_dir, filename)
            mtime = os.path.getmtime(filepath)
            size = os.path.getsize(filepath)
            md_files.append((filename, mtime, size))

    if not md_files:
        print(f"\n❌ 报告目录中没有找到账单报告文件")
        return

    # 按修改时间排序
    md_files.sort(key=lambda x: x[1], reverse=True)

    print("\n" + "="*60)
    print("📋 账单报告列表")
    print("="*60)
    print(f"{'文件名':<50} {'修改时间':<20} {'大小':<10}")
    print("-"*80)

    for filename, mtime, size in md_files:
        mtime_str = format_mtime(mtime)
        size_str = f"{size/1024:.1f}KB"
        print(f"{filename:<50} {mtime_str:<20} {size_str:<10}")

    print("="*60)


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        # 列出所有报告
        list_reports()
    else:
        # 查看最新报告
        view_report()


if __name__ == '__main__':
    main()
