#!/usr/bin/env python3
"""
任务：领取商店免费福利
点击商店按钮 -> 领取免费福利 -> 返回主界面
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


def run_shop_free_reward_task() -> bool:
    """
    执行领取商店免费福利任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：领取商店免费福利", flush=True)
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
    
    # 步骤4：点击商店按钮
    shop_btn = coords.get('shop_button', {})
    shop_x = shop_btn.get('screen_x', 690)
    shop_y = shop_btn.get('screen_y', 530)
    shop_radius = shop_btn.get('radius', 40)  # 直径80，半径40
    
    print("\n[步骤4] 点击商店按钮...", flush=True)
    
    # 在圆形区域内随机选择点击位置（比正方形更自然）
    angle = random.uniform(0, 2 * 3.14159)
    distance = random.uniform(0, shop_radius * 0.8)  # 留点边距
    offset_x = int(distance * random.choice([-1, 1]) * random.uniform(0.5, 1.0))
    offset_y = int(distance * random.choice([-1, 1]) * random.uniform(0.5, 1.0))
    
    # 简化为正方形偏移，但限制在圆形内
    offset_x = random.randint(-int(shop_radius*0.7), int(shop_radius*0.7))
    offset_y = random.randint(-int(shop_radius*0.7), int(shop_radius*0.7))
    
    target_x = shop_x + offset_x
    target_y = shop_y + offset_y
    
    print(f"商店按钮中心: ({shop_x}, {shop_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击商店按钮", flush=True)
    
    # 步骤5：等待特惠礼包弹窗
    print("\n[步骤5] 等待特惠礼包弹窗...", flush=True)
    time.sleep(2)
    
    # 步骤6：点击领取按钮
    claim_btn = coords.get('shop_claim_button', {})
    claim_x = claim_btn.get('screen_x', 1180)
    claim_y = claim_btn.get('screen_y', 815)
    
    print("\n[步骤6] 点击领取按钮...", flush=True)
    
    # 在中心点 ±10 像素范围内随机偏移
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    target_x = claim_x + offset_x
    target_y = claim_y + offset_y
    
    print(f"领取按钮中心: ({claim_x}, {claim_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击领取按钮", flush=True)
    
    # 步骤7：等待领取完成
    print("\n[步骤7] 等待领取完成...", flush=True)
    time.sleep(1.5)
    
    # 步骤8：点击返回按钮
    back_btn = coords.get('shop_back_button', {})
    back_x = back_btn.get('screen_x', 680)
    back_y = back_btn.get('screen_y', 1455)
    back_radius = back_btn.get('radius', 30)  # 直径60，半径30
    
    print("\n[步骤8] 点击返回按钮...", flush=True)
    
    # 在圆形区域内随机选择点击位置
    offset_x = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
    offset_y = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
    
    target_x = back_x + offset_x
    target_y = back_y + offset_y
    
    print(f"返回按钮中心: ({back_x}, {back_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击返回按钮", flush=True)
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！", flush=True)
    print("=" * 50, flush=True)
    
    return True


if __name__ == '__main__':
    run_shop_free_reward_task()
