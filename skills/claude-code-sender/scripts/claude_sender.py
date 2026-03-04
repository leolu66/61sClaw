#!/usr/bin/env python3
"""
Claude Code SDK 发送器
通过 Python 封装简化 Claude Code 的调用

使用方法:
    from claude_sender import send_to_claude, ClaudeCodeOptions
    
    result = send_to_claude("编写一个快速排序函数")
    print(result["text"])
"""

import subprocess
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


@dataclass
class ClaudeCodeOptions:
    """Claude Code 调用选项"""
    max_turns: Optional[int] = None
    output_format: str = "text"  # text, json, stream-json
    system_prompt: Optional[str] = None
    append_system_prompt: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    disallowed_tools: Optional[List[str]] = None
    permission_mode: Optional[str] = None  # acceptEdits, bypassPermissions, plan
    cwd: Optional[Union[str, Path]] = None
    mcp_config: Optional[Union[str, Path]] = None
    verbose: bool = False
    timeout: Optional[int] = 300  # 秒


def _build_args(options: ClaudeCodeOptions) -> List[str]:
    """构建命令行参数"""
    args = ["claude", "-p"]
    
    if options.output_format != "text":
        args.extend(["--output-format", options.output_format])
    
    if options.max_turns is not None:
        args.extend(["--max-turns", str(options.max_turns)])
    
    if options.system_prompt:
        args.extend(["--system-prompt", options.system_prompt])
    
    if options.append_system_prompt:
        args.extend(["--append-system-prompt", options.append_system_prompt])
    
    if options.allowed_tools:
        args.extend(["--allowed-tools", ",".join(options.allowed_tools)])
    
    if options.disallowed_tools:
        args.extend(["--disallowed-tools", ",".join(options.disallowed_tools)])
    
    if options.permission_mode:
        args.extend(["--permission-mode", options.permission_mode])
    
    if options.cwd:
        args.extend(["--cwd", str(options.cwd)])
    
    if options.mcp_config:
        args.extend(["--mcp-config", str(options.mcp_config)])
    
    if options.verbose:
        args.append("--verbose")
    
    return args


def send_to_claude(
    prompt: str,
    options: Optional[ClaudeCodeOptions] = None,
    input_data: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送消息到 Claude Code
    
    Args:
        prompt: 提示词
        options: 调用选项
        input_data: 通过 stdin 传入的额外数据
    
    Returns:
        包含响应结果的字典
        {
            "success": bool,
            "text": str,  # 响应文本
            "json": dict,  # JSON 格式的完整响应（如果 output_format 为 json）
            "session_id": str,
            "cost_usd": float,
            "duration_ms": int,
            "error": str  # 如果失败
        }
    """
    if options is None:
        options = ClaudeCodeOptions()
    
    # 检查 API 密钥
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "success": False,
            "error": "未设置 ANTHROPIC_API_KEY 环境变量",
            "text": ""
        }
    
    args = _build_args(options)
    args.append(prompt)
    
    try:
        result = subprocess.run(
            args,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=options.timeout,
            cwd=options.cwd if options.cwd else os.getcwd()
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        # 解析输出
        if options.output_format == "json":
            try:
                json_data = json.loads(stdout)
                return {
                    "success": json_data.get("subtype") == "success" and not json_data.get("is_error", False),
                    "text": json_data.get("result", ""),
                    "json": json_data,
                    "session_id": json_data.get("session_id"),
                    "cost_usd": json_data.get("total_cost_usd", 0),
                    "duration_ms": json_data.get("duration_ms", 0),
                    "error": None
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"JSON 解析失败: {e}",
                    "text": stdout,
                    "json": None
                }
        else:
            # 文本格式
            success = result.returncode == 0
            return {
                "success": success,
                "text": stdout,
                "json": None,
                "error": stderr if not success else None
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"请求超时（超过 {options.timeout} 秒）",
            "text": ""
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "未找到 claude 命令，请先安装: npm install -g @anthropic-ai/claude-code",
            "text": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"执行错误: {str(e)}",
            "text": ""
        }


def send_to_claude_with_file(
    prompt: str,
    file_path: Union[str, Path],
    options: Optional[ClaudeCodeOptions] = None
) -> Dict[str, Any]:
    """
    发送消息到 Claude Code，并传入文件内容
    
    Args:
        prompt: 提示词（如 "解释这段代码"）
        file_path: 文件路径
        options: 调用选项
    
    Returns:
        响应结果字典
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            "success": False,
            "error": f"文件不存在: {file_path}",
            "text": ""
        }
    
    try:
        content = file_path.read_text(encoding="utf-8")
        full_prompt = f"{prompt}\n\n文件内容 ({file_path}):\n```\n{content}\n```"
        return send_to_claude(full_prompt, options)
    except Exception as e:
        return {
            "success": False,
            "error": f"读取文件失败: {str(e)}",
            "text": ""
        }


def continue_conversation(
    prompt: str,
    session_id: Optional[str] = None,
    options: Optional[ClaudeCodeOptions] = None
) -> Dict[str, Any]:
    """
    继续已有对话
    
    Args:
        prompt: 新的提示词
        session_id: 会话 ID（为 None 则继续最近对话）
        options: 调用选项
    
    Returns:
        响应结果字典
    """
    if options is None:
        options = ClaudeCodeOptions()
    
    args = ["claude", "-p"]
    
    if session_id:
        args.extend(["--resume", session_id])
    else:
        args.append("--continue")
    
    if options.output_format != "text":
        args.extend(["--output-format", options.output_format])
    
    args.append(prompt)
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=options.timeout
        )
        
        stdout = result.stdout
        
        if options.output_format == "json":
            try:
                json_data = json.loads(stdout)
                return {
                    "success": json_data.get("subtype") == "success",
                    "text": json_data.get("result", ""),
                    "json": json_data,
                    "session_id": json_data.get("session_id"),
                    "cost_usd": json_data.get("total_cost_usd", 0),
                    "duration_ms": json_data.get("duration_ms", 0),
                    "error": None
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "JSON 解析失败",
                    "text": stdout
                }
        else:
            return {
                "success": result.returncode == 0,
                "text": stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"执行错误: {str(e)}",
            "text": ""
        }


# 示例用法
if __name__ == "__main__":
    # 示例 1: 简单调用
    print("=== 示例 1: 简单调用 ===")
    result = send_to_claude("用 Python 编写一个快速排序函数")
    print(f"成功: {result['success']}")
    print(f"响应:\n{result['text'][:500]}...")
    print()
    
    # 示例 2: JSON 输出
    print("=== 示例 2: JSON 输出 ===")
    options = ClaudeCodeOptions(output_format="json", max_turns=3)
    result = send_to_claude("编写一个斐波那契数列函数", options)
    print(f"成功: {result['success']}")
    if result["json"]:
        print(f"会话 ID: {result['session_id']}")
        print(f"成本: ${result['cost_usd']}")
        print(f"耗时: {result['duration_ms']}ms")
    print()
    
    # 示例 3: 带文件
    print("=== 示例 3: 带文件 ===")
    # 创建一个测试文件
    test_file = Path("test_code.py")
    test_file.write_text("def hello():\n    print('Hello World')")
    
    result = send_to_claude_with_file("优化这段代码", test_file)
    print(f"成功: {result['success']}")
    print(f"响应:\n{result['text'][:500]}...")
    
    # 清理
    test_file.unlink()
