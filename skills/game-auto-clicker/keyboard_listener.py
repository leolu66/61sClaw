#!/usr/bin/env python3
"""
键盘监听器 - 支持ESC键中止任务
使用pynput库，更稳定可靠
"""

import sys
import threading
import time


class KeyboardListener:
    """监听键盘事件，支持ESC键中止"""
    
    def __init__(self):
        self._stop_event = threading.Event()
        self._pressed = False
        self._thread = None
        self._listener = None
    
    def start(self):
        """启动键盘监听"""
        if self._thread is not None and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._pressed = False
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止监听"""
        self._stop_event.set()
        if self._listener is not None:
            try:
                self._listener.stop()
            except:
                pass
        if self._thread is not None:
            self._thread.join(timeout=1)
    
    def is_pressed(self) -> bool:
        """检查是否按下了ESC"""
        return self._pressed
    
    def reset(self):
        """重置状态"""
        self._pressed = False
    
    def _listen(self):
        """监听循环"""
        try:
            from pynput import keyboard
            
            def on_press(key):
                try:
                    if key == keyboard.Key.esc:
                        self._pressed = True
                        print("\n[!] ESC pressed - aborting...", flush=True)
                        return False # stop listener
                except:
                    pass
            
            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.start()
            
            # 保持线程活跃
            while not self._stop_event.is_set():
                time.sleep(0.1)
                
        except Exception as e:
            print(f"[!] Keyboard listener failed: {e}", flush=True)


# 全局监听器实例
_listener = None


def get_listener() -> KeyboardListener:
    """获取全局监听器实例"""
    global _listener
    if _listener is None:
        _listener = KeyboardListener()
    return _listener


def check_esc() -> bool:
    """检查是否按下了ESC"""
    listener = get_listener()
    return listener.is_pressed()


def start_listening():
    """启动ESC监听"""
    listener = get_listener()
    listener.reset()
    listener.start()


def stop_listening():
    """停止ESC监听"""
    listener = get_listener()
    listener.stop()


if __name__ == '__main__':
    print("键盘监听器测试")
    print("按ESC键中止...")
    
    start_listening()
    
    try:
        i = 0
        while not check_esc():
            time.sleep(0.5)
            i += 1
            print(f"工作中... {i}", flush=True)
    except KeyboardInterrupt:
        pass
    
    stop_listening()
    print("已退出")
