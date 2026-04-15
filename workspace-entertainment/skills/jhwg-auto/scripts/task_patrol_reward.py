#!/usr/bin/env python3
"""
任务：巡逻奖励 - 领取巡逻奖励（每日可定时领取）
点击巡逻奖励按钮 -> 领取全部 -> 关闭提示
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


def run_patrol_reward_task() -> bool:
    """
    执行领取巡逻奖励任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：巡逻奖励 - 每日可定时领取", flush=True)
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
        
        # 步骤4：点击巡逻奖励按钮
        patrol_btn = coords.get('patrol_reward_button', {})
        patrol_x = patrol_btn.get('screen_x', 1238)
        patrol_y = patrol_btn.get('screen_y', 1257)
        patrol_radius = patrol_btn.get('radius', 30)
        
        print("\n[步骤4] 点击巡逻奖励按钮...", flush=True)
        
        offset_x = random.randint(-int(patrol_radius*0.7), int(patrol_radius*0.7))
        offset_y = random.randint(-int(patrol_radius*0.7), int(patrol_radius*0.7))
        target_x = patrol_x + offset_x
        target_y = patrol_y + offset_y
        
        print(f"巡逻奖励按钮中心: ({patrol_x}, {patrol_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击巡逻奖励按钮", flush=True)
        
        # 步骤5：等待战利品弹窗
        print("\n[步骤5] 等待战利品弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤6：点击领取全部按钮
        claim_all_btn = coords.get('patrol_claim_all_button', {})
        claim_x = claim_all_btn.get('screen_x', 1090)
        claim_y = claim_all_btn.get('screen_y', 1257)
        
        print("\n[步骤6] 点击领取全部按钮...", flush=True)
        
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = claim_x + offset_x
        target_y = claim_y + offset_y
        
        print(f"领取全部按钮中心: ({claim_x}, {claim_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击领取全部按钮", flush=True)
        
        # 步骤7：等待领取成功提示弹窗
        print("\n[步骤7] 等待领取成功提示弹窗...", flush=True)
        time.sleep(0.5)
        
        # 步骤8：关闭成功提示弹窗（在领取按钮位置向下偏移点击）
        print("\n[步骤8] 关闭成功提示弹窗...", flush=True)
        
        # 在领取按钮位置附近向下偏移 10-20 像素点击关闭
        close_offset_x = random.randint(-10, 10)
        close_offset_y = random.randint(10, 20)
        close_x = claim_x + close_offset_x
        close_y = claim_y + close_offset_y
        
        print(f"关闭弹窗点击位置: ({close_x}, {close_y})", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭成功提示弹窗", flush=True)
        
        print("\n任务完成！", flush=True)
    
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
    run_patrol_reward_task()
