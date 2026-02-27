#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能 AI 新闻获取 - 增强编码容错性 v1.1
修复：
- 控制台输出 UTF-8 编码
- 路径编码容错
- 文件读取多种编码支持
"""
import os
import sys
import codecs
from datetime import datetime

# ===== 编码修复开始 =====
# 设置 Windows 控制台输出编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
    except Exception as e:
        print(f"[WARN] 设置 UTF-8 编码失败：{e}", file=sys.stderr)
# ===== 编码修复结束 =====

def find_today_file(news_dir):
    """查找当天的新闻文件（支持带序号的文件名）"""
    today = datetime.now().strftime("%Y%m%d")
    
    # 先检查标准文件名
    standard_file = os.path.join(news_dir, f"ainews_{today}.md")
    if os.path.exists(standard_file):
        return standard_file
    
    # 查找带序号的文件（ainews_20260226_1.md, ainews_20260226_2.md 等）
    pattern = f"ainews_{today}"
    try:
        files = [f for f in os.listdir(news_dir) if f.startswith(pattern) and f.endswith('.md')]
        if files:
            # 返回最新的文件（按修改时间）
            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(news_dir, f)))
            return os.path.join(news_dir, latest)
    except Exception as e:
        print(f"[WARN] 查找文件失败：{e}", file=sys.stderr)
    
    # 返回标准路径（用于创建新文件）
    return standard_file

# 新闻目录（英文名称，避免编码问题）
NEWS_DIR = r"D:\anthropic\AI_News"

# 查找当天文件
today_file = find_today_file(NEWS_DIR)

def read_file_safe(filepath):
    """安全读取文件，支持多种编码"""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[WARN] 读取失败 ({encoding}): {e}", file=sys.stderr)
            continue
    
    raise ValueError(f"无法解码文件，尝试了 {len(encodings)} 种编码")

def main():
    print("=" * 60)
    print("AI 新闻日报 - 智能获取 v1.1")
    print("=" * 60)
    print()
    
    # 检查目录是否存在
    if not os.path.exists(NEWS_DIR):
        print(f"[WARN] 新闻目录不存在，创建：{NEWS_DIR}")
        try:
            os.makedirs(NEWS_DIR, exist_ok=True)
            print(f"[OK] 目录创建成功")
        except Exception as e:
            print(f"[ERROR] 目录创建失败：{e}")
            print(f"提示：请手动创建目录")
            return
    
    # 检查当天文件是否存在
    if os.path.exists(today_file):
        print(f"[OK] 找到当天新闻文件")
        print()
        
        # 读取并打印文件内容（带容错）
        try:
            content = read_file_safe(today_file)
            
            # 打印（跳过最后的文件路径信息）
            lines = content.split('\n')
            output = []
            for line in lines:
                if '完整报告已保存到' in line:
                    break
                output.append(line)
            
            print('\n'.join(output))
            
        except Exception as e:
            print(f"[ERROR] 读取文件失败：{e}")
            print()
            print("建议：")
            print("1. 检查文件是否存在")
            print(f"   路径：{today_file}")
            print("2. 检查文件编码（应为 UTF-8）")
    else:
        print(f"[INFO] 未找到当天新闻文件")
        print()
        print("开始抓取最新新闻...")
        print()
        
        # 调用抓取脚本
        import subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fetch_script = os.path.join(script_dir, "generate_report.py")
        
        if not os.path.exists(fetch_script):
            print(f"[ERROR] 抓取脚本不存在：{fetch_script}")
            return
        
        try:
            result = subprocess.run(
                [sys.executable, fetch_script],
                capture_output=False,
                encoding='utf-8',
                errors='replace',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            
            if result.returncode != 0:
                print(f"[ERROR] 抓取失败，退出码：{result.returncode}")
                return
                
        except Exception as e:
            print(f"[ERROR] 执行脚本失败：{e}")
            return
        
        # 再次检查文件
        if os.path.exists(today_file):
            print()
            print("[OK] 新闻抓取成功")
            print()
            try:
                content = read_file_safe(today_file)
                lines = content.split('\n')
                output = []
                for line in lines:
                    if '完整报告已保存到' in line:
                        break
                    output.append(line)
                print('\n'.join(output))
            except Exception as e:
                print(f"[ERROR] 读取失败：{e}")
        else:
            print(f"[ERROR] 抓取完成但未找到文件")
            print(f"预期路径：{today_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    except Exception as e:
        print(f"\n[ERROR] 程序异常：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
