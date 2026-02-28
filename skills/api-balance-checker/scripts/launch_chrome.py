"""
启动带调试端口的 Chrome（不关闭现有 Chrome）
"""
import subprocess
import time
import os
import sys
import socket

def is_debug_port_running(port=9222):
    """检查调试端口是否已在运行"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def launch_chrome_with_debug():
    """启动带调试端口的 Chrome（不关闭现有 Chrome）"""
    # 先检查是否已有调试端口运行
    if is_debug_port_running(9222):
        print("[OK] 调试端口 9222 已就绪，直接复用现有 Chrome！")
        print("[INFO] 如果当前 Chrome 已登录鲸云平台，将自动获取余额数据")
        return True

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if not chrome_path:
        print("找不到 Chrome 安装路径，请手动指定")
        return False

    print(f"使用 Chrome: {chrome_path}")
    print("[NEW] 启动新的 Chrome 实例（带调试端口）...")
    print("[INFO] 这是新的 Chrome 窗口，不影响你正在使用的 Chrome")

    # 使用独立的用户数据目录，避免与现有 Chrome 冲突
    user_data_dir = os.path.expandvars(r"%TEMP%\\chrome-debug-profile")

    # 启动 Chrome 带调试参数
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={user_data_dir}"
    ]

    subprocess.Popen(cmd, shell=True)
    print("Chrome 已启动，等待调试端口就绪...")
    time.sleep(3)

    # 检查端口
    if is_debug_port_running(9222):
        print("[OK] 调试端口 9222 已就绪!")
        print("[WARN] 新 Chrome 是空白会话，需要登录鲸云平台")
        print("[INFO] 请访问：https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        return True
    else:
        print("[ERROR] 调试端口未就绪，请手动检查")
        return False

if __name__ == "__main__":
    launch_chrome_with_debug()
