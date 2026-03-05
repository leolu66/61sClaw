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


# 技能别名映射表（基础别名，会被 SKILL.md 中的配置扩展）
SKILL_ALIASES = {}


def load_skill_metadata():
    """
    从所有 SKILL.md 加载技能元数据（aliases 和 triggers）
    
    Returns:
        dict: {skill_name: [aliases]}
    """
    aliases = {}
    skills_dir = Path(__file__).parent.parent.parent.parent / "skills"
    
    if not skills_dir.exists():
        return aliases
    
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
            
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        
        skill_name = skill_dir.name
        skill_aliases = []
        
        try:
            content = skill_md.read_text(encoding='utf-8')
            
            # 解析 YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    yaml_content = parts[1]
                    
                    # 提取 aliases
                    if 'aliases:' in yaml_content:
                        for line in yaml_content.split('\n'):
                            if 'aliases:' in line:
                                # 解析内联数组格式：aliases: ["a", "b"]
                                import re
                                match = re.search(r'aliases:\s*\[(.*?)\]', line)
                                if match:
                                    items = match.group(1).split(',')
                                    skill_aliases.extend([item.strip().strip('"\'') for item in items])
                                break
                    
                    # 提取 triggers 作为备选别名
                    if 'triggers:' in yaml_content:
                        in_triggers = False
                        for line in yaml_content.split('\n'):
                            if 'triggers:' in line:
                                in_triggers = True
                                # 解析内联数组格式
                                import re
                                match = re.search(r'triggers:\s*\[(.*?)\]', line)
                                if match:
                                    items = match.group(1).split(',')
                                    skill_aliases.extend([item.strip().strip('"\'') for item in items])
                                continue
                            
                            if in_triggers and line.strip().startswith('-'):
                                trigger = line.strip()[1:].strip().strip('"\'')
                                if trigger:
                                    skill_aliases.append(trigger)
                            elif in_triggers and line.strip() and not line.strip().startswith('#'):
                                break
            
            if skill_aliases:
                aliases[skill_name] = list(set(skill_aliases))  # 去重
                
        except Exception as e:
            print(f"[警告] 读取 {skill_name}/SKILL.md 失败: {e}")
            continue
    
    return aliases


def get_all_aliases():
    """获取所有别名（基础别名 + SKILL.md 中的配置）"""
    # 基础别名（硬编码的兜底）
    base_aliases = {
        "billing-analyzer": ["账单分析", "账单", "billing", "消费分析", "成本分析"],
        "multi-agent-coordinator": ["多智能体", "协调器", "coordinator", "multi-agent", "任务协调"],
        "claude-code-sender": ["claude发送", "claude-code", "code-sender", "SDK发送"],
        "skill-syncer": ["技能同步", "同步技能", "skill-sync", "syncer", "获取技能"],
        "todo-manager": ["待办", "todo", "任务管理", "待办事项"],
        "weather-skill": ["天气", "weather", "天气预报"],
        "gobang-game": ["五子棋", "gobang", "游戏", "下棋"],
        "solitaire-game": ["纸牌", "solitaire", "接龙", "纸牌接龙"],
        "code-stats": ["代码统计", "统计", "工作量统计", "技能统计"],
        "log-migrator": ["日志归档", "日志迁移", "备份", "归档"],
        "work-session-logger": ["工作日志", "会话记录", "logger", "记录日志"],
        "github-compliance-checker": ["合规检查", "github检查", "合规", "检查github"],
        "model-selector": ["模型选择", "切换模型", "selector", "换模型"],
        "api-balance-checker": ["查余额", "余额检查", "api余额", "检查余额"],
        "disk-cleaner": ["磁盘清理", "清理磁盘", "C盘清理", "释放空间"],
        "vpn-controller": ["VPN", "vpn", "翻墙", "代理"],
        "audio-control": ["音频", "声音", "静音", "音量"],
        "wechat-article-fetcher": ["微信文章", "公众号", "wechat", "文章获取"],
        "telecom-news-fetcher": ["电信新闻", "运营商", "通信新闻", "telecom"],
        "ai-news-fetcher": ["AI新闻", "人工智能", "科技新闻", "ai-news"],
        "jhwg-auto": ["几何王国", "jhwg", "游戏自动", "代玩"],
        "game-auto-clicker": ["游戏点击", "自动点击", "clicker", "游戏辅助"],
        "potplayer-music": ["音乐", "播放音乐", "potplayer", "听歌"],
        "mouseinfo-launcher": ["鼠标坐标", "mouseinfo", "取色", "坐标"],
        "exchange-email-reader": ["邮件", "邮箱", "exchange", "读邮件"],
        "feishu-notifier": ["飞书通知", "通知", "feishu", "推送"],
        "one-click-commit": ["提交", "一键提交", "commit", "保存"],
        "brave-search": ["搜索", "brave", "网页搜索", "查资料"],
    }
    
    # 加载 SKILL.md 中的配置
    skill_md_aliases = load_skill_metadata()
    
    # 合并（SKILL.md 配置覆盖基础别名）
    merged = base_aliases.copy()
    for skill_name, aliases in skill_md_aliases.items():
        if skill_name in merged:
            # 合并并去重
            merged[skill_name] = list(set(merged[skill_name] + aliases))
        else:
            merged[skill_name] = aliases
    
    return merged


