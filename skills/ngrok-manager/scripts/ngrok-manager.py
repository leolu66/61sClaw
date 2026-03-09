#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ngrok 管理脚本
用于启动/停止/查看 ngrok 公网映射
"""

import subprocess
import sys
import time
import json
import urllib.request
import os

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置
LOCAL_PORT = 18789
NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"

# ngrok 可执行文件路径（如果不在 PATH 中，请修改这里）
NGROK_PATH = "ngrok"  # 或使用完整路径，如: r"C:\Program Files\ngrok\ngrok.exe"


def check_ngrok_installed():
    """检查 ngrok 是否已安装"""
    try:
        result = subprocess.run(
            [NGROK_PATH, "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


def get_ngrok_processes():
    """获取所有 ngrok 进程"""
    try:
        # Windows: 使用 tasklist
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ngrok.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        processes = []
        lines = result.stdout.strip().split('\n')
        
        # 跳过标题行
        for line in lines[1:]:
            if line.strip() and 'ngrok' in line.lower():
                parts = line.strip().strip('"').split('","')
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        processes.append(pid)
                    except ValueError:
                        continue
        
        return processes
    except Exception as e:
        print(f"❌ 获取进程列表失败: {e}")
        return []


def kill_ngrok_processes():
    """终止所有 ngrok 进程"""
    processes = get_ngrok_processes()
    
    if not processes:
        return True
    
    killed = []
    for pid in processes:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                timeout=5
            )
            killed.append(pid)
        except Exception as e:
            print(f"⚠️ 终止进程 {pid} 失败: {e}")
    
    return len(killed) > 0


def get_ngrok_public_url():
    """从 ngrok API 获取公网 URL"""
    try:
        req = urllib.request.Request(
            NGROK_API_URL,
            headers={"Accept": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            for tunnel in data.get('tunnels', []):
                public_url = tunnel.get('public_url', '')
                if public_url.startswith('https://'):
                    return public_url
                elif public_url.startswith('http://'):
                    return public_url
        
        return None
    except Exception:
        return None


def start_ngrok():
    """启动 ngrok"""
    if not check_ngrok_installed():
        print("❌ ngrok 未安装或未添加到 PATH")
        print("💡 请先安装 ngrok: https://ngrok.com/download")
        print("💡 并配置 authtoken: ngrok config add-authtoken <token>")
        return False
    
    # 检查是否已在运行
    existing = get_ngrok_processes()
    if existing:
        print("⚠️ ngrok 已在运行")
        url = get_ngrok_public_url()
        if url:
            print(f"🌐 公网地址: {url}")
        return True
    
    # 启动 ngrok
    try:
        # 使用 CREATE_NEW_PROCESS_GROUP 让进程在后台运行
        subprocess.Popen(
            [NGROK_PATH, "http", str(LOCAL_PORT), "--log=stdout"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        
        # 等待 ngrok 启动并获取 URL
        print("⏳ 正在启动 ngrok...")
        time.sleep(3)
        
        url = get_ngrok_public_url()
        
        if url:
            print("✅ ngrok 已启动")
            print(f"🌐 公网地址: {url}")
            print(f"📍 本地映射: 127.0.0.1:{LOCAL_PORT} → 公网")
            print("💡 使用此地址远程访问 OpenClaw Control UI")
            return True
        else:
            print("⚠️ ngrok 已启动，但无法获取公网地址")
            print("💡 请稍等几秒后手动检查: http://127.0.0.1:4040")
            return True
            
    except Exception as e:
        print(f"❌ 启动 ngrok 失败: {e}")
        return False


def stop_ngrok():
    """停止 ngrok"""
    processes = get_ngrok_processes()
    
    if not processes:
        print("ℹ️ ngrok 未在运行")
        return True
    
    if kill_ngrok_processes():
        print("✅ ngrok 已停止")
        for pid in processes:
            print(f"🔍 终止进程: ngrok.exe (PID: {pid})")
        return True
    else:
        print("❌ 停止 ngrok 失败")
        return False


def status_ngrok():
    """查看 ngrok 状态"""
    processes = get_ngrok_processes()
    
    if not processes:
        print("📊 ngrok 状态: 未运行")
        return False
    
    print("📊 ngrok 状态: 运行中")
    print(f"🔢 进程数: {len(processes)}")
    
    url = get_ngrok_public_url()
    if url:
        print(f"🌐 公网地址: {url}")
        print(f"🔌 本地端口: {LOCAL_PORT}")
    else:
        print("⚠️ 无法获取公网地址，ngrok 可能还在启动中")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python ngrok-manager.py <start|stop|status>")
        print("")
        print("命令:")
        print("  start   - 启动 ngrok")
        print("  stop    - 停止 ngrok")
        print("  status  - 查看 ngrok 状态")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success = start_ngrok()
    elif command == "stop":
        success = stop_ngrok()
    elif command == "status":
        success = status_ngrok()
    else:
        print(f"❌ 未知命令: {command}")
        print("用法: python ngrok-manager.py <start|stop|status>")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
