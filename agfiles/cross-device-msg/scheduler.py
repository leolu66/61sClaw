"""
任务调度器
定时检查消息队列，执行任务，返回结果
"""

import time
import threading
from pathlib import Path
from msg_queue import poll_messages, complete_message, send_message
from executor import execute_task

# 设备名称（在小白上运行设为"小白"，在小天才上运行设为"小天才"）
DEVICE_NAME = "小白"

# 轮询间隔（秒）
POLL_INTERVAL = 10

# 运行标志
running = False


def process_messages():
    """处理待处理消息"""
    messages = poll_messages(DEVICE_NAME, limit=5)
    
    for msg in messages:
        msg_id = msg.get("id")
        from_device = msg.get("from")
        
        print(f"📥 收到消息 from {from_device}: {msg.get('content', {}).get('action')}")
        
        # 执行任务
        result = execute_task(msg)
        
        # 完成任务
        msg_path = Path("Z:/61sOpenClaw/inbox") / DEVICE_NAME / f"{msg_id}.json"
        complete_message(str(msg_path))
        
        # 发送回复
        send_message(
            from_device=DEVICE_NAME,
            to_device=from_device,
            msg_type="response",
            content={
                "original_msg_id": msg_id,
                "result": result
            }
        )
        
        print(f"✅ 消息 {msg_id} 处理完成")


def start_scheduler():
    """启动调度器"""
    global running
    running = True
    
    print(f"📅 {DEVICE_NAME} 调度器启动，每 {POLL_INTERVAL} 秒检查一次消息")
    
    while running:
        try:
            process_messages()
        except Exception as e:
            print(f"⚠️ 处理消息出错: {e}")
        
        time.sleep(POLL_INTERVAL)


def stop_scheduler():
    """停止调度器"""
    global running
    running = False
    print(f"🛑 {DEVICE_NAME} 调度器已停止")


def run_scheduler_thread():
    """在后台线程运行调度器"""
    thread = threading.Thread(target=start_scheduler, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    # 测试
    run_scheduler_thread()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()
