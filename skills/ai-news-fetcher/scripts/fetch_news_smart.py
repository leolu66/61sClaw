#!/usr/bin/env python3
"""
智能 AI 新闻获取 - 先检查当天文件是否存在，不存在再抓取
"""
import os
from datetime import datetime

# 新闻目录
NEWS_DIR = r"D:\anthropic\AI新闻"

# 当天文件名
today = datetime.now().strftime("%Y%m%d")
today_file = os.path.join(NEWS_DIR, f"ainews_{today}.md")

def main():
    # 检查当天文件是否存在
    if os.path.exists(today_file):
        print(f"找到当天新闻文件: {today_file}")
        print("=" * 60)
        # 读取并打印文件内容
        with open(today_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 打印（跳过最后的文件路径信息）
            lines = content.split('\n')
            # 找到最后的 --- 分隔线，在那之前的内容
            output = []
            for line in lines:
                if '完整报告已保存到' in line:
                    break
                output.append(line)
            print('\n'.join(output))
    else:
        print(f"未找到当天新闻文件: {today_file}")
        print("开始抓取最新新闻...")
        print("=" * 60)
        
        # 调用抓取脚本
        import subprocess
        import sys
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fetch_script = os.path.join(script_dir, "generate_report.py")
        
        subprocess.run([sys.executable, fetch_script])
        
        # 再次检查文件
        if os.path.exists(today_file):
            with open(today_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                output = []
                for line in lines:
                    if '完整报告已保存到' in line:
                        break
                    output.append(line)
                print('\n'.join(output))

if __name__ == "__main__":
    main()
