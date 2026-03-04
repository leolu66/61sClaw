#!/usr/bin/env python3
"""
GitHub 合规检查器 - 改进版
检查 Git 暂存区和已提交文件是否符合上传规则

使用方法:
    from compliance_checker import ComplianceChecker
    
    checker = ComplianceChecker()
    
    # 检查暂存区（准备提交的文件）
    staged_issues = checker.check_staged_files()
    
    # 检查已提交的文件（已经在仓库中的）
    committed_issues = checker.check_committed_files()
    
    # 自动修复
    checker.auto_fix(issues)
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceIssue:
    """合规问题"""
    file_path: str
    issue_type: str
    risk_level: RiskLevel
    description: str
    rule: str


class ComplianceChecker:
    """GitHub 合规检查器"""
    
    # 合规规则定义
    RULES = {
        # 高风险 - 隐私保护
        "memory.md": {
            "pattern": r"^MEMORY\.md$",
            "type": "个人记忆文件",
            "risk": RiskLevel.HIGH,
            "description": "包含长期记忆和个人偏好"
        },
        "user_config": {
            "pattern": r"^(USER|SOUL|AGENTS|IDENTITY|HEARTBEAT|BOOTSTRAP|CORE_PRINCIPLES)\.md$",
            "type": "用户配置文件",
            "risk": RiskLevel.HIGH,
            "description": "包含用户个人信息和配置"
        },
        "logs": {
            "pattern": r"^logs/.*$",
            "type": "工作日志",
            "risk": RiskLevel.HIGH,
            "description": "工作日志文件，可能包含敏感信息"
        },
        "user_data": {
            "pattern": r"^(datas|data|agfiles)/.*$",
            "type": "用户数据",
            "risk": RiskLevel.HIGH,
            "description": "用户数据目录"
        },
        
        # 中风险
        "tools_md": {
            "pattern": r"^TOOLS\.md$",
            "type": "本地工具配置",
            "risk": RiskLevel.MEDIUM,
            "description": "本地工具配置，包含环境特定信息"
        },
        "skill_data": {
            "pattern": r"^skills/[^/]+/data/.*$",
            "type": "技能数据",
            "risk": RiskLevel.MEDIUM,
            "description": "技能运行时数据"
        },
        "skill_node_modules": {
            "pattern": r"^skills/[^/]+/node_modules/.*$",
            "type": "技能依赖",
            "risk": RiskLevel.MEDIUM,
            "description": "技能 node_modules 目录"
        },
        
        # 低风险 - 技术规范
        "pycache": {
            "pattern": r"^__pycache__/.*$",
            "type": "Python 缓存",
            "risk": RiskLevel.LOW,
            "description": "Python 缓存文件"
        },
        "pyc": {
            "pattern": r".*\.pyc$",
            "type": "Python 字节码",
            "risk": RiskLevel.LOW,
            "description": "Python 编译后的字节码"
        },
        "pyo": {
            "pattern": r".*\.pyo$",
            "type": "Python 优化字节码",
            "risk": RiskLevel.LOW,
            "description": "Python 优化后的字节码"
        },
        "vscode": {
            "pattern": r"^\.vscode/.*$",
            "type": "VS Code 配置",
            "risk": RiskLevel.LOW,
            "description": "VS Code 编辑器配置"
        },
        "idea": {
            "pattern": r"^\.idea/.*$",
            "type": "IDEA 配置",
            "risk": RiskLevel.LOW,
            "description": "JetBrains IDEA 配置"
        },
        "swp": {
            "pattern": r".*\.swp$",
            "type": "Vim 交换文件",
            "risk": RiskLevel.LOW,
            "description": "Vim 编辑器交换文件"
        },
        "swo": {
            "pattern": r".*\.swo$",
            "type": "Vim 交换文件",
            "risk": RiskLevel.LOW,
            "description": "Vim 编辑器交换文件"
        },
        "tmp": {
            "pattern": r"^(tmp|temp)/.*$|.*\.tmp$",
            "type": "临时文件",
            "risk": RiskLevel.LOW,
            "description": "临时文件"
        },
        "ds_store": {
            "pattern": r"^\.DS_Store$",
            "type": "macOS 系统文件",
            "risk": RiskLevel.LOW,
            "description": "macOS 系统文件"
        },
        "thumbs": {
            "pattern": r"^Thumbs\.db$",
            "type": "Windows 缩略图",
            "risk": RiskLevel.LOW,
            "description": "Windows 缩略图缓存"
        },
        "debug_files": {
            "pattern": r"^(debug|test).*\.py$|.*_(debug|test|backup|old)\.py$",
            "type": "调试文件",
            "risk": RiskLevel.LOW,
            "description": "调试和测试文件"
        }
    }
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        初始化检查器
        
        Args:
            repo_path: 仓库路径，默认为当前目录
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.issues: List[ComplianceIssue] = []
    
    def get_staged_files(self) -> List[str]:
        """
        获取 Git 暂存区的文件列表
        
        Returns:
            文件路径列表
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]
            
        except subprocess.CalledProcessError as e:
            print(f"[错误] 获取暂存区文件失败: {e}")
            return []
        except FileNotFoundError:
            print("[错误] 未找到 git 命令")
            return []
    
    def get_committed_files(self) -> List[str]:
        """
        获取 Git 仓库中已跟踪的文件列表（包括已提交的）
        
        Returns:
            文件路径列表
        """
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]
            
        except subprocess.CalledProcessError as e:
            print(f"[错误] 获取已跟踪文件失败: {e}")
            return []
        except FileNotFoundError:
            print("[错误] 未找到 git 命令")
            return []
    
    def check_file(self, file_path: str) -> Optional[ComplianceIssue]:
        """
        检查单个文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            如果发现违规返回 ComplianceIssue，否则返回 None
        """
        for rule_name, rule in self.RULES.items():
            if re.match(rule["pattern"], file_path):
                return ComplianceIssue(
                    file_path=file_path,
                    issue_type=rule["type"],
                    risk_level=rule["risk"],
                    description=rule["description"],
                    rule=rule_name
                )
        return None
    
    def check_staged_files(self) -> List[ComplianceIssue]:
        """
        检查暂存区的所有文件
        
        Returns:
            违规问题列表
        """
        self.issues = []
        staged_files = self.get_staged_files()
        
        for file_path in staged_files:
            issue = self.check_file(file_path)
            if issue:
                self.issues.append(issue)
        
        return self.issues
    
    def check_committed_files(self) -> List[ComplianceIssue]:
        """
        检查已提交到仓库的文件（发现不应上传的隐私文件）
        
        Returns:
            违规问题列表
        """
        self.issues = []
        committed_files = self.get_committed_files()
        
        for file_path in committed_files:
            issue = self.check_file(file_path)
            if issue:
                self.issues.append(issue)
        
        return self.issues
    
    def remove_from_staging(self, file_path: str) -> bool:
        """
        从 Git 暂存区移除文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否成功
        """
        try:
            subprocess.run(
                ["git", "rm", "--cached", file_path],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"[错误] 移除文件失败 {file_path}: {e}")
            return False
    
    def auto_fix(self, issues: Optional[List[ComplianceIssue]] = None) -> Dict[str, any]:
        """
        自动修复问题（从暂存区移除不合规文件）
        
        Args:
            issues: 问题列表，默认为上次检查的结果
        
        Returns:
            修复结果统计
        """
        if issues is None:
            issues = self.issues
        
        if not issues:
            return {
                "success": True,
                "removed": 0,
                "failed": 0,
                "details": []
            }
        
        removed = 0
        failed = 0
        details = []
        
        for issue in issues:
            if self.remove_from_staging(issue.file_path):
                removed += 1
                details.append({
                    "file": issue.file_path,
                    "status": "removed",
                    "type": issue.issue_type
                })
            else:
                failed += 1
                details.append({
                    "file": issue.file_path,
                    "status": "failed",
                    "type": issue.issue_type
                })
        
        return {
            "success": failed == 0,
            "removed": removed,
            "failed": failed,
            "details": details
        }
    
    def generate_report(
        self,
        issues: Optional[List[ComplianceIssue]] = None,
        fix_result: Optional[Dict] = None,
        auto_mode: bool = False,
        check_type: str = "staged"
    ) -> str:
        """
        生成检查报告
        
        Args:
            issues: 问题列表
            fix_result: 修复结果
            auto_mode: 是否为自动修正模式
            check_type: 检查类型 (staged/committed)
        
        Returns:
            报告文本
        """
        if issues is None:
            issues = self.issues
        
        lines = []
        lines.append("## GitHub 合规检查报告")
        lines.append("")
        
        if check_type == "staged":
            lines.append(f"**检查范围**: 暂存区文件（准备提交）")
        else:
            lines.append(f"**检查范围**: 已提交文件（已在仓库中）")
        
        lines.append(f"**检查模式**: {'自动修正' if auto_mode else '仅检查'}")
        
        if not issues:
            lines.append("")
            lines.append("[OK] **没有发现合规问题。**")
            return "\n".join(lines)
        
        # 按风险等级分组
        high_risk = [i for i in issues if i.risk_level == RiskLevel.HIGH]
        medium_risk = [i for i in issues if i.risk_level == RiskLevel.MEDIUM]
        low_risk = [i for i in issues if i.risk_level == RiskLevel.LOW]
        
        lines.append("")
        lines.append(f"### 发现的问题 ({len(issues)} 个)")
        lines.append("")
        
        # 高风险
        if high_risk:
            lines.append(f"#### [H] 高风险 ({len(high_risk)} 个)")
            lines.append("")
            lines.append("| 文件路径 | 问题类型 | 说明 |")
            lines.append("|---------|---------|------|")
            for issue in high_risk:
                lines.append(f"| `{issue.file_path}` | {issue.issue_type} | {issue.description} |")
            lines.append("")
        
        # 中风险
        if medium_risk:
            lines.append(f"#### [M] 中风险 ({len(medium_risk)} 个)")
            lines.append("")
            lines.append("| 文件路径 | 问题类型 | 说明 |")
            lines.append("|---------|---------|------|")
            for issue in medium_risk:
                lines.append(f"| `{issue.file_path}` | {issue.issue_type} | {issue.description} |")
            lines.append("")
        
        # 低风险
        if low_risk:
            lines.append(f"#### [L] 低风险 ({len(low_risk)} 个)")
            lines.append("")
            lines.append("| 文件路径 | 问题类型 | 说明 |")
            lines.append("|---------|---------|------|")
            for issue in low_risk:
                lines.append(f"| `{issue.file_path}` | {issue.issue_type} | {issue.description} |")
            lines.append("")
        
        # 修复结果
        if fix_result:
            lines.append("### 修复结果")
            lines.append("")
            lines.append(f"- 成功移除: {fix_result['removed']} 个文件")
            if fix_result['failed'] > 0:
                lines.append(f"- 移除失败: {fix_result['failed']} 个文件")
            lines.append("")
            
            if fix_result['success']:
                lines.append("[OK] **所有不合规文件已处理。**")
            else:
                lines.append("[!] **部分文件处理失败，请手动检查。**")
        elif not auto_mode:
            # 需要确认的模式
            lines.append("### 建议操作")
            lines.append("")
            if check_type == "staged":
                lines.append("1. **从 Git 暂存区移除这些文件**")
            else:
                lines.append("1. **从 Git 仓库中移除这些文件**（git rm --cached）")
            lines.append("2. **更新 .gitignore** 防止再次提交")
            lines.append("")
            lines.append("### 确认执行")
            lines.append("")
            lines.append("是否执行修复操作？")
            lines.append('- 回复 "确认" 或 "是" 执行修复')
            lines.append('- 回复 "取消" 或 "否" 保持现状')
        
        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    checker = ComplianceChecker()
    
    print("=== 检查暂存区文件 ===")
    staged_issues = checker.check_staged_files()
    
    print("\n=== 检查已提交文件 ===")
    committed_issues = checker.check_committed_files()
    
    all_issues = staged_issues + committed_issues
    
    if all_issues:
        print(f"\n发现 {len(all_issues)} 个合规问题:")
        for issue in all_issues:
            risk_icon = "[H]" if issue.risk_level == RiskLevel.HIGH else "[M]" if issue.risk_level == RiskLevel.MEDIUM else "[L]"
            print(f"{risk_icon} {issue.file_path} - {issue.issue_type}")
    else:
        print("\n[OK] 没有发现合规问题")
