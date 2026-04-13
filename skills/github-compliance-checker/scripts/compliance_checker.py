#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 设置 stdout 编码为 utf-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


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
    
    # 确认记录文件路径（放在技能自己的 data 目录下）
    APPROVALS_FILE = Path(__file__).parent.parent / 'data' / '.compliance_approvals.json'
    
    # 允许在根目录存在的目录（白名单）
    ALLOWED_TOP_LEVEL_DIRS = {
        'skills',           # 技能目录（核心，唯一允许同步的代码目录）
        'scripts',          # 公共脚本目录
        '.git',             # Git 系统目录（必须保留，不会同步到远程）
    }
    
    # 允许在根目录存在的文件（白名单）
    ALLOWED_TOP_LEVEL_FILES = {
        '.gitignore',       # Git 忽略规则文件（唯一允许同步的根目录文件）
    }
    
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
        self.approved_items: Dict[str, dict] = self._load_approvals()
    
    def _load_approvals(self) -> Dict[str, dict]:
        """加载已确认的记录"""
        try:
            if self.APPROVALS_FILE.exists():
                import json
                with open(self.APPROVALS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[警告] 加载确认记录失败: {e}")
        return {}
    
    def _save_approvals(self):
        """保存确认记录"""
        try:
            self.APPROVALS_FILE.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(self.APPROVALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.approved_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 保存确认记录失败: {e}")
    
    def allow_item(self, item_path: str, reason: str = ""):
        """
        允许某个项目同步到GitHub（加入白名单，下次检查将忽略）
        
        Args:
            item_path: 项目路径（文件或目录）
            reason: 允许原因
        """
        import time
        self.approved_items[item_path] = {
            'approved_at': time.time(),
            'reason': reason,
            'approved_by': 'user',
            'action': 'allow'
        }
        self._save_approvals()
        print(f"[OK] 已允许同步: {item_path}")
    
    def deny_item(self, item_path: str) -> bool:
        """
        禁止某个项目同步到GitHub：添加到.gitignore，并从Git仓库删除
        
        Args:
            item_path: 项目路径（文件或目录）
            
        Returns:
            是否成功
        """
        try:
            # 1. 添加到 .gitignore
            gitignore_path = self.repo_path / '.gitignore'
            
            # 检查是否已经存在
            if gitignore_path.exists():
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if item_path in content or f"{item_path}/" in content:
                    print(f"[INFO] {item_path} 已在 .gitignore 中")
                else:
                    with open(gitignore_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n{item_path}\n")
                    print(f"[OK] 已添加 {item_path} 到 .gitignore")
            else:
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write(f"{item_path}\n")
                print(f"[OK] 已创建 .gitignore 并添加 {item_path}")
            
            # 2. 从Git仓库移除（如果已经跟踪）
            try:
                subprocess.run(
                    ["git", "rm", "-r", "--cached", item_path],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=True
                )
                print(f"[OK] 已将 {item_path} 从Git仓库移除")
            except subprocess.CalledProcessError:
                # 文件可能未被跟踪，忽略错误
                pass
            
            # 3. 记录到已确认列表
            import time
            self.approved_items[item_path] = {
                'approved_at': time.time(),
                'reason': '用户禁止同步',
                'approved_by': 'user',
                'action': 'deny'
            }
            self._save_approvals()
            
            return True
            
        except Exception as e:
            print(f"[错误] 禁止同步失败 {item_path}: {e}")
            return False
    
    def is_approved(self, item_path: str) -> bool:
        """检查项目是否已确认（允许或禁止都算已处理）"""
        # 直接匹配
        if item_path in self.approved_items:
            return True
        
        # 检查父目录是否已确认
        parts = item_path.split('/')
        for i in range(len(parts)):
            parent_path = '/'.join(parts[:i+1])
            if parent_path in self.approved_items:
                return True
        
        return False
    
    def list_approvals(self):
        """列出所有已确认的项目"""
        if not self.approved_items:
            print("[INFO] 没有已确认的项目")
            return
        
        import time
        print("\n=== 已确认的项目 ===")
        for path, info in self.approved_items.items():
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(info['approved_at']))
            print(f"  - {path}")
            print(f"    确认时间: {date}")
            print(f"    原因: {info.get('reason', '无')}")
        print()
    
    def revoke_approval(self, item_path: str):
        """
        撤销确认
        
        Args:
            item_path: 项目路径
        """
        if item_path in self.approved_items:
            del self.approved_items[item_path]
            self._save_approvals()
            print(f"[OK] 已撤销确认: {item_path}")
        else:
            print(f"[警告] 未找到确认记录: {item_path}")
    
    def check_non_skills_content(self, files: List[str]) -> List[ComplianceIssue]:
        """
        检查 skills 目录外的新增内容
        
        Args:
            files: 文件路径列表
            
        Returns:
            合规问题列表
        """
        issues = []
        
        for file_path in files:
            # 跳过空路径
            if not file_path:
                continue
                
            # 检查是否在 skills 目录内
            if file_path.startswith('skills/'):
                continue
            
            # 检查是否已确认
            if self.is_approved(file_path):
                continue
            
            # 获取顶级目录或文件名
            top_level = file_path.split('/')[0]
            
            # 检查是否是允许的顶级目录
            if top_level in self.ALLOWED_TOP_LEVEL_DIRS:
                continue
            
            # 检查是否是允许的顶级文件
            if file_path in self.ALLOWED_TOP_LEVEL_FILES:
                continue
            
            # 检查是否是 .gitignore 中的文件
            if self._is_in_gitignore(file_path):
                continue
            
            # 不在白名单内的内容，发出告警
            if '/' in file_path:
                # 这是一个目录下的文件
                issues.append(ComplianceIssue(
                    file_path=file_path,
                    issue_type="非白名单目录内容",
                    risk_level=RiskLevel.HIGH,
                    description=f"目录 '{top_level}' 不在允许同步的白名单内，请确认是否允许同步",
                    rule="external_content"
                ))
            else:
                # 这是一个顶级文件
                issues.append(ComplianceIssue(
                    file_path=file_path,
                    issue_type="非白名单根目录文件",
                    risk_level=RiskLevel.HIGH,
                    description=f"文件 '{file_path}' 不在允许同步的白名单内，请确认是否允许同步",
                    rule="external_content"
                ))
        
        return issues
    
    def _is_in_gitignore(self, file_path: str) -> bool:
        """检查文件是否在 .gitignore 中"""
        try:
            result = subprocess.run(
                ["git", "check-ignore", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
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
        
        # 首先检查 skills 目录外的新增内容
        external_issues = self.check_non_skills_content(staged_files)
        self.issues.extend(external_issues)
        
        # 然后检查常规规则
        for file_path in staged_files:
            issue = self.check_file(file_path)
            if issue:
                self.issues.append(issue)
        
        return self.issues
    
    def check_committed_files(self) -> List[ComplianceIssue]:
        """
        检查已提交的文件
        
        Returns:
            违规问题列表
        """
        self.issues = []
        committed_files = self.get_committed_files()
        
        # 首先检查 skills 目录外的新增内容
        external_issues = self.check_non_skills_content(committed_files)
        self.issues.extend(external_issues)
        
        # 然后检查常规规则
        for file_path in committed_files:
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
    import sys
    checker = ComplianceChecker()
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        # 允许某个项目同步（兼容旧approve命令）
        if (cmd == 'allow' or cmd == 'approve') and len(sys.argv) > 2:
            path = sys.argv[2]
            reason = sys.argv[3] if len(sys.argv) > 3 else "用户允许同步"
            checker.allow_item(path, reason)
            sys.exit(0)
        
        # 禁止某个项目同步
        if cmd == 'deny' and len(sys.argv) > 2:
            path = sys.argv[2]
            success = checker.deny_item(path)
            sys.exit(0 if success else 1)
        
        # 列出已确认的项目
        if cmd == 'list-approvals':
            checker.list_approvals()
            sys.exit(0)
        
        # 撤销确认
        if cmd == 'revoke' and len(sys.argv) > 2:
            checker.revoke_approval(sys.argv[2])
            sys.exit(0)
    
    # 默认执行检查
    print("=== 检查暂存区文件 ===")
    staged_issues = checker.check_staged_files()
    
    if staged_issues:
        print(f"\n[!] 发现 {len(staged_issues)} 个不合规文件")
        print("\n" + checker.generate_report(staged_issues, check_type="staged"))
    else:
        print("\n[OK] 没有发现不合规文件")
    
    print("\n=== 检查已提交文件 ===")
    committed_issues = checker.check_committed_files()
    
    if committed_issues:
        print(f"\n[!] 发现 {len(committed_issues)} 个不合规文件")
        print("\n" + checker.generate_report(committed_issues, check_type="committed"))
    else:
        print("\n[OK] 没有发现不合规文件")
    
    all_issues = staged_issues + committed_issues
    
    if all_issues:
        print(f"\n发现 {len(all_issues)} 个合规问题:")
        for issue in all_issues:
            risk_icon = "[H]" if issue.risk_level == RiskLevel.HIGH else "[M]" if issue.risk_level == RiskLevel.MEDIUM else "[L]"
            print(f"{risk_icon} {issue.file_path} - {issue.issue_type}")
        print("\n提示: 使用 'python compliance_checker.py approve <path> [reason]' 确认项目")
    else:
        print("\n[OK] 没有发现合规问题")
