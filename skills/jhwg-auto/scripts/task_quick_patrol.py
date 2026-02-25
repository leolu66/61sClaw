#!/usr/bin/env python3
"""
任务：快速巡逻 - 执行快速巡逻（每日有限制次数）
点击快速巡逻 -> 点击免费领取（2次）-> 关闭提示
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


def run_quick_patrol_task() -> bool:
    """
    执行快速巡逻任务（每日有限制次数）
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：快速巡逻 - 每日有限制次数", flush=True)
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
        
        # 步骤4：点击巡逻奖励按钮（进入巡逻界面）
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
        
        # 步骤6：点击快速巡逻按钮
        print("\n[步骤6] 点击快速巡逻按钮...", flush=True)
        quick_patrol_x = 835
        quick_patrol_y = 1257
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-30, 30)
        target_x = quick_patrol_x + offset_x
        target_y = quick_patrol_y + offset_y
        
        print(f"快速巡逻按钮中心: ({quick_patrol_x}, {quick_patrol_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击快速巡逻按钮", flush=True)
        
        # 步骤7：等待快速巡逻成功提示
        print("\n[步骤7] 等待快速巡逻成功提示...", flush=True)
        time.sleep(1.5)
        
        # 步骤8：点击免费领取按钮
        print("\n[步骤8] 点击免费领取按钮...", flush=True)
        free_claim_x = 960
        free_claim_y = 1050
        
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = free_claim_x + offset_x
        target_y = free_claim_y + offset_y
        
        print(f"免费领取按钮中心: ({free_claim_x}, {free_claim_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击免费领取按钮", flush=True)
        
        # 步骤9：等待领取完成
        print("\n[步骤9] 等待领取完成...", flush=True)
        time.sleep(1)
        
        # 步骤10：再次点击免费领取按钮
        print("\n[步骤10] 再次点击免费领取按钮...", flush=True)
        
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = free_claim_x + offset_x
        target_y = free_claim_y + offset_y
        
        print(f"免费领取按钮中心: ({free_claim_x}, {free_claim_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已再次点击免费领取按钮", flush=True)
        
        # 步骤11：等待
        print("\n[步骤11] 等待...", flush=True)
        wait_time = random.uniform(0.5, 1.0)
        time.sleep(wait_time)
        
        # 步骤12：关闭提示
        print("\n[步骤12] 关闭提示...", flush=True)
        
        close_offset_x = random.randint(-10, 10)
        close_offset_y = random.randint(10, 20)
        close_x = free_claim_x + close_offset_x
        close_y = free_claim_y + close_offset_y
        
        print(f"关闭提示点击位置: ({close_x}, {close_y}) [Y>1100区域]", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭提示", flush=True)
        time.sleep(1)
        
        # 步骤13：关闭战利品弹窗
        print("\n[步骤13] 关闭战利品弹窗...", flush=True)
        close_btn_x = 1230
        close_btn_y = 580
        
        offset_x = random.randint(-12, 12)
        offset_y = random.randint(-12, 12)
        target_x = close_btn_x + offset_x
        target_y = close_btn_y + offset_y
        
        print(f"关闭按钮中心: ({close_btn_x}, {close_btn_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭战利品提示窗口", flush=True)
    
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
    run_quick_patrol_task()
