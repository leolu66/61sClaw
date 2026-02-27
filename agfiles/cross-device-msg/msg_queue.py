"""
跨设备消息队列模块
负责通过 NAS Z 盘收发消息
"""

import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime

# 配置
NAS_BASE = Path("Z:/61sOpenClaw")
INBOX_DIR = NAS_BASE / "inbox"


def get_inbox_path(device_name: str) -> Path:
    """获取指定设备的收件箱路径"""
    inbox = INBOX_DIR / device_name
    inbox.mkdir(parents=True, exist_ok=True)
    return inbox


def send_message(from_device: str, to_device: str, msg_type: str, content: dict) -> str:
    """
    发送消息到目标设备的收件箱
    
    Args:
        from_device: 发送方设备名
        to_device: 接收方设备名
        msg_type: 消息类型 (task|response|heartbeat)
        content: 消息内容
    
    Returns:
        消息ID
    """
    msg_id = str(uuid.uuid4())
    message = {
        "id": msg_id,
        "from": from_device,
        "to": to_device,
        "type": msg_type,
        "content": content,
        "timestamp": datetime.now().isoformat() + "Z",
        "status": "pending"  # pending, read, done
    }
    
    inbox = get_inbox_path(to_device)
    msg_file = inbox / f"{msg_id}.json"
    
    with open(msg_file, "w", encoding="utf-8") as f:
        json.dump(message, f, ensure_ascii=False, indent=2)
    
    print(f"[send] Message sent to {to_device}: {msg_id}")
    return msg_id


def poll_messages(device_name: str, limit: int = 10) -> list:
    """
    拉取未读消息
    
    Args:
        device_name: 设备名
        limit: 最多拉取数量
    
    Returns:
        消息列表
    """
    inbox = get_inbox_path(device_name)
    messages = []
    
    for msg_file in sorted(inbox.glob("*.json")):
        try:
            with open(msg_file, "r", encoding="utf-8") as f:
                msg = json.load(f)
                if msg.get("status") == "pending":
                    messages.append(msg)
                    if len(messages) >= limit:
                        break
        except Exception as e:
            print(f"[warn] Failed to read message {msg_file}: {e}")
    
    return messages


def ack_message(msg_path: str) -> bool:
    """
    签收消息（标记为已读）
    
    Args:
        msg_path: 消息文件路径
    
    Returns:
        是否成功
    """
    try:
        with open(msg_path, "r", encoding="utf-8") as f:
            msg = json.load(f)
        
        msg["status"] = "read"
        
        with open(msg_path, "w", encoding="utf-8") as f:
            json.dump(msg, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"[warn] Failed to ack message: {e}")
        return False


def complete_message(msg_path: str) -> bool:
    """
    完成消息（标记为已完成）
    
    Args:
        msg_path: 消息文件路径
    
    Returns:
        是否成功
    """
    try:
        with open(msg_path, "r", encoding="utf-8") as f:
            msg = json.load(f)
        
        msg["status"] = "done"
        msg["completed_at"] = datetime.now().isoformat() + "Z"
        
        # 移到 done 文件夹
        done_dir = Path(msg_path).parent / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        done_path = done_dir / Path(msg_path).name
        
        with open(done_path, "w", encoding="utf-8") as f:
            json.dump(msg, f, ensure_ascii=False, indent=2)
        
        # 删除原文件
        os.remove(msg_path)
        
        return True
    except Exception as e:
        print(f"[warn] Failed to complete message: {e}")
        return False


# 测试
if __name__ == "__main__":
    # 测试发送
    msg_id = send_message(
        from_device="小天才",
        to_device="小白",
        msg_type="task",
        content={"action": "ping", "params": {}}
    )
    print(f"[OK] Test message ID: {msg_id}")
    
    # 测试接收
    msgs = poll_messages("小天才")
    print(f"[inbox] Xiaotiancai has {len(msgs)} messages")
