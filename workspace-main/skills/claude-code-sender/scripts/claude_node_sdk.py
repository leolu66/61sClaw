#!/usr/bin/env python3
"""
Claude Code 节点 SDK 调用器
通过 claude -p 命令向 Claude Code 进程发送任务并获取结果

使用方法:
    from claude_node_sdk import ClaudeNodeSDK
    
    sdk = ClaudeNodeSDK("claude")
    result = sdk.send_task("请分析这个文件", file_path="data.txt")
    print(result["output"])
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

# 添加父目录到路径以导入 claude_sender
sys.path.insert(0, str(Path(__file__).parent))
from claude_sender import send_to_claude, send_to_claude_with_file, ClaudeCodeOptions


class ClaudeNodeSDK:
    """
    Claude Code 节点 SDK 封装
    用于向指定 Claude Code 节点发送任务
    """
    
    def __init__(self, node_id: str = "claude", workspace: Optional[str] = None):
        """
        初始化 SDK
        
        Args:
            node_id: 节点 ID (如 "claude", "kimi")
            workspace: 工作区路径
        """
        self.node_id = node_id
        self.workspace = workspace or f"D:\\projects\\workspace\\node-{node_id}"
        self.session_id = None
        
    def send_task(
        self,
        instruction: str,
        file_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        max_turns: int = 10,
        system_prompt: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        发送任务到 Claude Code 节点
        
        Args:
            instruction: 任务指令
            file_path: 可选的文件路径
            output_dir: 输出目录
            max_turns: 最大对话轮数
            system_prompt: 系统提示
            timeout: 超时时间（秒）
        
        Returns:
            执行结果字典
        """
        # 构建提示词
        prompt = self._build_prompt(instruction, output_dir)
        
        # 配置选项
        options = ClaudeCodeOptions(
            output_format="json",
            max_turns=max_turns,
            system_prompt=system_prompt,
            cwd=self.workspace,
            timeout=timeout
        )
        
        # 如果有文件，使用带文件的调用
        if file_path and Path(file_path).exists():
            result = send_to_claude_with_file(prompt, file_path, options)
        else:
            result = send_to_claude(prompt, options)
        
        # 保存会话 ID 以便继续对话
        if result.get("session_id"):
            self.session_id = result["session_id"]
        
        return result
    
    def send_task_with_continue(
        self,
        instruction: str,
        max_turns: int = 10,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        继续之前的对话发送任务
        
        Args:
            instruction: 任务指令
            max_turns: 最大对话轮数
            timeout: 超时时间
        
        Returns:
            执行结果字典
        """
        from claude_sender import continue_conversation
        
        options = ClaudeCodeOptions(
            output_format="json",
            max_turns=max_turns,
            cwd=self.workspace,
            timeout=timeout
        )
        
        result = continue_conversation(instruction, self.session_id, options)
        
        if result.get("session_id"):
            self.session_id = result["session_id"]
        
        return result
    
    def _build_prompt(self, instruction: str, output_dir: Optional[str]) -> str:
        """构建提示词"""
        prompt_parts = ["# 任务指令", "", instruction]
        
        if output_dir:
            prompt_parts.extend([
                "",
                "# 输出要求",
                f"请将结果输出到: {output_dir}",
                "如果生成文件，请确保文件保存到上述目录。"
            ])
        
        prompt_parts.extend([
            "",
            "# 执行完成后",
            "请简要总结执行结果，包括：",
            "1. 完成了什么",
            "2. 生成了哪些文件（如果有）",
            "3. 是否成功"
        ])
        
        return "\n".join(prompt_parts)
    
    def batch_tasks(
        self,
        tasks: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量发送任务
        
        Args:
            tasks: 任务列表，每个任务是字典包含 instruction, file_path 等
            continue_on_error: 出错时是否继续
        
        Returns:
            结果列表
        """
        results = []
        
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] 执行任务: {task.get('instruction', '')[:50]}...")
            
            try:
                result = self.send_task(**task)
                results.append(result)
                
                if not result.get("success") and not continue_on_error:
                    print(f"任务失败，停止批量执行")
                    break
                    
            except Exception as e:
                print(f"任务异常: {e}")
                results.append({"success": False, "error": str(e)})
                
                if not continue_on_error:
                    break
        
        return results


