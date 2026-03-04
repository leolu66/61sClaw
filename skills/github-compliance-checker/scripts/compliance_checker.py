#!/usr/bin/env python3
"""
GitHub 合规检查器
检查 Git 暂存区文件是否符合上传规则

使用方法:
    from compliance_checker import ComplianceChecker
    
    checker = ComplianceChecker()
    
    # 检查暂存区
    issues = checker.check_staged_files()
    
    # 自动修复
    checker.auto_fix(issues)
    
    # 生成报告
    report = checker.generate_report(issues)
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
        # 🔴 高风险 - 隐私保护
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
        "memory_dir": {
            "pattern": r"^memory/.*$",
            "type": "历史记忆（已废弃）",
            "risk": RiskLevel.HIGH,
            "description": "历史记忆目录，已废弃，建议删除"
        },
        "user_data": {
            "pattern": r"^(datas|data|agfiles)/.*$",
            "type": "用户数据",
            "risk": RiskLevel.HIGH,
            "description": "用户数据目录"
        },
        
        # 🟡 中风险
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
        
        # 🟢 低风险 - 技术规范
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
    
    def check_all_files(self) -> List[ComplianceIssue]:
        """
        检查仓库中的所有文件（包括未暂存的）
        
        Returns:
            违规问题列表
        """
        self.issues = []
        
        try:
            # 获取所有被 Git 跟踪的文件
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            all_files = result.stdout.strip().split("\n")
            
            for file_path in all_files:
                if file_path:
                    issue = self.check_file(file_path)
                    if issue:
                        self.issues.append(issue)
            
            return self.issues
            
        except subprocess.CalledProcessError as e:
            print(f"[错误] 获取文件列表失败: {e}")
            return []
    
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
        auto_mode: bool = False
    ) -> str:
        """
        生成检查报告
        
        Args:
            issues: 问题列表
            fix_result: 修复结果
            auto_mode: 是否为自动修正模式
        
        Returns:
            报告文本
        """
        if issues is None:
            issues = self.issues
        
        lines = []
        lines.append("## GitHub 合规检查报告")
        lines.append("")
        lines.append(f"**检查模式**: {'自动修正' if auto_mode else '仅检查'}")
        
        if not issues:
            lines.append("")
            lines.append("✅ **没有发现合规问题，可以安全提交。**")
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
            lines.append(f"#### 🔴 高风险 ({len(high_risk)} 个)")
            lines.append("")
            lines.append("| 文件路径 | 问题类型 | 说明 |")
            lines.append("|---------|---------|------|")
            for issue in high_risk:
                lines.append(f"| `{issue.file_path}` | {issue.issue_type} | {issue.description} |")
            lines.append("")
        
        # 中风险
        if medium_risk:
            lines.append(f"#### 🟡 中风险 ({len(medium_risk)} 个)")
            lines.append("")
            lines.append("| 文件路径 | 问题类型 | 说明 |")
            lines.append("|---------|---------|------|")
            for issue in medium_risk:
                lines.append(f"| `{issue.file_path}` | {issue.issue_type} | {issue.description} |")
            lines.append("")
        
        # 低风险
        if low_risk:
            lines.append(f"#### 🟢 低风险 ({len(low_risk)} 个)")
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
                lines.append("✅ **所有不合规文件已处理，可以安全提交。**")
            else:
                lines.append("⚠️ **部分文件处理失败，请手动检查。**")
        elif not auto_mode:
            # 需要确认的模式
            lines.append("### 建议操作")
            lines.append("")
            lines.append("1. **从 Git 暂存区移除这些文件**")
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
    issues = checker.check_staged_files()
    
    if issues:
        print(f"\n发现 {len(issues)} 个合规问题:")
        for issue in issues:
            risk_icon = "🔴" if issue.risk_level == RiskLevel.HIGH else "🟡" if issue.risk_level == RiskLevel.MEDIUM else "🟢"
            print(f"{risk_icon} {issue.file_path} - {issue.issue_type}")
        
        print("\n=== 生成报告 ===")
        report = checker.generate_report(issues, auto_mode=False)
        print(report)
        
        print("\n=== 自动修复 ===")
        fix_result = checker.auto_fix(issues)
        print(f"移除: {fix_result['removed']}, 失败: {fix_result['failed']}")
        
        print("\n=== 修复后报告 ===")
        report = checker.generate_report(issues, fix_result, auto_mode=True)
        print(report)
    else:
        print("✅ 没有发现合规问题")
