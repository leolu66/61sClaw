#!/usr/bin/env python3
"""
任务：领取巡逻奖励
点击巡逻奖励按钮 -> 领取全部 -> 关闭成功提示弹窗
"""

import sys
import json
import time
import random
from pathlib import Path

# 添加父目录到路径，以便导入其他模块
sys.path.insert(0, str(Path(__file__).parent))

from mouse_controller import MouseController


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
    print("任务：领取巡逻奖励", flush=True)
    print("=" * 50, flush=True)
    
    # 步骤1：聚焦到游戏窗口
    print("\n[步骤1] 聚焦到游戏窗口...", flush=True)
    print("请在3秒内切换到游戏窗口！", flush=True)
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
    patrol_radius = patrol_btn.get('radius', 30)  # 直径60，半径30
    
    print("\n[步骤4] 点击巡逻奖励按钮...", flush=True)
    
    # 在圆形区域内随机选择点击位置
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
    
    # 在中心点 ±10 像素范围内随机偏移
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
    time.sleep(1.5)
    
    # 步骤8：关闭成功提示弹窗（点击弹窗外区域）
    print("\n[步骤8] 关闭成功提示弹窗...", flush=True)
    
    # Y坐标小于700或大于1075
    y_options = [
        [325, 700],    # 弹窗上方区域
        [1075, 1520]   # 弹窗下方区域
    ]
    
    # 随机选择X坐标（游戏区域内）
    close_x = random.randint(630, 1290)
    
    # 随机选择上方或下方区域
    y_zone = random.choice(y_options)
    close_y = random.randint(y_zone[0], y_zone[1])
    
    print(f"关闭弹窗点击位置: ({close_x}, {close_y})", flush=True)
    controller.move_and_click(close_x, close_y)
    print("[OK] 已关闭成功提示弹窗", flush=True)
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！", flush=True)
    print("=" * 50, flush=True)
    
    return True


if __name__ == '__main__':
    run_patrol_reward_task()
