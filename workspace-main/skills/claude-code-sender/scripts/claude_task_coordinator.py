#!/usr/bin/env python3
"""
Claude Code 任务协调器
实现完整的任务生命周期管理：
发送任务 -> 监控执行 -> 检查结果 -> [OK]关闭会话 / [有问题]要求改进

使用方法:
    from claude_task_coordinator import TaskCoordinator
    
    coordinator = TaskCoordinator()
    result = coordinator.send_task_and_wait(
        node_id="claude",
        instruction="创建一个 Python 计算器类",
        output_dir="D:\\projects\\workspace\\shared\\output\\task-001",
        check_callback=my_check_function
    )
"""

import json
import time
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from claude_sender import send_to_claude, ClaudeCodeOptions, continue_conversation


@dataclass
class TaskResult:
    """任务结果"""
    success: bool
    task_id: str
    output_dir: str
    output_files: List[str]
    output: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    retry_count: int = 0


class TaskCoordinator:
    """
    Claude Code 任务协调器
    管理任务的完整生命周期
    """
    
    def __init__(self, base_output_dir: str = "D:\\projects\\workspace\\shared\\output"):
        """
        初始化协调器
        
        Args:
            base_output_dir: 任务输出基础目录
        """
        self.base_output_dir = Path(base_output_dir)
        self.sessions: Dict[str, str] = {}  # node_id -> session_id
        
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        return f"task-{timestamp}"
    
    def _build_task_prompt(
        self,
        task_id: str,
        instruction: str,
        output_dir: str,
        sender_id: str = "coordinator"
    ) -> str:
        """
        构建任务单格式提示词
        
        Args:
            task_id: 任务ID
            instruction: 任务指令
            output_dir: 输出目录
            sender_id: 发送者ID
        
        Returns:
            格式化的任务单
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""# [TASK] 协同工作任务单

## 任务信息
- 任务ID: {task_id}
- 发送者: {sender_id}
- 发送时间: {timestamp}
- 优先级: medium

## 任务指令
{instruction}

## 输出要求
- 输出目录: {output_dir}
- 结果文件: result.json（必须包含以下字段）
  {{
    "taskId": "{task_id}",
    "status": "success/failed",
    "output": "执行结果摘要",
    "outputFiles": ["file1.txt", "file2.py"],
    "executedAt": "ISO格式时间"
  }}
- 日志文件: execution.log（可选，记录执行过程）

## 执行完成后
1. 创建 result.json 文件，严格按照上述格式
2. 将所有生成的文件放入输出目录
3. 在回复中简要说明：
   - 完成了什么
   - 生成了哪些文件（完整路径）
   - 是否成功

## 注意事项
- 这是协同工作任务，请严格按照输出要求执行
- result.json 文件必须创建，否则主节点无法确认完成
- 如有问题请在 result.json 中 status 设为 "failed" 并说明原因
- 输出目录如果不存在请自动创建
"""
        return prompt
    
    def _check_result_file(self, output_dir: str, task_id: str) -> Dict[str, Any]:
        """
        检查结果文件
        
        Args:
            output_dir: 输出目录
            task_id: 任务ID
        
        Returns:
            检查结果 {"ok": bool, "result": dict, "error": str}
        """
        output_path = Path(output_dir)
        result_file = output_path / "result.json"
        
        # 检查目录是否存在
        if not output_path.exists():
            return {
                "ok": False,
                "error": f"输出目录不存在: {output_dir}",
                "result": None
            }
        
        # 检查结果文件
        if not result_file.exists():
            return {
                "ok": False,
                "error": "result.json 文件不存在",
                "result": None
            }
        
        try:
            result_data = json.loads(result_file.read_text(encoding="utf-8"))
            
            # 验证必要字段
            if "status" not in result_data:
                return {
                    "ok": False,
                    "error": "result.json 缺少 status 字段",
                    "result": result_data
                }
            
            if result_data["status"] != "success":
                return {
                    "ok": False,
                    "error": result_data.get("output", "任务执行失败"),
                    "result": result_data
                }
            
            # 检查输出文件
            output_files = result_data.get("outputFiles", [])
            missing_files = []
            for f in output_files:
                if not (output_path / f).exists():
                    missing_files.append(f)
            
            if missing_files:
                return {
                    "ok": False,
                    "error": f"输出文件不存在: {', '.join(missing_files)}",
                    "result": result_data
                }
            
            return {
                "ok": True,
                "error": None,
                "result": result_data
            }
            
        except json.JSONDecodeError as e:
            return {
                "ok": False,
                "error": f"result.json 解析失败: {e}",
                "result": None
            }
        except Exception as e:
            return {
                "ok": False,
                "error": f"检查结果时出错: {e}",
                "result": None
            }
    
    def send_task(
        self,
        node_id: str,
        instruction: str,
        output_dir: Optional[str] = None,
        task_id: Optional[str] = None,
        file_path: Optional[str] = None,
        sender_id: str = "coordinator",
        max_turns: int = 10,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        发送任务到 Claude Code 节点
        
        Args:
            node_id: 节点ID
            instruction: 任务指令
            output_dir: 输出目录（可选，默认自动生成）
            task_id: 任务ID（可选，默认自动生成）
            file_path: 附件文件路径（可选）
            sender_id: 发送者ID
            max_turns: 最大对话轮数
            timeout: 超时时间（秒）
        
        Returns:
            发送结果
        """
        # 生成任务ID和输出目录
        if task_id is None:
            task_id = self._generate_task_id()
        
        if output_dir is None:
            output_dir = str(self.base_output_dir / task_id)
        
        # 构建任务单提示词
        prompt = self._build_task_prompt(task_id, instruction, output_dir, sender_id)
        
        # 配置选项
        options = ClaudeCodeOptions(
            output_format="json",
            max_turns=max_turns,
            timeout=timeout
        )
        
        print(f"[发送任务] {task_id} -> {node_id}")
        print(f"[输出目录] {output_dir}")
        
        # 发送任务
        if file_path and Path(file_path).exists():
            from claude_sender import send_to_claude_with_file
            result = send_to_claude_with_file(prompt, file_path, options)
        else:
            result = send_to_claude(prompt, options)
        
        # 保存会话ID
        if result.get("session_id"):
            self.sessions[node_id] = result["session_id"]
        
        return {
            "task_id": task_id,
            "output_dir": output_dir,
            "send_result": result
        }
    
    def check_task_result(
        self,
        output_dir: str,
        task_id: str,
        check_callback: Optional[Callable[[str], Dict]] = None
    ) -> Dict[str, Any]:
        """
        检查任务结果
        
        Args:
            output_dir: 输出目录
            task_id: 任务ID
            check_callback: 自定义检查函数（接收 output_dir，返回 {"ok": bool, "error": str}）
        
        Returns:
            检查结果
        """
        print(f"[检查结果] {task_id}")
        
        # 基本检查
        basic_check = self._check_result_file(output_dir, task_id)
        
        if not basic_check["ok"]:
            print(f"[检查失败] {basic_check['error']}")
            return basic_check
        
        # 自定义检查
        if check_callback:
            try:
                custom_check = check_callback(output_dir)
                if not custom_check.get("ok", True):
                    print(f"[自定义检查失败] {custom_check.get('error')}")
                    return {
                        "ok": False,
                        "error": custom_check.get("error", "自定义检查失败"),
                        "result": basic_check["result"]
                    }
            except Exception as e:
                print(f"[自定义检查异常] {e}")
                return {
                    "ok": False,
                    "error": f"自定义检查异常: {e}",
                    "result": basic_check["result"]
                }
        
        print(f"[检查通过] 任务完成")
        return basic_check
    
    def request_improvement(
        self,
        node_id: str,
        error_message: str,
        max_turns: int = 5,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        在同一会话中要求改进
        
        Args:
            node_id: 节点ID
            error_message: 错误信息/改进要求
            max_turns: 最大对话轮数
            timeout: 超时时间
        
        Returns:
            改进请求结果
        """
        session_id = self.sessions.get(node_id)
        
        if not session_id:
            return {
                "success": False,
                "error": "没有可用的会话"
            }
        
        prompt = f"""# [TASK] 任务改进要求

之前提交的结果检查未通过，请根据以下反馈进行改进：

## 问题反馈
{error_message}

## 改进要求
1. 修复上述问题
2. 更新 result.json 文件
3. 如有需要，更新其他输出文件
4. 完成后简要说明修改内容

请重新执行任务并输出正确结果。"""
        
        options = ClaudeCodeOptions(
            output_format="json",
            max_turns=max_turns,
            timeout=timeout
        )
        
        print(f"[要求改进] {node_id}")
        print(f"[反馈] {error_message[:100]}...")
        
        result = continue_conversation(prompt, session_id, options)
        
        return result
    
    def send_task_and_wait(
        self,
        node_id: str,
        instruction: str,
        output_dir: Optional[str] = None,
        task_id: Optional[str] = None,
        file_path: Optional[str] = None,
        sender_id: str = "coordinator",
        check_callback: Optional[Callable[[str], Dict]] = None,
        max_retries: int = 2,
        max_turns: int = 10,
        timeout: int = 300,
        check_interval: int = 5
    ) -> TaskResult:
        """
        发送任务并等待完成（完整流程）
        
        Args:
            node_id: 节点ID
            instruction: 任务指令
            output_dir: 输出目录
            task_id: 任务ID
            file_path: 附件文件
            sender_id: 发送者ID
            check_callback: 自定义检查函数
            max_retries: 最大重试次数
            max_turns: 最大对话轮数
            timeout: 超时时间
            check_interval: 检查间隔（秒）
        
        Returns:
            TaskResult 对象
        """
        # 发送任务
        send_result = self.send_task(
            node_id=node_id,
            instruction=instruction,
            output_dir=output_dir,
            task_id=task_id,
            file_path=file_path,
            sender_id=sender_id,
            max_turns=max_turns,
            timeout=timeout
        )
        
        task_id = send_result["task_id"]
        output_dir = send_result["output_dir"]
        session_result = send_result["send_result"]
        
        if not session_result.get("success"):
            return TaskResult(
                success=False,
                task_id=task_id,
                output_dir=output_dir,
                output_files=[],
                output="",
                error=f"发送任务失败: {session_result.get('error')}",
                session_id=session_result.get("session_id")
            )
        
        session_id = session_result.get("session_id")
        cost_usd = session_result.get("json", {}).get("total_cost_usd", 0)
        duration_ms = session_result.get("json", {}).get("duration_ms", 0)
        
        # 等待执行完成并检查
        retry_count = 0
        while retry_count <= max_retries:
            # 等待一段时间让任务执行
            print(f"[等待执行] {check_interval}秒后检查...")
            time.sleep(check_interval)
            
            # 检查结果
            check_result = self.check_task_result(
                output_dir, task_id, check_callback
            )
            
            if check_result["ok"]:
                # 任务完成且检查通过
                result_data = check_result["result"]
                return TaskResult(
                    success=True,
                    task_id=task_id,
                    output_dir=output_dir,
                    output_files=result_data.get("outputFiles", []),
                    output=result_data.get("output", ""),
                    error=None,
                    session_id=session_id,
                    cost_usd=cost_usd,
                    duration_ms=duration_ms,
                    retry_count=retry_count
                )
            
            # 检查未通过，需要改进
            if retry_count < max_retries:
                error_msg = check_result.get("error", "未知错误")
                print(f"[第{retry_count + 1}次重试] 原因: {error_msg}")
                
                improvement_result = self.request_improvement(
                    node_id, error_msg, max_turns, timeout
                )
                
                if not improvement_result.get("success"):
                    return TaskResult(
                        success=False,
                        task_id=task_id,
                        output_dir=output_dir,
                        output_files=[],
                        output="",
                        error=f"改进请求失败: {improvement_result.get('error')}",
                        session_id=session_id,
                        cost_usd=cost_usd,
                        duration_ms=duration_ms,
                        retry_count=retry_count
                    )
                
                retry_count += 1
            else:
                # 重试次数用完
                return TaskResult(
                    success=False,
                    task_id=task_id,
                    output_dir=output_dir,
                    output_files=[],
                    output="",
                    error=f"达到最大重试次数，最后错误: {check_result.get('error')}",
                    session_id=session_id,
                    cost_usd=cost_usd,
                    duration_ms=duration_ms,
                    retry_count=retry_count
                )
        
        return TaskResult(
            success=False,
            task_id=task_id,
            output_dir=output_dir,
            output_files=[],
            output="",
            error="未知错误",
            session_id=session_id,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            retry_count=retry_count
        )
    
    def close_session(self, node_id: str) -> bool:
        """
        关闭会话（目前只是清理本地记录，实际会话由 Claude Code 管理）
        
        Args:
            node_id: 节点ID
        
        Returns:
            是否成功
        """
        if node_id in self.sessions:
            del self.sessions[node_id]
            print(f"[关闭会话] {node_id}")
            return True
        return False


# 示例用法
if __name__ == "__main__":
    coordinator = TaskCoordinator()
    
    # 示例 1: 简单任务
    print("=== 示例 1: 简单任务 ===")
    result = coordinator.send_task_and_wait(
        node_id="claude",
        instruction="创建一个简单的 Python Hello World 程序",
        max_retries=1
    )
    
    print(f"\n任务ID: {result.task_id}")
    print(f"成功: {result.success}")
    print(f"输出: {result.output[:200]}...")
    print(f"生成文件: {result.output_files}")
    print(f"成本: ${result.cost_usd}")
    print(f"重试次数: {result.retry_count}")
    
    # 示例 2: 带自定义检查的任务
    print("\n=== 示例 2: 带自定义检查的任务 ===")
    
    def check_has_calculator(output_dir: str) -> dict:
        """检查是否包含计算器实现"""
        calc_file = Path(output_dir) / "calculator.py"
        if not calc_file.exists():
            return {"ok": False, "error": "缺少 calculator.py 文件"}
        
        code = calc_file.read_text()
        if "class Calculator" not in code:
            return {"ok": False, "error": "缺少 Calculator 类定义"}
        
        return {"ok": True}
    
    result = coordinator.send_task_and_wait(
        node_id="claude",
        instruction="""创建一个 Python 计算器类：
1. 类名为 Calculator
2. 支持 add, subtract, multiply, divide 方法
3. 保存为 calculator.py""",
        check_callback=check_has_calculator,
        max_retries=2
    )
    
    print(f"\n任务ID: {result.task_id}")
    print(f"成功: {result.success}")
    if result.success:
        print(f"生成文件: {result.output_files}")
    else:
        print(f"失败原因: {result.error}")
