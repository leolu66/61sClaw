#!/usr/bin/env python3
"""
GitHub 合规检查命令行工具

使用方法:
    python check_cli.py [check|fix|report|committed]
    
    check      - 检查暂存区
    fix        - 检查并自动修复暂存区
    report     - 生成完整报告（包括已提交文件）
    committed  - 检查已提交的文件（发现不应上传的隐私文件）
"""

import sys
import argparse
from pathlib import Path

# 解决 Windows 中文编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from compliance_checker import ComplianceChecker


def main():
    parser = argparse.ArgumentParser(
        description="GitHub 合规检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python check_cli.py check       # 检查暂存区
  python check_cli.py fix         # 检查并修复暂存区
  python check_cli.py report      # 完整报告（所有文件）
  python check_cli.py committed   # 检查已提交的文件
        """
    )
    
    parser.add_argument(
        "command",
        choices=["check", "fix", "report", "committed"],
        help="执行命令: check=检查暂存区, fix=修复, report=完整报告, committed=检查已提交文件"
    )
    
    args = parser.parse_args()
    
    checker = ComplianceChecker()
    
    if args.command == "check":
        print("[OK] 正在检查 Git 暂存区文件...")
        issues = checker.check_staged_files()
        
        if issues:
            print(f"\n[!] 发现 {len(issues)} 个合规问题:\n")
            report = checker.generate_report(issues, auto_mode=False, check_type="staged")
            print(report)
            return 1
        else:
            print("\n[OK] 暂存区没有发现合规问题，可以安全提交。")
            return 0
    
    elif args.command == "fix":
        print("[OK] 正在检查 Git 暂存区文件...")
        issues = checker.check_staged_files()
        
        if not issues:
            print("\n[OK] 没有发现合规问题。")
            return 0
        
        print(f"\n[!] 发现 {len(issues)} 个合规问题，正在自动修复...\n")
        
        fix_result = checker.auto_fix(issues)
        
        report = checker.generate_report(issues, fix_result, auto_mode=True, check_type="staged")
        print(report)
        
        return 0 if fix_result["success"] else 1
    
    elif args.command == "committed":
        print("[OK] 正在检查已提交到仓库的文件...")
        print("[INFO] 这会检查所有已跟踪的文件，发现不应上传的隐私文件\n")
        
        issues = checker.check_committed_files()
        
        if issues:
            print(f"[!] 发现 {len(issues)} 个已提交的合规问题:\n")
            report = checker.generate_report(issues, auto_mode=False, check_type="committed")
            print(report)
            print("\n[!] 警告: 这些文件已经在 Git 仓库中，需要从仓库中移除:")
            print("   git rm --cached <file>")
            print("   git commit -m '移除隐私文件'")
            return 1
        else:
            print("[OK] 已提交文件中没有发现合规问题。")
            return 0
    
    elif args.command == "report":
        print("[OK] 正在生成完整合规报告...")
        
        # 检查暂存区
        staged_issues = checker.check_staged_files()
        # 检查已提交文件
        committed_issues = checker.check_committed_files()
        
        print(f"\n{'='*60}")
        print("GitHub 合规检查 - 完整报告")
        print(f"{'='*60}\n")
        
        # 暂存区报告
        print("【暂存区文件】")
        if staged_issues:
            print(f"[!] 发现 {len(staged_issues)} 个问题\n")
            report = checker.generate_report(staged_issues, auto_mode=False, check_type="staged")
            print(report)
        else:
            print("[OK] 没有问题\n")
        
        # 已提交文件报告
        print("\n【已提交文件】")
        if committed_issues:
            print(f"[!] 发现 {len(committed_issues)} 个问题\n")
            report = checker.generate_report(committed_issues, auto_mode=False, check_type="committed")
            print(report)
        else:
            print("[OK] 没有问题\n")
        
        # 汇总
        total = len(staged_issues) + len(committed_issues)
        print(f"{'='*60}")
        print(f"汇总: 共发现 {total} 个合规问题")
        print(f"  - 暂存区: {len(staged_issues)} 个")
        print(f"  - 已提交: {len(committed_issues)} 个")
        print(f"{'='*60}")
        
        return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
