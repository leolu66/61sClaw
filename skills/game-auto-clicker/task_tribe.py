#!/usr/bin/env python3
"""
任务：部落
触发路径：部落按钮
任务流程：
1. 点击签到按钮（190x80长方形，中心970, 620）
2. 4个子任务：
   - 部落试炼（中心坐标：970, 780）
   - 战歌峡谷（中心坐标：970, 1000）
   - 海神遗迹（中心坐标：970, 1220）
   - 冰封王座（中心坐标：970, 1370）
3. 返回主界面
"""

import sys
import json
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mouse_controller import MouseController
from keyboard_listener import start_listening, stop_listening, check_esc


DEFAULT_CONFIG = {
    "tribe_button": {
        "screen_x": 900,
        "screen_y": 1430,
        "radius": 30,
        "description": "部落按钮 - 直径60的圆，中心(900,1430)"
    },
    "tribe_sign": {
        "screen_x": 970,
        "screen_y": 620,
        "size": [190, 80],
        "description": "签到按钮 - 中心(970, 620)"
    },
    "tribe_trial": {
        "screen_x": 970,
        "screen_y": 780,
        "description": "部落试炼 - 中心(970, 780)"
    },
    "battle_song_canyon": {
        "screen_x": 970,
        "screen_y": 1000,
        "description": "战歌峡谷 - 中心(970, 1000)"
    },
    "sea_god_ruins": {
        "screen_x": 970,
        "screen_y": 1220,
        "description": "海神遗迹 - 中心(970, 1220)"
    },
    "ice_throne": {
        "screen_x": 970,
        "screen_y": 1370,
        "description": "冰封王座 - 中心(970, 1370)"
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
    # 检查ESC
    if check_esc():
        print("\n[⚠️] 任务已中止", flush=True)
        stop_listening()
        raise KeyboardInterrupt("ESC pressed")
    
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
    # 检查ESC
    if check_esc():
        print("\n[⚠️] 任务已中止", flush=True)
        stop_listening()
        raise KeyboardInterrupt("ESC pressed")
    
    close_popup = coords.get('close_popup', {})
    x_range = close_popup.get('x_range', [630, 1290])
    y_options = close_popup.get('y_options', [[325, 695], [1070, 1520]])
    
    close_x = random.randint(x_range[0], x_range[1])
    y_zone = random.choice(y_options)
    close_y = random.randint(y_zone[0], y_zone[1])
    
    print(f"  关闭弹窗: ({close_x}, {close_y})", flush=True)
    controller.move_and_click(close_x, close_y)


def run_tribe_task() -> bool:
    """执行部落任务"""
    print("=" * 50, flush=True)
    print("任务：部落", flush=True)
    print("按 ESC 可中止任务", flush=True)
    print("=" * 50, flush=True)
    
    # 启动ESC监听
    start_listening()
    
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
    
    # 检查ESC
    if check_esc():
        print("\n[⚠️] 任务已中止", flush=True)
        stop_listening()
        return False
    
    # ========== 步骤1：进入部落 ==========
    print("\n[步骤1] 进入部落...", flush=True)
    tribe = coords.get('tribe_button', {})
    move_click_with_offset(controller, tribe['screen_x'], tribe['screen_y'],
                           offset_range=40, description="部落按钮")
    time.sleep(2)
    
    # 检查ESC
    if check_esc():
        print("\n[⚠️] 任务已中止", flush=True)
        stop_listening()
        return False
    
    # ========== 步骤2：签到 ==========
    print("\n[步骤2] 签到...", flush=True)
    sign = coords.get('tribe_sign', {})
    move_click_with_offset(controller, sign['screen_x'], sign['screen_y'],
                           offset_range=10, description="签到按钮")
    time.sleep(1.5)
    
    # 点击签到领奖按钮
    sign_claim = coords.get('tribe_sign_claim', {})
    move_click_with_offset(controller, sign_claim['screen_x'], sign_claim['screen_y'],
                           offset_range=10, description="签到领奖")
    time.sleep(1.5)
    
    # 关闭签到成功提示
    close_popup(controller, coords)
    time.sleep(0.5)
    
    # 4个子任务的坐标列表
    sub_tasks = [
        ("部落试炼", coords.get('tribe_trial', {})),
        ("战歌峡谷", coords.get('battle_song_canyon', {})),
        ("海神遗迹", coords.get('sea_god_ruins', {})),
        ("冰封王座", coords.get('ice_throne', {}))
    ]
    
    # ========== 步骤3：依次完成4个子任务 ==========
    print("\n[步骤3] 依次完成4个子任务...", flush=True)
    
    for task_name, task_coords in sub_tasks:
        print(f"\n  >> 执行 [{task_name}]", flush=True)
        
        # 点击子任务
        move_click_with_offset(controller, task_coords['screen_x'], task_coords['screen_y'],
                               offset_range=10, description=task_name)
        time.sleep(1.5)
        
        # 尝试点击领取按钮
        claim_btn = coords.get('claim_button', {})
        move_click_with_offset(controller, claim_btn['screen_x'], claim_btn['screen_y'],
                               offset_range=10, description="领取")
        time.sleep(1)
        
        # 关闭成功提示弹窗
        close_popup(controller, coords)
        time.sleep(0.5)
        
        # 如果有免费领取选项，再领一次
        claim_free = coords.get('claim_free_button', {})
        move_click_with_offset(controller, claim_free['screen_x'], claim_free['screen_y'],
                               offset_range=10, description="免费领取")
        time.sleep(1)
        
        # 关闭成功提示弹窗
        close_popup(controller, coords)
        time.sleep(0.5)
    
    # ========== 步骤4：返回主界面 ==========
    print("\n[步骤4] 返回主界面...", flush=True)
    back = coords.get('back_button', {})
    move_click_with_offset(controller, back['screen_x'], back['screen_y'],
                           offset_range=30, description="返回按钮")
    time.sleep(1)
    
    # 再返回一次确保回到主界面
    move_click_with_offset(controller, back['screen_x'], back['screen_y'],
                           offset_range=30, description="返回按钮")
    
    # 停止ESC监听
    stop_listening()
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！", flush=True)
    print("=" * 50, flush=True)
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='部落任务')
    parser.add_argument('--auto-focus', action='store_true', help='尝试自动聚焦窗口')
    
    args = parser.parse_args()
    
    try:
        run_tribe_task()
    except KeyboardInterrupt:
        print("\n[⚠️] 任务被用户中止", flush=True)
        stop_listening()
    except Exception as e:
        print(f"\n[❌] 任务出错: {e}", flush=True)
        stop_listening()
