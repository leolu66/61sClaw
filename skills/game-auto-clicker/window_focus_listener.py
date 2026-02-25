#!/usr/bin/env python3
"""
窗口焦点监听器 - 检测游戏窗口是否失去焦点
当用户切换到其他窗口时，任务自动中止
"""

import sys
import threading
import time


class WindowFocusListener:
    """监听窗口焦点变化"""
    
    def __init__(self, game_window_title: str = None):
        self._stop_event = threading.Event()
        self._lost_focus = False
        self._thread = None
        self._game_title = game_window_title or "支付宝"  # 游戏窗口标题关键词
    
    def start(self):
        """启动窗口焦点监听"""
        if self._thread is not None and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._lost_focus = False
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        print("[+] Window focus listener started", flush=True)
    
    def stop(self):
        """停止监听"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
    
    def is_lost_focus(self) -> bool:
        """检查是否失去焦点"""
        return self._lost_focus
    
    def reset(self):
        """重置状态"""
        self._lost_focus = False
    
    def _listen(self):
        """监听循环"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Windows API
            GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
            GetWindowTextW = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
            
            # 保存初始窗口
            initial_window = GetForegroundWindow()
            
            while not self._stop_event.is_set():
                time.sleep(0.3)
                
                current_window = GetForegroundWindow()
                
                # 如果窗口变化了
                if current_window != initial_window:
                    # 获取窗口标题
                    length = GetWindowTextLengthW(current_window)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        GetWindowTextW(current_window, buff, length + 1)
                        title = buff.value
                        
                        # 检查是否离开了游戏窗口
                        if self._game_title not in title:
                            # 检查是否是浏览器（可能是用户切换到其他标签页）
                            browser_keywords = ['Chrome', 'Edge', 'Firefox', 'Safari', '支付宝']
                            is_browser = any(kw in title for kw in browser_keywords)
                            
                            # 如果不是游戏相关窗口，认为是失去焦点
                            game_keywords = ['支付宝', '小程序', '几何王国']
                            is_game = any(kw in title for kw in game_keywords)
                            
                            if not is_game:
                                self._lost_focus = True
                                print(f"\n[!] Window lost focus: {title}", flush=True)
                                print("[!] Task will abort when clicking...", flush=True)
                                break
                            
                            # 更新窗口句柄
                            initial_window = current_window
                
        except Exception as e:
            print(f"[!] Window focus listener failed: {e}", flush=True)


# 全局监听器实例
_listener = None


def get_listener(game_title: str = None) -> WindowFocusListener:
    """获取全局监听器实例"""
    global _listener
    if _listener is None:
        _listener = WindowFocusListener(game_title)
    return _listener


def check_focus_lost() -> bool:
    """检查是否失去焦点"""
    listener = get_listener()
    return listener.is_lost_focus()


def start_listening(game_title: str = None):
    """启动焦点监听"""
    global _listener
    _listener = WindowFocusListener(game_title)
    _listener.start()


def stop_listening():
    """停止焦点监听"""
    if _listener is not None:
        _listener.stop()


if __name__ == '__main__':
    print("Window Focus Listener Test")
    print("Switch to another window to test...")
    
    start_listening()
    
    try:
        i = 0
        while not check_focus_lost():
            time.sleep(0.5)
            i += 1
            if i % 4 == 0:
                print(f"Monitoring... {i//2}s", flush=True)
    except KeyboardInterrupt:
        pass
    
    stop_listensing()
    print("Done")
