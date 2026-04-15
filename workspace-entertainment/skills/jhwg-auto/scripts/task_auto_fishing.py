#!/usr/bin/env python3
"""
任务：开启自动钓鱼
点击钓鱼按钮 -> 点击自动 -> 点击开始 -> 返回主界面
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
from keyboard_listener import start_keyboard_listener, stop_keyboard_listener


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('coordinates', {})
    
    return {}


def run_auto_fishing_task() -> bool:
    """
    执行开启自动钓鱼任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：开启自动钓鱼", flush=True)
    print("=" * 50, flush=True)
    
    # 启动键盘监听器
    keyboard_listener = start_keyboard_listener()
    
    try:
        # 步骤1：聚焦到游戏窗口
        print("\n[步骤1] 聚焦到游戏窗口...", flush=True)
        print("请在3秒内切换到游戏窗口！", flush=True)
        print("[提示: 按Esc键可随时终止任务]", flush=True)
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
        
        # 步骤4：点击钓鱼按钮
        fishing_btn = coords.get('fishing_button', {})
        fishing_x = fishing_btn.get('screen_x', 1010)
        fishing_y = fishing_btn.get('screen_y', 1436)
        fishing_size = fishing_btn.get('size', 80)
        
        print("\n[步骤4] 点击钓鱼按钮...", flush=True)
        
        half_size = int(fishing_size / 2 * 0.7)
        offset_x = random.randint(-half_size, half_size)
        offset_y = random.randint(-half_size, half_size)
        target_x = fishing_x + offset_x
        target_y = fishing_y + offset_y
        
        print(f"钓鱼按钮中心: ({fishing_x}, {fishing_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击钓鱼按钮", flush=True)
        
        # 步骤5：等待钓鱼弹窗
        print("\n[步骤5] 等待钓鱼弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤6：点击自动按钮
        auto_btn = coords.get('fishing_auto_button', {})
        auto_x = auto_btn.get('screen_x', 1240)
        auto_y = auto_btn.get('screen_y', 1080)
        auto_radius = auto_btn.get('radius', 30)
        
        print("\n[步骤6] 点击自动按钮...", flush=True)
        
        offset_x = random.randint(-int(auto_radius*0.7), int(auto_radius*0.7))
        offset_y = random.randint(-int(auto_radius*0.7), int(auto_radius*0.7))
        target_x = auto_x + offset_x
        target_y = auto_y + offset_y
        
        print(f"自动按钮中心: ({auto_x}, {auto_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击自动按钮", flush=True)
        
        # 步骤7：等待自动钓鱼提示弹窗
        print("\n[步骤7] 等待自动钓鱼提示弹窗...", flush=True)
        time.sleep(1.5)
        
        # 步骤8：点击开始按钮
        start_btn = coords.get('fishing_start_button', {})
        start_x = start_btn.get('screen_x', 962)
        start_y = start_btn.get('screen_y', 1250)
        
        print("\n[步骤8] 点击开始按钮...", flush=True)
        
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = start_x + offset_x
        target_y = start_y + offset_y
        
        print(f"开始按钮中心: ({start_x}, {start_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击开始按钮", flush=True)
        
        # 步骤9：等待自动钓鱼启动
        print("\n[步骤9] 等待自动钓鱼启动...", flush=True)
        time.sleep(1.5)
        
        # 步骤10：点击返回按钮
        back_btn = coords.get('fishing_back_button', {})
        back_x = back_btn.get('screen_x', 680)
        back_y = back_btn.get('screen_y', 1455)
        back_radius = back_btn.get('radius', 30)
        
        print("\n[步骤10] 点击返回按钮...", flush=True)
        
        offset_x = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        offset_y = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        target_x = back_x + offset_x
        target_y = back_y + offset_y
        
        print(f"返回按钮中心: ({back_x}, {back_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击返回按钮", flush=True)
    
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
    run_auto_fishing_task()
