"""
网络检测模块
检测是否在局域网，可以直接与小白通信
"""

import socket
import requests
import time


# 小白台式机的 IP 和端口
XIAOBAI_HOST = "192.168.x.x"  # 需要配置实际 IP
XIAOBAI_PORT = 8765

# 检测超时
TIMEOUT = 3


def is_same_network() -> bool:
    """
    检测是否与小白在同一局域网
    
    思路：
    1. 检查本机 IP 是否在常见家庭网段
    2. 尝试连接小白机器的端口
    
    Returns:
        是否在局域网内
    """
    # 方法1：尝试 HTTP 请求
    try:
        url = f"http://{XIAOBAI_HOST}:{XIAOBAI_PORT}/health"
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            print("🌐 检测到小白在同一局域网（HTTP）")
            return True
    except Exception:
        pass
    
    # 方法2：尝试 TCP 连接
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((XIAOBAI_HOST, XIAOBAI_PORT))
        sock.close()
        if result == 0:
            print("🌐 检测到小白在同一局域网（TCP）")
            return True
    except Exception:
        pass
    
    print("🚪 不在同一局域网，切换到 NAS 消息队列模式")
    return False


def get_local_ip() -> str:
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


# 缓存检测结果，避免频繁检测
_cached_result = None
_cache_time = 0
CACHE_DURATION = 60  # 缓存 60 秒


def is_same_network_cached() -> bool:
    """带缓存的网络检测"""
    global _cached_result, _cache_time
    
    now = time.time()
    if _cached_result is not None and (now - _cache_time) < CACHE_DURATION:
        return _cached_result
    
    _cached_result = is_same_network()
    _cache_time = now
    return _cached_result


if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"本机 IP: {local_ip}")
    
    in_network = is_same_network_cached()
    print(f"是否在局域网: {in_network}")
