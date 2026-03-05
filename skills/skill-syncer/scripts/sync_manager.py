#!/usr/bin/env python3
"""
技能同步管理器
管理本地技能与远程技能的同步

使用方法:
    from sync_manager import SkillSyncManager
    
    syncer = SkillSyncManager()
    result = syncer.sync_skill("todo-manager")
    results = syncer.sync_all_skills()
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass, field

# 添加父目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))
from github_client import GitHubClient


@dataclass
class SyncResult:
    """同步结果"""
    skill_name: str
    success: bool
    updated: bool
    files_changed: int = 0
    files_added: int = 0
    files_removed: int = 0
    backup_path: Optional[str] = None
    error: Optional[str] = None
    details: List[str] = field(default_factory=list)


class SkillSyncManager:
    """技能同步管理器"""
    
    def __init__(
        self,
        github_repo: str = "leolu66/61sClaw",
        local_skills_dir: Optional[str] = None,
        backup_dir: Optional[str] = None
    ):
        """
        初始化同步管理器
        
        Args:
            github_repo: GitHub 仓库名
            local_skills_dir: 本地技能目录
            backup_dir: 备份目录
        """
        self.github_repo = github_repo
        self.local_skills_dir = Path(local_skills_dir) if local_skills_dir else Path("skills")
        self.backup_dir = Path(backup_dir) if backup_dir else Path("backups/skills")
        
        # 初始化 GitHub 客户端
        self.github = GitHubClient(github_repo)
        
        # 确保目录存在
        self.local_skills_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_local_skills(self) -> List[str]:
        """
        获取本地技能列表
        
        Returns:
            本地技能名称列表
        """
        skills = []
        
        if not self.local_skills_dir.exists():
            return skills
        
        for item in self.local_skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        
        return sorted(skills)
    
    def get_remote_skills(self) -> List[str]:
        """
        获取远程技能列表
        
        Returns:
            远程技能名称列表
        """
        try:
            return self.github.get_skills_list()
        except Exception as e:
            print(f"[错误] 获取远程技能列表失败: {e}")
            return []
    
    def get_skill_status(self, skill_name: str) -> Dict[str, Any]:
        """
        获取技能同步状态
        
        Args:
            skill_name: 技能名称
        
        Returns:
            状态信息
        """
        local_exists = (self.local_skills_dir / skill_name / "SKILL.md").exists()
        
        try:
            remote_files = self.github.get_skill_files(skill_name)
            remote_exists = len(remote_files) > 0
        except Exception:
            remote_exists = False
            remote_files = []
        
        return {
            "skill_name": skill_name,
            "local_exists": local_exists,
            "remote_exists": remote_exists,
            "can_sync": local_exists and remote_exists,
            "local_only": local_exists and not remote_exists,
            "remote_only": remote_exists and not local_exists,
            "remote_files": remote_files
        }
    
    def backup_skill(self, skill_name: str) -> Optional[str]:
        """
        备份技能
        
        Args:
            skill_name: 技能名称
        
        Returns:
            备份路径，失败返回 None
        """
        skill_path = self.local_skills_dir / skill_name
        
        if not skill_path.exists():
            return None
        
        # 创建带时间戳的备份目录
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / skill_name / timestamp
        
        try:
            shutil.copytree(skill_path, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"[警告] 备份失败: {e}")
            return None
    
    def sync_skill(self, skill_name: str, dry_run: bool = False, force: bool = False) -> SyncResult:
        """
        同步单个技能
        
        Args:
            skill_name: 技能名称
            dry_run: 是否仅预览（不实际执行）
            force: 是否强制更新（覆盖本地特有技能保护）
        
        Returns:
            同步结果
        """
        print(f"[同步] {skill_name}...")
        
        # 检查状态
        status = self.get_skill_status(skill_name)
        
        # 本地特有技能（远程不存在）- 保护（force 可跳过）
        if status["local_only"] and not force:
            return SyncResult(
                skill_name=skill_name,
                success=True,
                updated=False,
                details=["本地特有技能，已保护（使用 --force 强制更新）"]
            )
        
        # 远程有但本地没有 - 安装新技能
        if status["remote_only"]:
            if dry_run:
                return SyncResult(
                    skill_name=skill_name,
                    success=True,
                    updated=True,
                    details=["将安装新技能（预览模式）"]
                )
            return self._install_new_skill(skill_name)
        
        # 都不能同步
        if not status["can_sync"]:
            return SyncResult(
                skill_name=skill_name,
                success=False,
                updated=False,
                error="无法同步（本地或远程不存在）"
            )
        
        # 获取远程文件列表
        remote_files = status["remote_files"]
        
        if dry_run:
            # 仅预览模式
            return SyncResult(
                skill_name=skill_name,
                success=True,
                updated=True,
                files_changed=len(remote_files),
                details=[f"将更新 {len(remote_files)} 个文件（预览模式）"]
            )
        
        # 备份
        backup_path = self.backup_skill(skill_name)
        
        try:
            # 同步文件
            skill_path = self.local_skills_dir / skill_name
            skill_path.mkdir(parents=True, exist_ok=True)
            
            files_changed = 0
            files_added = 0
            details = []
            
            for file_info in remote_files:
                remote_path = file_info["path"]
                relative_path = remote_path.replace(f"skills/{skill_name}/", "")
                local_file_path = skill_path / relative_path
                
                # 确保目录存在
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 检查文件是否存在且不同
                need_update = True
                if local_file_path.exists():
                    try:
                        local_content = local_file_path.read_text(encoding="utf-8")
                        remote_content = self.github.get_file_content(remote_path)
                        
                        if local_content == remote_content:
                            need_update = False
                        else:
                            files_changed += 1
                            details.append(f"更新: {relative_path}")
                    except Exception:
                        files_changed += 1
                        details.append(f"更新: {relative_path}")
                else:
                    files_added += 1
                    details.append(f"新增: {relative_path}")
                
                if need_update:
                    # 下载文件
                    content = self.github.get_file_content(remote_path)
                    local_file_path.write_text(content, encoding="utf-8")
            
            return SyncResult(
                skill_name=skill_name,
                success=True,
                updated=True,
                files_changed=files_changed,
                files_added=files_added,
                backup_path=backup_path,
                details=details
            )
            
        except Exception as e:
            return SyncResult(
                skill_name=skill_name,
                success=False,
                updated=False,
                error=str(e),
                backup_path=backup_path
            )
    
    def sync_all_skills(self, dry_run: bool = False, install_new: bool = True, force: bool = False) -> Dict[str, Any]:
        """
        同步所有技能
        
        Args:
            dry_run: 是否仅预览
            install_new: 是否安装远程新技能（获取全部技能时为 True）
            force: 是否强制更新（覆盖本地特有技能保护）
        
        Returns:
            批量同步结果
        """
        local_skills = self.get_local_skills()
        remote_skills = self.get_remote_skills()
        
        print(f"[信息] 本地技能: {len(local_skills)} 个")
        print(f"[信息] 远程技能: {len(remote_skills)} 个")
        print()
        
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0
        installed_count = 0
        
        # 先同步本地已存在的技能
        for skill_name in local_skills:
            result = self.sync_skill(skill_name, dry_run, force)
            results.append(result)
            
            if result.success:
                if result.updated:
                    success_count += 1
                else:
                    skipped_count += 1
            else:
                failed_count += 1
        
        # 安装远程新技能（如果启用）
        if install_new and not dry_run:
            new_skills = [s for s in remote_skills if s not in local_skills]
            
            if new_skills:
                print(f"\n[信息] 发现 {len(new_skills)} 个新技能，开始安装...")
                
                for skill_name in new_skills:
                    print(f"[安装] {skill_name}...")
                    result = self._install_new_skill(skill_name)
                    results.append(result)
                    
                    if result.success:
                        installed_count += 1
                    else:
                        failed_count += 1
        
        return {
            "success": failed_count == 0,
            "total": len(local_skills) + (len(remote_skills) - len(local_skills) if install_new else 0),
            "updated_count": success_count,
            "installed_count": installed_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "results": results
        }
    
    def compare_skill(self, skill_name: str) -> Dict[str, Any]:
        """
        比较本地和远程技能差异
        
        Args:
            skill_name: 技能名称
        
        Returns:
            差异信息
        """
        status = self.get_skill_status(skill_name)
        
        if not status["can_sync"]:
            return {
                "skill_name": skill_name,
                "can_compare": False,
                "reason": "本地或远程不存在"
            }
        
        skill_path = self.local_skills_dir / skill_name
        remote_files = status["remote_files"]
        
        differences = []
        
        for file_info in remote_files:
            remote_path = file_info["path"]
            relative_path = remote_path.replace(f"skills/{skill_name}/", "")
            local_file_path = skill_path / relative_path
            
            if not local_file_path.exists():
                differences.append({
                    "file": relative_path,
                    "status": "missing_local"
                })
            else:
                try:
                    local_content = local_file_path.read_text(encoding="utf-8")
                    remote_content = self.github.get_file_content(remote_path)
                    
                    if local_content != remote_content:
                        differences.append({
                            "file": relative_path,
                            "status": "different"
                        })
                except Exception as e:
                    differences.append({
                        "file": relative_path,
                        "status": "error",
                        "error": str(e)
                    })
        
        return {
            "skill_name": skill_name,
            "can_compare": True,
            "differences": differences,
            "has_differences": len(differences) > 0
        }
    
    def _install_new_skill(self, skill_name: str) -> SyncResult:
        """
        安装新技能（远程有，本地没有）
        
        Args:
            skill_name: 技能名称
        
        Returns:
            安装结果
        """
        print(f"[安装新技能] {skill_name}...")
        
        try:
            # 获取远程文件列表
            remote_files = self.github.get_skill_files(skill_name)
            
            if not remote_files:
                return SyncResult(
                    skill_name=skill_name,
                    success=False,
                    updated=False,
                    error="远程技能没有文件"
                )
            
            # 创建本地目录
            skill_path = self.local_skills_dir / skill_name
            skill_path.mkdir(parents=True, exist_ok=True)
            
            files_installed = 0
            details = []
            
            for file_info in remote_files:
                remote_path = file_info["path"]
                relative_path = remote_path.replace(f"skills/{skill_name}/", "")
                local_file_path = skill_path / relative_path
                
                # 确保目录存在
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 下载文件
                content = self.github.get_file_content(remote_path)
                local_file_path.write_text(content, encoding="utf-8")
                
                files_installed += 1
                details.append(f"安装: {relative_path}")
            
            return SyncResult(
                skill_name=skill_name,
                success=True,
                updated=True,  # 标记为已更新（新安装）
                files_added=files_installed,
                details=details
            )
            
        except Exception as e:
            return SyncResult(
                skill_name=skill_name,
                success=False,
                updated=False,
                error=f"安装失败: {str(e)}"
            )


# 示例用法
if __name__ == "__main__":
    syncer = SkillSyncManager()
    
    print("=== 本地技能列表 ===")
    local_skills = syncer.get_local_skills()
    print(f"共 {len(local_skills)} 个: {', '.join(local_skills[:5])}...")
    print()
    
    print("=== 远程技能列表 ===")
    remote_skills = syncer.get_remote_skills()
    print(f"共 {len(remote_skills)} 个: {', '.join(remote_skills[:5])}...")
    print()
    
    if local_skills:
        skill_name = local_skills[0]
        print(f"=== 同步技能 '{skill_name}'（预览模式）===")
        result = syncer.sync_skill(skill_name, dry_run=True)
        print(f"成功: {result.success}")
        print(f"将更新: {result.files_changed} 个文件")
        for detail in result.details[:5]:
            print(f"  - {detail}")
