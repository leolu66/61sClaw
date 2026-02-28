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


def view_report(open_file=False, summarize=False):
    """
    查看最新账单报告

    Args:
        open_file: 是否直接用系统默认应用打开文件（WebChat/计算机渠道）
        summarize: 是否总结报告内容（飞书渠道）
    """
    # 报告目录
    script_path = os.path.abspath(__file__)
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path))))
    report_dir = os.path.join(workspace_root, 'agfiles', 'billing_report')

    # 查找最新报告
    filepath, filename, mtime = find_latest_report(report_dir)

    if filepath is None:
        if not os.path.exists(report_dir):
            return False, f"报告目录不存在: {report_dir}"
        else:
            return False, "报告目录中没有找到账单报告文件"

    # 如果是 WebChat/计算机渠道，直接打开文件
    if open_file:
        try:
            if sys.platform.startswith('win'):
                os.startfile(filepath)
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{filepath}"')
            else:
                os.system(f'xdg-open "{filepath}"')
            return True, f"✅ 已打开账单报告: {filename}"
        except Exception as e:
            return False, f"打开报告失败: {str(e)}"

    # 如果是飞书渠道，读取并总结内容
    if summarize:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"读取报告失败: {str(e)}"

    # 默认：直接打开文件
    return view_report(open_file=True, summarize=False)


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
    """
    主函数

    命令行参数：
    - 无参数：默认用系统默认应用打开报告（WebChat/本地渠道）
    - --list：列出所有账单报告
    - --summarize：读取并输出报告内容（飞书渠道）
    - --channel <channel>：指定渠道（webchat/feishu），自动选择行为
    """
    channel = None
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            # 列出所有报告
            list_reports()
            return
        elif sys.argv[1] == '--summarize':
            # 强制总结模式
            success, result = view_report(open_file=False, summarize=True)
            if success:
                print(result)
            else:
                print(f"❌ {result}")
            return
        elif sys.argv[1] == '--channel' and len(sys.argv) > 2:
            channel = sys.argv[2].lower()
    
    # 根据渠道自动选择行为
    if channel == 'feishu':
        # 飞书渠道：读取并输出报告内容
        success, result = view_report(open_file=False, summarize=True)
        if success:
            print(result)
        else:
            print(f"❌ {result}")
    else:
        # 默认（WebChat/本地）：直接打开文件
        success, result = view_report(open_file=True, summarize=False)
        if success:
            print(result)
        else:
            print(f"❌ {result}")


if __name__ == '__main__':
    main()
