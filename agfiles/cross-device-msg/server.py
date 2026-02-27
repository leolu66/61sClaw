"""
跨设备通信 HTTP 服务
提供 REST API 供局域网内设备调用
"""

from flask import Flask, request, jsonify
import threading
import json
from msg_queue import send_message, poll_messages, ack_message, complete_message

app = Flask(__name__)

# 本设备名称
DEVICE_NAME = "小白"  # 在小白机器上运行


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "device": DEVICE_NAME})


@app.route("/send", methods=["POST"])
def send():
    """
    发送消息到目标设备
    
    请求体:
    {
        "to": "小天才",
        "type": "task",
        "content": {"action": "xxx", "params": {}}
    }
    """
    data = request.json
    
    msg_id = send_message(
        from_device=DEVICE_NAME,
        to_device=data.get("to", "小天才"),
        msg_type=data.get("type", "task"),
        content=data.get("content", {})
    )
    
    return jsonify({"success": True, "msg_id": msg_id})


@app.route("/poll", methods=["GET"])
def poll():
    """
    拉取未读消息
    
    Query params:
        limit: 最多拉取数量，默认 10
    """
    limit = int(request.args.get("limit", 10))
    messages = poll_messages(DEVICE_NAME, limit)
    
    return jsonify({
        "success": True,
        "messages": messages,
        "count": len(messages)
    })


@app.route("/ack", methods=["POST"])
def ack():
    """
    签收消息
    
    请求体:
    {
        "msg_id": "xxx"
    }
    """
    msg_id = request.json.get("msg_id")
    if not msg_id:
        return jsonify({"success": False, "error": "msg_id required"}), 400
    
    # 构造文件路径
    from pathlib import Path
    msg_path = Path("Z:/61sOpenClaw/inbox") / DEVICE_NAME / f"{msg_id}.json"
    
    success = ack_message(str(msg_path))
    return jsonify({"success": success})


@app.route("/complete", methods=["POST"])
def complete():
    """
    完成消息
    
    请求体:
    {
        "msg_id": "xxx"
    }
    """
    msg_id = request.json.get("msg_id")
    if not msg_id:
        return jsonify({"success": False, "error": "msg_id required"}), 400
    
    from pathlib import Path
    msg_path = Path("Z:/61sOpenClaw/inbox") / DEVICE_NAME / f"{msg_id}.json"
    
    success = complete_message(str(msg_path))
    return jsonify({"success": success})


def run_server(port=8765):
    """启动 HTTP 服务"""
    print(f"🚀 {DEVICE_NAME} 服务启动中，端口: {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run_server()
