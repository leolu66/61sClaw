#!/usr/bin/env python3
"""
任务：冒险-试炼之地
触发路径：冒险按钮 → 试炼之地
5个子任务，每个领取2次免费：
- 废弃矿山（中心坐标：970, 610）
- 远古战场（中心坐标：970, 840）
- 神秘森林（中心坐标：970, 1090）
- 月光神殿（中心坐标：970, 1330）
- 宝石矿洞（中心坐标：970, 1500）
"""

import sys
import json
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mouse_controller import MouseController


DEFAULT_CONFIG = {
    "adventure_button": {
        "screen_x": 690,
        "screen_y": 845,
        "radius": 40,
        "description": "冒险按钮 - 直径80的圆"
    },
    "trial_land_button": {
        "screen_x": 960,
        "screen_y": 1200,
        "description": "试炼之地按钮 - 中心(960, 1200)"
    },
    "waste_mine": {
        "screen_x": 970,
        "screen_y": 610,
        "description": "废弃矿山 - 中心(970, 610)"
    },
    "ancient_battlefield": {
        "screen_x": 970,
        "screen_y": 840,
        "description": "远古战场 - 中心(970, 840)"
    },
    "mystic_forest": {
        "screen_x": 970,
        "screen_y": 1090,
        "description": "神秘森林 - 中心(970, 1090)"
    },
    "moonlight_temple": {
        "screen_x": 970,
        "screen_y": 1330,
        "description": "月光神殿 - 中心(970, 1330)"
    },
    "gem_cave": {
        "screen_x": 970,
        "screen_y": 1500,
        "description": "宝石矿洞 - 中心(970, 1500)"
    },
    "claim_button": {
        "screen_x": 960,
        "screen_y": 1200,
        "size": [180, 80],
        "description": "领取按钮 - 中心(960, 1200)"
    },
    "claim_free_button": {
        "screen_x": 960,
        "screen_y": 1050,
        "size": [180, 80],
        "description": "免费领取按钮 - 中心(960, 1050)"
    },
    "close_popup": {
        "x_range": [630, 1290],
        "y_options": [[325, 695], [1070, 1520]],
        "description": "关闭弹窗点击区域"
    },
    "back_button": {
        "screen_x": 680,
        "screen_y": 1455,
        "radius": 30,
        "description": "返回按钮 - 直径60的圆"
    },
    "trial_back_button": {
        "screen_x": 680,
        "screen_y": 1455,
        "radius": 30,
        "description": "试炼之地返回按钮"
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


def move_click_with_offset(controller: MouseController, x: int, y: int, 
                           offset_range: int = 10, description: str = ""):
    """移动并点击，带随机偏移"""
    offset_x = random.randint(-offset_range, offset_range)
    offset_y = random.randint(-offset_range, offset_range)
    target_x = x + offset_x
    target_y = y + offset_y
    
    if description:
        print(f"  {description}: 中心({x}, {y}) → 实际({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    return target_x, target_y


def close_popup(controller: MouseController, coords: dict):
    """关闭弹窗"""
    close_popup = coords.get('close_popup', {})
    x_range = close_popup.get('x_range', [630, 1290])
    y_options = close_popup.get('y_options', [[325, 695], [1070, 1520]])
    
    close_x = random.randint(x_range[0], x_range[1])
    y_zone = random.choice(y_options)
    close_y = random.randint(y_zone[0], y_zone[1])
    
    print(f"  关闭弹窗: ({close_x}, {close_y})", flush=True)
    controller.move_and_click(close_x, close_y)


def claim_twice(controller: MouseController, coords: dict, location_name: str):
    """在某个地点领取2次"""
    print(f"\n    领取 [{location_name}]", flush=True)
    
    for i in range(1, 3):
        print(f"      第{i}次领取...", flush=True)
        
        # 点击免费领取按钮
        claim_btn = coords.get('claim_free_button', {})
        move_click_with_offset(controller, claim_btn['screen_x'], claim_btn['screen_y'],
                               offset_range=10, description=f"免费领取")
        
        time.sleep(1.5)
        
        # 关闭成功提示弹窗
        close_popup(controller, coords)
        time.sleep(0.5)


def run_adventure_trial_task() -> bool:
    """执行冒险-试炼之地任务"""
    print("=" * 50, flush=True)
    print("任务：冒险-试炼之地", flush=True)
    print("=" * 50, flush=True)
    
    # 聚焦到游戏窗口
    print("\n[步骤] 请在3秒内切换到游戏窗口！", flush=True)
    time.sleep(3)
    
    # 初始化鼠标控制器
    print("\n[初始化] 加载配置...", flush=True)
    config_path = Path(__file__).parent / "config.json"
    mouse_config = {}
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            mouse_config = json.load(f).get('settings', {})
    
    controller = MouseController(mouse_config)
    coords = load_config()
    
    # ========== 步骤1：进入冒险 ==========
    print("\n[步骤1] 进入冒险...", flush=True)
    adventure = coords.get('adventure_button', {})
    move_click_with_offset(controller, adventure['screen_x'], adventure['screen_y'],
                           offset_range=40, description="冒险按钮")
    time.sleep(1.5)
    
    # ========== 步骤2：进入试炼之地 ==========
    print("\n[步骤2] 进入试炼之地...", flush=True)
    trial_land = coords.get('trial_land_button', {})
    move_click_with_offset(controller, trial_land['screen_x'], trial_land['screen_y'],
                           offset_range=10, description="试炼之地")
    time.sleep(2)
    
    # 5个子任务的坐标列表
    locations = [
        ("废弃矿山", coords.get('waste_mine', {})),
        ("远古战场", coords.get('ancient_battlefield', {})),
        ("神秘森林", coords.get('mystic_forest', {})),
        ("月光神殿", coords.get('moonlight_temple', {})),
        ("宝石矿洞", coords.get('gem_cave', {}))
    ]
    
    # ========== 步骤3：依次完成任务 ==========
    print("\n[步骤3] 依次完成5个地点...", flush=True)
    
    for loc_name, loc_coords in locations:
        print(f"\n  >> 前往 [{loc_name}]", flush=True)
        
        # 点击地点
        move_click_with_offset(controller, loc_coords['screen_x'], loc_coords['screen_y'],
                               offset_range=10, description=loc_name)
        time.sleep(1.5)
        
        # 领取2次
        claim_twice(controller, coords, loc_name)
        
        time.sleep(0.5)
    
    # ========== 步骤4：返回主界面 ==========
    print("\n[步骤4] 返回主界面...", flush=True)
    back = coords.get('trial_back_button', {})
    move_click_with_offset(controller, back['screen_x'], back['screen_y'],
                           offset_range=30, description="返回按钮")
    time.sleep(1)
    
    # 再返回一次确保回到主界面
    move_click_with_offset(controller, back['screen_x'], back['screen_y'],
                           offset_range=30, description="返回按钮")
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！共领取 5个地点 × 2次 = 10次", flush=True)
    print("=" * 50, flush=True)
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='冒险-试炼之地任务')
    parser.add_argument('--auto-focus', action='store_true', help='尝试自动聚焦窗口')
    
    args = parser.parse_args()
    
    run_adventure_trial_task()
