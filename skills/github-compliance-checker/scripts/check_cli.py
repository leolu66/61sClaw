#!/usr/bin/env python3
"""
GitHub 合规检查命令行工具

使用方法:
    python check_cli.py [check|fix|report]
    
    check  - 仅检查并报告
    fix    - 检查并自动修复
    report - 生成详细报告
"""

import sys
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from compliance_checker import ComplianceChecker


def main():
    parser = argparse.ArgumentParser(
        description="GitHub 合规检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python check_cli.py check    # 仅检查
  python check_cli.py fix      # 检查并修复
  python check_cli.py report   # 生成详细报告
        """
    )
    
    parser.add_argument(
        "command",
        choices=["check", "fix", "report"],
        help="执行命令: check=检查, fix=修复, report=报告"
    )
    
    args = parser.parse_args()
    
    checker = ComplianceChecker()
    
    if args.command == "check":
        print("🔍 正在检查 Git 暂存区文件...")
        issues = checker.check_staged_files()
        
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个合规问题:\n")
            report = checker.generate_report(issues, auto_mode=False)
            print(report)
            return 1
        else:
            print("\n✅ 没有发现合规问题，可以安全提交。")
            return 0
    
    elif args.command == "fix":
        print("🔍 正在检查 Git 暂存区文件...")
        issues = checker.check_staged_files()
        
        if not issues:
            print("\n✅ 没有发现合规问题。")
            return 0
        
        print(f"\n⚠️  发现 {len(issues)} 个合规问题，正在自动修复...\n")
        
        fix_result = checker.auto_fix(issues)
        
        report = checker.generate_report(issues, fix_result, auto_mode=True)
        print(report)
        
        return 0 if fix_result["success"] else 1
    
    elif args.command == "report":
        print("🔍 正在生成详细报告...")
        issues = checker.check_all_files()
        
        print(f"\n{'='*60}")
        print("GitHub 合规检查 - 完整仓库扫描")
        print(f"{'='*60}\n")
        
        if issues:
            print(f"发现 {len(issues)} 个合规问题:\n")
            
            # 按风险等级分组
            from compliance_checker import RiskLevel
            high = [i for i in issues if i.risk_level == RiskLevel.HIGH]
            medium = [i for i in issues if i.risk_level == RiskLevel.MEDIUM]
            low = [i for i in issues if i.risk_level == RiskLevel.LOW]
            
            print(f"🔴 高风险: {len(high)} 个")
            print(f"🟡 中风险: {len(medium)} 个")
            print(f"🟢 低风险: {len(low)} 个")
            print()
            
            report = checker.generate_report(issues, auto_mode=False)
            print(report)
        else:
            print("✅ 没有发现合规问题。")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())
