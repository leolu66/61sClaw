#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
键盘监听器 - 支持 Esc 键终止任务
"""

import threading
import sys
import io

# 设置标准输出为 UTF-8 编码（兼容 Windows 控制台）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("警告：pynput 模块未安装，Esc 键终止功能不可用")
    print("如需使用，请运行：pip install pynput")


class KeyboardListener:
    """键盘监听器，用于捕获 Esc 键终止任务"""
    
    def __init__(self):
        self.esc_pressed = False
        self.listener = None
        self._lock = threading.Lock()
    
    def _on_press(self, key):
        """按键按下回调"""
        try:
            if key == keyboard.Key.esc:
                with self._lock:
                    self.esc_pressed = True
                print("\n[⚠️ 检测到 Esc 键，准备终止任务...]")
                return False  # 停止监听
        except Exception:
            pass
    
    def start(self):
        """开始监听键盘"""
        if not PYNPUT_AVAILABLE:
            return False
        
        self.esc_pressed = False
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.daemon = True
        self.listener.start()
        return True
    
    def stop(self):
        """停止监听键盘"""
        if self.listener and self.listener.is_alive():
            self.listener.stop()
    
    def is_esc_pressed(self) -> bool:
        """检查 Esc 键是否被按下"""
        with self._lock:
            return self.esc_pressed
    
    def check_and_raise(self):
        """检查 Esc 键是否被按下，如果是则抛出异常终止任务"""
        if self.is_esc_pressed():
            raise KeyboardInterrupt("用户按下 Esc 键终止任务")


# 全局监听器实例
_global_listener = None


def start_keyboard_listener() -> KeyboardListener:
    """启动全局键盘监听器"""
    global _global_listener
    _global_listener = KeyboardListener()
    _global_listener.start()
    print("[💡 提示：按 Esc 键可随时终止任务]")
    return _global_listener


def stop_keyboard_listener():
    """停止全局键盘监听器"""
    global _global_listener
    if _global_listener:
        _global_listener.stop()
        _global_listener = None


def check_esc_key():
    """检查 Esc 键是否被按下，返回布尔值"""
    global _global_listener
    if _global_listener:
        return _global_listener.is_esc_pressed()
    return False


if __name__ == '__main__':
    import time
    
    print("键盘监听器测试")
    print("按 Esc 键终止...")
    
    listener = start_keyboard_listener()
    
    try:
        for i in range(30):
            check_esc_key()
            print(f"等待中... {i+1}/30")
            time.sleep(1)
    except KeyboardInterrupt as e:
        print(f"\n{e}")
    finally:
        stop_keyboard_listener()
        print("测试结束")
