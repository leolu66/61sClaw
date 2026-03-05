#!/usr/bin/env python3
"""
GitHub 客户端
用于从 GitHub 仓库获取技能文件

使用方法:
    from github_client import GitHubClient
    
    client = GitHubClient("leolu66/61sClaw")
    skills = client.get_skills_list()
    content = client.get_file_content("skills/todo-manager/SKILL.md")
"""

import os
import json
import base64
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Any
from pathlib import Path


class GitHubClient:
    """GitHub API 客户端"""
    
    def __init__(self, repo: str, branch: str = "main", token: Optional[str] = None):
        """
        初始化 GitHub 客户端
        
        Args:
            repo: 仓库名 (如 "leolu66/61sClaw")
            branch: 分支名
            token: GitHub Token (可选，用于提高 API 限制)
        """
        self.repo = repo
        self.branch = branch
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_api_url = f"https://api.github.com/repos/{repo}"
        self.raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}"
        
    def _make_request(self, url: str, headers: Optional[Dict] = None) -> Any:
        """
        发送 HTTP 请求
        
        优先使用 curl（避免 urllib SSL 握手问题），失败时回退到 urllib
        
        Args:
            url: 请求 URL
            headers: 请求头
        
        Returns:
            响应数据
        """
        if headers is None:
            headers = {}
        
        headers["User-Agent"] = "SkillSyncer/1.0"
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        # 优先使用 curl（避免 Windows 上 urllib 的 SSL 握手超时问题）
        try:
            cmd = ["curl", "-s", "-L", "--max-time", "30", "-A", headers["User-Agent"]]
            
            # 添加自定义 headers
            for key, value in headers.items():
                if key != "User-Agent":  # User-Agent 已通过 -A 设置
                    cmd.extend(["-H", f"{key}: {value}"])
            
            cmd.append(url)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            
            if result.returncode == 0:
                data = result.stdout
                # 尝试解析 JSON
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            else:
                # curl 失败，回退到 urllib
                raise Exception(f"curl failed: {result.stderr}")
                
        except Exception:
            # 回退到 urllib 方式
            request = urllib.request.Request(url, headers=headers)
            
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = response.read().decode("utf-8")
                    
                    # 尝试解析 JSON
                    try:
                        return json.loads(data)
                    except json.JSONDecodeError:
                        return data
                        
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise FileNotFoundError(f"文件不存在: {url}")
                elif e.code == 403:
                    raise PermissionError(f"API 限制或权限不足: {url}")
                else:
                    raise Exception(f"HTTP 错误 {e.code}: {e.reason}")
                    
            except urllib.error.URLError as e:
                raise ConnectionError(f"网络错误: {e.reason}")
    
    def get_repo_tree(self, path: str = "") -> List[Dict]:
        """
        获取仓库文件树
        
        使用 GitHub API 获取目录列表（目录列表没有 raw URL 方式）
        但可以通过访问 skills/ 目录的 README 或特定文件来推断
        
        Args:
            path: 目录路径
        
        Returns:
            文件列表
        """
        # 尝试使用 raw URL 获取目录列表（通过访问一个已知文件来推断）
        if path == "skills" or path.startswith("skills/"):
            # 对于技能目录，尝试直接获取技能列表
            try:
                return self._get_skills_list_via_raw()
            except Exception:
                pass
        
        # 回退到 API 方式
        url = f"{self.base_api_url}/contents/{path}?ref={self.branch}"
        
        try:
            result = self._make_request(url)
            if isinstance(result, list):
                return result
            return []
        except FileNotFoundError:
            return []
    
    def _get_skills_list_via_raw(self) -> List[Dict]:
        """通过 raw URL 获取技能列表（避免 API 限流）"""
        # 尝试获取 skills 目录下的几个已知技能来推断列表
        # 这是一个变通方案，因为 GitHub 没有提供目录列表的 raw 接口
        
        # 常见技能列表（硬编码兜底）
        common_skills = [
            "ai-news-fetcher", "api-balance-checker", "audio-control",
            "billing-analyzer", "brave-search", "claude-code-sender",
            "code-stats", "disk-cleaner", "exchange-email-reader",
            "feishu-notifier", "game-auto-clicker", "github-compliance-checker",
            "gobang-game", "jhwg-auto", "log-migrator", "model-selector",
            "mouseinfo-launcher", "multi-agent-coordinator", "one-click-commit",
            "potplayer-music", "skill-syncer", "solitaire-game",
            "telecom-news-fetcher", "todo-manager", "vpn-controller",
            "weather-skill", "wechat-article-fetcher", "work-session-logger"
        ]
        
        skills = []
        for skill_name in common_skills:
            # 尝试获取 SKILL.md 验证技能存在
            try:
                raw_url = f"{self.raw_url}/skills/{skill_name}/SKILL.md"
                self._make_request(raw_url)
                # 如果成功，说明技能存在
                skills.append({
                    "name": skill_name,
                    "path": f"skills/{skill_name}",
                    "type": "dir"
                })
            except Exception:
                # 技能不存在或网络错误，跳过
                continue
        
        if not skills:
            # 如果 raw 方式失败，回退到 API
            raise Exception("Raw URL 方式获取失败")
        
        return skills
    
    def get_file_content(self, path: str) -> str:
        """
        获取文件内容
        
        Args:
            path: 文件路径
        
        Returns:
            文件内容
        """
        # 优先使用 raw.githubusercontent.com（无 API 限制）
        raw_url = f"{self.raw_url}/{path}"
        
        try:
            content = self._make_request(raw_url)
            if isinstance(content, str):
                return content
            else:
                # 如果返回的不是字符串，使用 API 方式
                raise Exception("Unexpected response type")
        except Exception:
            # 回退到 API 方式
            url = f"{self.base_api_url}/contents/{path}?ref={self.branch}"
            result = self._make_request(url)
            
            if isinstance(result, dict) and "content" in result:
                # Base64 解码
                content = base64.b64decode(result["content"]).decode("utf-8")
                return content
            
            raise FileNotFoundError(f"无法获取文件: {path}")
    
    def get_skills_list(self) -> List[str]:
        """
        获取技能列表
        
        Returns:
            技能名称列表
        """
        skills = []
        items = self.get_repo_tree("skills")
        
        for item in items:
            if item.get("type") == "dir":
                skill_name = item.get("name")
                # 验证是否是有效技能（包含 SKILL.md）
                try:
                    self.get_file_content(f"skills/{skill_name}/SKILL.md")
                    skills.append(skill_name)
                except FileNotFoundError:
                    pass  # 不是有效技能目录
        
        return sorted(skills)
    
    def get_skill_files(self, skill_name: str) -> List[Dict]:
        """
        获取技能的所有文件
        
        Args:
            skill_name: 技能名称
        
        Returns:
            文件列表，每个文件包含 path 和 type
        """
        files = []
        path = f"skills/{skill_name}"
        
        def traverse(current_path: str):
            items = self.get_repo_tree(current_path)
            
            for item in items:
                item_path = item.get("path", "")
                item_type = item.get("type", "")
                
                if item_type == "file":
                    files.append({
                        "path": item_path,
                        "name": item.get("name"),
                        "size": item.get("size", 0),
                        "sha": item.get("sha", "")
                    })
                elif item_type == "dir":
                    traverse(item_path)
        
        traverse(path)
        return files
    
    def get_directory_structure(self, skill_name: str) -> Dict:
        """
        获取技能目录结构
        
        Args:
            skill_name: 技能名称
        
        Returns:
            目录结构字典
        """
        structure = {
            "name": skill_name,
            "files": [],
            "directories": []
        }
        
        path = f"skills/{skill_name}"
        items = self.get_repo_tree(path)
        
        for item in items:
            if item.get("type") == "file":
                structure["files"].append(item.get("name"))
            elif item.get("type") == "dir":
                dir_name = item.get("name")
                sub_files = self.get_skill_files(f"{skill_name}/{dir_name}")
                structure["directories"].append({
                    "name": dir_name,
                    "files": [f["name"] for f in sub_files]
                })
        
        return structure


# 示例用法
if __name__ == "__main__":
    client = GitHubClient("leolu66/61sClaw")
    
    print("=== 获取技能列表 ===")
    skills = client.get_skills_list()
    print(f"找到 {len(skills)} 个技能:")
    for skill in skills[:10]:  # 只显示前10个
        print(f"  - {skill}")
    if len(skills) > 10:
        print(f"  ... 还有 {len(skills) - 10} 个")
    print()
    
    if skills:
        print(f"=== 获取技能 '{skills[0]}' 的文件 ===")
        files = client.get_skill_files(skills[0])
        print(f"文件数量: {len(files)}")
        for f in files[:5]:
            print(f"  - {f['path']} ({f['size']} bytes)")
        print()
        
        print(f"=== 读取 SKILL.md 内容 ===")
        try:
            content = client.get_file_content(f"skills/{skills[0]}/SKILL.md")
            print(f"前 500 字符:\n{content[:500]}...")
        except Exception as e:
            print(f"错误: {e}")