def resolve_skill_name(name: str) -> str:
    """
    解析技能名称，支持别名匹配
    
    Args:
        name: 用户输入的技能名称或别名
        
    Returns:
        标准技能名称，如果无法解析则返回原名称
    """
    name_lower = name.lower().strip()
    
    # 加载所有别名（基础 + SKILL.md）
    all_aliases = get_all_aliases()
    
    # 1. 直接匹配标准名称
    if name_lower in all_aliases:
        return name_lower
    
    # 2. 遍历别名映射表
    for standard_name, aliases in all_aliases.items():
        # 检查是否匹配别名
        if name_lower in [a.lower() for a in aliases]:
            return standard_name
        # 检查是否包含别名关键词
        for alias in aliases:
            if alias.lower() in name_lower or name_lower in alias.lower():
                return standard_name
    
    # 3. 模糊匹配（处理空格、连字符等）
    name_normalized = name_lower.replace(" ", "-").replace("_", "-")
    for standard_name in all_aliases.keys():
        if name_normalized == standard_name.lower():
            return standard_name
        if name_normalized in standard_name.lower():
            return standard_name
        if standard_name.lower() in name_normalized:
            return standard_name
    
    # 无法解析，返回原名称
    return name


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
            skill_name: 技能名称（支持标准名称或别名）
            dry_run: 是否仅预览（不实际执行）
            force: 是否强制更新（覆盖本地特有技能保护）
        
        Returns:
            同步结果
        """
        # 解析技能名称（支持别名）
        resolved_name = resolve_skill_name(skill_name)
        if resolved_name != skill_name:
            print(f"[信息] 技能名称 '{skill_name}' 解析为 '{resolved_name}'")
        
        print(f"[同步] {resolved_name}...")
        
        # 检查状态
        status = self.get_skill_status(resolved_name)
        
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
        backup_path = self.backup_skill(resolved_name)
        
        try:
            # 同步文件
            skill_path = self.local_skills_dir / resolved_name
            skill_path.mkdir(parents=True, exist_ok=True)
            
            files_changed = 0
            files_added = 0
            details = []
            
            for file_info in remote_files:
                remote_path = file_info["path"]
                relative_path = remote_path.replace(f"skills/{resolved_name}/", "")
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
    
    def get_latest_skills(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        获取最新技能（本地没有的新技能 + 有更新的技能）
        
        Args:
            dry_run: 是否仅预览
            
        Returns:
            批量同步结果
        """
        local_skills = self.get_local_skills()
        remote_skills = self.get_remote_skills()
        
        print(f"[信息] 本地技能: {len(local_skills)} 个")
        print(f"[信息] 远程技能: {len(remote_skills)} 个")
        print()
        
        # 找出需要处理的技能
        new_skills = []  # 本地没有的新技能
        update_skills = []  # 有更新的技能
        
        for skill_name in remote_skills:
            if skill_name not in local_skills:
                new_skills.append(skill_name)
            else:
                # 检查是否有更新
                status = self.get_skill_status(skill_name)
                if status["can_sync"]:
                    # 比较本地和远程文件
                    has_update = self._check_skill_update(skill_name)
                    if has_update:
                        update_skills.append(skill_name)
        
        print(f"[信息] 新技能: {len(new_skills)} 个")
        print(f"[信息] 有更新的技能: {len(update_skills)} 个")
        print()
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "new_skills": new_skills,
                "update_skills": update_skills,
                "message": f"预览模式：发现 {len(new_skills)} 个新技能，{len(update_skills)} 个有更新"
            }
        
        results = []
        success_count = 0
        failed_count = 0
        
        # 安装新技能
        if new_skills:
            print(f"[信息] 开始安装 {len(new_skills)} 个新技能...")
            for skill_name in new_skills:
                result = self._install_new_skill(skill_name)
                results.append(result)
                if result.success:
                    success_count += 1
                else:
                    failed_count += 1
        
        # 更新有变动的技能
        if update_skills:
            print(f"[信息] 开始更新 {len(update_skills)} 个技能...")
            for skill_name in update_skills:
                result = self.sync_skill(skill_name, dry_run=False, force=False)
                results.append(result)
                if result.success and result.updated:
                    success_count += 1
                elif not result.success:
                    failed_count += 1
        
        return {
            "success": failed_count == 0,
            "total": len(new_skills) + len(update_skills),
            "new_count": len(new_skills),
            "update_count": len(update_skills),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "message": f"完成！安装 {len(new_skills)} 个新技能，更新 {len(update_skills)} 个技能"
        }
    
    def _check_skill_update(self, skill_name: str) -> bool:
        """检查技能是否有更新（比较文件内容）"""
        try:
            remote_files = self.github.get_skill_files(skill_name)
            skill_path = self.local_skills_dir / skill_name
            
            for file_info in remote_files:
                remote_path = file_info["path"]
                relative_path = remote_path.replace(f"skills/{skill_name}/", "")
                local_file_path = skill_path / relative_path
                
                if not local_file_path.exists():
                    return True  # 本地缺少文件，需要更新
                
                try:
                    local_content = local_file_path.read_text(encoding="utf-8")
                    remote_content = self.github.get_file_content(remote_path)
                    
                    if local_content != remote_content:
                        return True  # 文件内容不同，需要更新
                except Exception:
                    return True  # 读取失败，假设需要更新
            
            return False  # 所有文件相同，无需更新
        except Exception:
            return False  # 检查失败，假设无需更新
    
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
