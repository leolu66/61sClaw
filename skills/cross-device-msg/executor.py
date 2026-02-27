"""
任务执行器
根据消息内容执行相应任务
"""

import os
import subprocess
from pathlib import Path

# 设备名称
DEVICE_NAME = "小白"


# 注册任务处理器
TASK_HANDLERS = {}


def register_task(action: str):
    """装饰器：注册任务处理器"""
    def decorator(func):
        TASK_HANDLERS[action] = func
        return func
    return decorator


@register_task("ping")
def handle_ping(content: dict):
    """处理 ping 任务"""
    return {"result": "pong", "from": DEVICE_NAME}


@register_task("echo")
def handle_echo(content: dict):
    """处理 echo 任务"""
    return {"result": content.get("message", "no message")}


@register_task("run_script")
def handle_run_script(content: dict):
    """处理运行脚本任务"""
    script_path = content.get("script_path")
    if not script_path:
        return {"error": "script_path required"}
    
    try:
        # 安全检查：只允许运行 agfiles 目录下的脚本
        safe_base = Path("C:/Users/luzhe/.openclaw/workspace-main/agfiles")
        full_path = (safe_base / script_path).resolve()
        
        if not str(full_path).startswith(str(safe_base.resolve())):
            return {"error": "invalid path"}
        
        # 执行脚本
        result = subprocess.run(
            ["python", str(full_path)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"error": str(e)}


@register_task("list_files")
def handle_list_files(content: dict):
    """处理列出文件任务"""
    dir_path = content.get("path", ".")
    try:
        items = list(Path(dir_path).iterdir())
        return {
            "items": [str(i) for i in items],
            "count": len(items)
        }
    except Exception as e:
        return {"error": str(e)}


def execute_task(msg: dict) -> dict:
    """
    执行任务
    
    Args:
        msg: 消息对象
    
    Returns:
        执行结果
    """
    content = msg.get("content", {})
    action = content.get("action")
    
    if not action:
        return {"error": "action required"}
    
    handler = TASK_HANDLERS.get(action)
    if not handler:
        return {"error": f"unknown action: {action}"}
    
    try:
        result = handler(content)
        return result
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # 测试
    test_msg = {
        "id": "test-1",
        "content": {"action": "ping", "params": {}}
    }
    result = execute_task(test_msg)
    print(f"测试结果: {result}")
