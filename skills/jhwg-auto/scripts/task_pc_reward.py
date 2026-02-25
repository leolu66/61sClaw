#!/usr/bin/env python3
"""
任务：领取PC端奖励
点击游戏区域上方的"PC端"图标领取奖励
支持Esc键终止任务
"""

import sys
import json
import time
import random
from pathlib import Path

# 添加父目录到路径，以便导入其他模块
sys.path.insert(0, str(Path(__file__).parent))

from mouse_controller import MouseController
from browser_focus import focus_game_tab
from keyboard_listener import start_keyboard_listener, stop_keyboard_listener


# PC端图标坐标配置（相对于游戏区域的百分比）
DEFAULT_CONFIG = {
    "pc_icon": {
        "x_percent": 0.85,
        "y_percent": 0.08,
        "description": "PC端图标位置"
    },
    "reward_button": {
        "x_percent": 0.5,
        "y_percent": 0.6,
        "description": "领取奖励按钮位置"
    }
}


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('coordinates', DEFAULT_CONFIG)
    
    return DEFAULT_CONFIG


def run_pc_reward_task(use_manual_focus: bool = True) -> bool:
    """
    执行领取PC端奖励任务
    
    Args:
        use_manual_focus: 是否使用手动聚焦模式
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：领取PC端奖励", flush=True)
    print("=" * 50, flush=True)
    
    # 启动键盘监听器
    keyboard_listener = start_keyboard_listener()
    
    try:
        # 步骤1：聚焦到游戏窗口
        print("\n[步骤1] 聚焦到游戏窗口...", flush=True)
        print("请在3秒内切换到游戏窗口！", flush=True)
        print("[💡 提示: 按Esc键可随时终止任务]", flush=True)
        time.sleep(3)
        
        # 步骤2：初始化鼠标控制器
        print("\n[步骤2] 初始化鼠标控制器...", flush=True)
        config_path = Path(__file__).parent / "config.json"
        mouse_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mouse_config = json.load(f).get('settings', {})
        
        controller = MouseController(mouse_config)
        
        # 步骤3：加载坐标配置
        print("\n[步骤3] 加载坐标配置...", flush=True)
        coords = load_config()
        
        # 直接使用精确坐标
        pc_icon = coords.get('pc_icon', {})
        pc_x = pc_icon.get('screen_x', 990)
        pc_y = pc_icon.get('screen_y', 450)
        print(f"PC端按钮位置: ({pc_x}, {pc_y})", flush=True)
        
        # 步骤4：移动鼠标并点击PC端图标（带随机偏移）
        print("\n[步骤4] 移动鼠标到PC端图标并点击...", flush=True)
        print("（鼠标将模拟真人移动轨迹，点击位置带随机偏移）", flush=True)
        
        # 获取当前位置
        current_x, current_y = controller.get_position()
        print(f"当前鼠标位置: ({current_x}, {current_y})", flush=True)
        
        # 在中心点 ±10 像素范围内随机偏移
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = pc_x + offset_x
        target_y = pc_y + offset_y
        
        print(f"PC端按钮中心: ({pc_x}, {pc_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        # 移动到PC端图标并点击
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击PC端图标", flush=True)
        
        # 步骤5：等待奖励弹窗并点击领取
        print("\n[步骤5] 等待奖励弹窗...", flush=True)
        time.sleep(2)  # 等待弹窗出现
        
        # 使用领取按钮的精确坐标
        reward_btn = coords.get('reward_button', {})
        btn_x = reward_btn.get('screen_x', 960)
        btn_y = reward_btn.get('screen_y', 1120)
        
        print(f"领取按钮中心: ({btn_x}, {btn_y})", flush=True)
        
        # 在中心点 ±10 像素范围内随机偏移
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = btn_x + offset_x
        target_y = btn_y + offset_y
        
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击领取按钮", flush=True)
        
        # 步骤6：关闭恭喜画面弹窗（在原位置点击即可关闭）
        print("\n[步骤6] 关闭恭喜画面弹窗...", flush=True)
        time.sleep(1)  # 等待弹窗出现
        
        # 在领取按钮位置附近点击关闭（向下偏移小范围）
        close_offset_x = random.randint(-10, 10)
        close_offset_y = random.randint(5, 20)  # 向下偏移 5-20 像素
        close_x = btn_x + close_offset_x
        close_y = btn_y + close_offset_y
        
        print(f"关闭弹窗点击位置: ({close_x}, {close_y})", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭弹窗", flush=True)
    
    except KeyboardInterrupt:
        print("\n" + "=" * 50, flush=True)
        print("任务被用户终止！", flush=True)
        print("=" * 50, flush=True)
        return False
    
    finally:
        # 停止键盘监听器
        stop_keyboard_listener()
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！", flush=True)
    print("=" * 50, flush=True)
    
    return True


if __name__ == '__main__':
    run_pc_reward_task()
