"""
跨设备通信客户端
小天才用这个来调用小白
"""

import requests
import time
from pathlib import Path
from msg_queue import send_message as send_nas_message, poll_messages as poll_nas_messages
from network_detect import is_same_network_cached

# 配置
XIAOBAI_HOST = "192.168.1.100"  # 小白台式机 IP，需要根据实际情况修改
XIAOBAI_PORT = 8765
DEVICE_NAME = "小天才"


class CrossDeviceClient:
    """跨设备通信客户端"""
    
    def __init__(self, target_device: str = "小白"):
        self.target_device = target_device
        self.target_host = XIAOBAI_HOST
        self.target_port = XIAOBAI_PORT
    
    def _http_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """发送 HTTP 请求"""
        url = f"http://{self.target_host}:{self.target_port}/{endpoint}"
        try:
            resp = requests.request(method, url, **kwargs)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_online(self) -> bool:
        """检测目标设备是否在线"""
        return is_same_network_cached()
    
    def send_task(self, action: str, params: dict = None) -> dict:
        """
        发送任务到目标设备
        
        Args:
            action: 任务动作
            params: 任务参数
        
        Returns:
            发送结果
        """
        if self.is_online():
            # 在家模式：HTTP 直连
            return self._http_request(
                "POST", "send",
                json={
                    "to": self.target_device,
                    "type": "task",
                    "content": {
                        "action": action,
                        "params": params or {}
                    }
                }
            )
        else:
            # 出门模式：NAS 消息队列
            msg_id = send_nas_message(
                from_device=DEVICE_NAME,
                to_device=self.target_device,
                msg_type="task",
                content={
                    "action": action,
                    "params": params or {}
                }
            )
            return {"success": True, "mode": "nas", "msg_id": msg_id}
    
    def wait_response(self, timeout: int = 60, poll_interval: int = 2) -> dict:
        """
        等待任务响应
        
        Args:
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            响应结果
        """
        start = time.time()
        
        while time.time() - start < timeout:
            # 检查本地收件箱
            messages = poll_nas_messages(DEVICE_NAME, limit=10)
            
            for msg in messages:
                if msg.get("type") == "response":
                    from pathlib import Path
                    msg_path = Path("Z:/61sOpenClaw/inbox") / DEVICE_NAME / f"{msg.get('id')}.json"
                    from msg_queue import complete_message
                    complete_message(str(msg_path))
                    return msg.get("content", {})
            
            time.sleep(poll_interval)
        
        return {"error": "timeout"}


# 便捷函数
def ping() -> bool:
    """Ping 小白"""
    client = CrossDeviceClient()
    return client.is_online()


def run_on_xiaobai(action: str, params: dict = None, wait: bool = True) -> dict:
    """
    在小白上执行任务
    
    Args:
        action: 任务动作
        params: 任务参数
        wait: 是否等待响应
    
    Returns:
        执行结果
    """
    client = CrossDeviceClient()
    
    result = client.send_task(action, params)
    
    if wait and result.get("success"):
        return client.wait_response()
    
    return result


if __name__ == "__main__":
    # 测试
    client = CrossDeviceClient()
    print(f"小白是否在线: {client.is_online()}")
    
    # 发送测试任务
    result = client.send_task("ping", {})
    print(f"发送结果: {result}")