class MultiNodeCoordinator:
    """
    多节点协调器
    管理多个 Claude Code 节点，实现任务分发
    """
    
    def __init__(self):
        self.nodes: Dict[str, ClaudeNodeSDK] = {}
        self.node_status: Dict[str, Dict] = {}
    
    def register_node(self, node_id: str, workspace: Optional[str] = None):
        """注册节点"""
        self.nodes[node_id] = ClaudeNodeSDK(node_id, workspace)
        self.node_status[node_id] = {
            "status": "online",
            "current_task": None,
            "last_heartbeat": time.time()
        }
        print(f"[注册] 节点 {node_id} 已注册")
    
    def get_available_node(self) -> Optional[str]:
        """获取可用节点"""
        for node_id, status in self.node_status.items():
            if status["status"] == "online" and status["current_task"] is None:
                return node_id
        return None
    
    def send_task_to_node(
        self,
        node_id: str,
        instruction: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送任务到指定节点"""
        if node_id not in self.nodes:
            return {"success": False, "error": f"节点 {node_id} 未注册"}
        
        # 标记节点为忙碌
        self.node_status[node_id]["status"] = "busy"
        self.node_status[node_id]["current_task"] = instruction[:50]
        
        try:
            sdk = self.nodes[node_id]
            result = sdk.send_task(instruction, **kwargs)
            
            # 更新节点状态
            self.node_status[node_id]["status"] = "online"
            self.node_status[node_id]["current_task"] = None
            self.node_status[node_id]["last_heartbeat"] = time.time()
            
            return result
            
        except Exception as e:
            self.node_status[node_id]["status"] = "error"
            self.node_status[node_id]["current_task"] = None
            return {"success": False, "error": str(e)}
    
    def broadcast_task(
        self,
        instruction: str,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """广播任务到所有节点"""
        results = {}
        
        for node_id in self.nodes:
            print(f"[广播] 发送到节点 {node_id}...")
            results[node_id] = self.send_task_to_node(node_id, instruction, **kwargs)
        
        return results
    
    def get_node_status(self) -> Dict:
        """获取所有节点状态"""
        return {
            "nodes": self.node_status,
            "total": len(self.nodes),
            "online": sum(1 for s in self.node_status.values() if s["status"] == "online"),
            "busy": sum(1 for s in self.node_status.values() if s["status"] == "busy")
        }


# 示例用法
if __name__ == "__main__":
    # 示例 1: 单节点调用
    print("=== 示例 1: 单节点调用 ===")
    sdk = ClaudeNodeSDK("claude")
    result = sdk.send_task(
        instruction="创建一个简单的 Python 计算器类",
        max_turns=5
    )
    print(f"成功: {result.get('success')}")
    print(f"输出: {result.get('text', '')[:500]}...")
    if result.get('json'):
        print(f"成本: ${result['json'].get('total_cost_usd')}")
    print()
    
    # 示例 2: 多节点协调
    print("=== 示例 2: 多节点协调 ===")
    coordinator = MultiNodeCoordinator()
    coordinator.register_node("claude", "D:\\projects\\workspace\\node-claude")
    coordinator.register_node("kimi", "D:\\projects\\workspace\\node-kimi")
    
    # 获取可用节点
    node = coordinator.get_available_node()
    if node:
        result = coordinator.send_task_to_node(
            node,
            "分析当前目录下的文件结构"
        )
        print(f"发送到节点 {node}: {result.get('success')}")
    
    print(f"\n节点状态: {coordinator.get_node_status()}")
