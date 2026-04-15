#!/usr/bin/env python3
"""
浏览器标签聚焦工具
用于切换到游戏所在的 Chrome Tab
"""

import subprocess
import json
import time
from typing import Optional


class BrowserTabFocus:
    """浏览器标签聚焦器"""
    
    def __init__(self, game_url_keyword: str = "wanyiwan"):
        """
        初始化
        
        Args:
            game_url_keyword: 游戏URL的关键词，用于识别游戏标签页
        """
        self.game_url_keyword = game_url_keyword
    
    def focus_game_tab(self) -> bool:
        """
        聚焦到游戏标签页
        
        使用多种方法尝试激活游戏窗口：
        1. 首先尝试通过 OpenClaw Browser Relay（如果可用）
        2. 尝试通过窗口标题查找 Chrome 窗口
        
        Returns:
            是否成功聚焦
        """
        # 方法1：尝试使用 OpenClaw 的 browser 工具（如果运行在 OpenClaw 环境）
        try:
            return self._focus_via_openclaw()
        except Exception as e:
            print(f"OpenClaw 方式失败: {e}")
        
        # 方法2：通过窗口标题查找并激活
        try:
            return self._focus_via_window_title()
        except Exception as e:
            print(f"窗口标题方式失败: {e}")
        
        return False
    
    def _focus_via_openclaw(self) -> bool:
        """通过 OpenClaw browser 工具聚焦"""
        # 这个函数在 OpenClaw 环境中会被替换为实际的工具调用
        # 在独立运行时打印提示
        print("提示：在 OpenClaw 环境中，可以使用 browser 工具自动切换标签页")
        print("      请确保 Chrome 扩展已安装并连接到 OpenClaw")
        raise NotImplementedError("需要在 OpenClaw 环境中运行")
    
    def _focus_via_window_title(self) -> bool:
        """通过窗口标题查找并激活 Chrome 窗口"""
        # Windows 平台使用 PowerShell
        import platform
        
        if platform.system() != 'Windows':
            print("非 Windows 平台，请手动切换到游戏窗口")
            return False
        
        # 使用 PowerShell 查找包含游戏关键词的 Chrome 窗口
        ps_script = f'''
        $chromeWindows = Get-Process | Where-Object {{ $_.ProcessName -eq "chrome" -and $_.MainWindowTitle -ne "" }}
        foreach ($window in $chromeWindows) {{
            if ($window.MainWindowTitle -like "*{self.game_url_keyword}*") {{
                # 激活窗口
                $hwnd = $window.MainWindowHandle
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Win32 {{
                        [DllImport("user32.dll")]
                        [return: MarshalAs(UnmanagedType.Bool)]
                        public static extern bool SetForegroundWindow(IntPtr hWnd);
                        
                        [DllImport("user32.dll")]
                        [return: MarshalAs(UnmanagedType.Bool)]
                        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                    }}
"@
                [Win32]::ShowWindow($hwnd, 9)  # SW_RESTORE = 9
                [Win32]::SetForegroundWindow($hwnd)
                Write-Output "FOUND"
                exit 0
            }}
        }}
        Write-Output "NOT_FOUND"
        '''
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "FOUND" in result.stdout:
                print("成功激活游戏窗口")
                time.sleep(0.5)  # 等待窗口激活
                return True
            else:
                print("未找到游戏窗口，请确保 Chrome 已打开游戏页面")
                return False
                
        except Exception as e:
            print(f"激活窗口失败: {e}")
            return False
    
    def manual_focus_instruction(self) -> None:
        """打印手动聚焦指导"""
        print("=" * 50)
        print("请手动切换到游戏窗口：")
        print(f"1. 点击 Chrome 浏览器")
        print(f"2. 切换到包含 '{self.game_url_keyword}' 的标签页")
        print("3. 等待 3 秒后开始执行...")
        print("=" * 50)
        time.sleep(3)


def focus_game_tab(use_manual: bool = False) -> bool:
    """
    便捷的聚焦函数
    
    Args:
        use_manual: 是否使用手动模式（打印提示让用户自己切换）
    
    Returns:
        是否成功聚焦
    """
    focuser = BrowserTabFocus()
    
    if use_manual:
        focuser.manual_focus_instruction()
        return True
    
    success = focuser.focus_game_tab()
    if not success:
        print("自动聚焦失败，切换到手动模式...")
        focuser.manual_focus_instruction()
        return True
    
    return success


if __name__ == '__main__':
    print("浏览器标签聚焦工具测试")
    print("尝试自动聚焦到游戏窗口...")
    
    success = focus_game_tab(use_manual=False)
    
    if success:
        print("窗口已激活，可以进行后续操作")
    else:
        print("聚焦失败")
