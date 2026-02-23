#!/usr/bin/env python3
"""
任务：领取更多
包含三部分：
1. 邮件领取 - 点击领取更多 → 邮件 → 领取全部 → 关闭提示 → 关闭弹窗
2. 好友收送 - 点击领取更多 → 好友 → 一键收送 → 关闭提示 → 关闭弹窗
3. 杂货铺宝箱 - 第一个宝箱（每日限领1次），第二、三、四宝箱按2→3→4顺序循环3轮
"""

import sys
import json
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mouse_controller import MouseController
from window_focus_listener import start_listening, stop_listening, check_focus_lost


DEFAULT_CONFIG = {
    "claim_more_button": {
        "screen_x": 1250,
        "screen_y": 1450,
        "size": [60, 40],
        "description": "领取更多按钮 - 60x40矩形，中心(1250,1450)"
    },
    "mail_tab": {
        "screen_x": 770,
        "screen_y": 550,
        "description": "邮件标签页 - 中心(770, 550)"
    },
    "claim_all_button": {
        "screen_x": 960,
        "screen_y": 1200,
        "size": [180, 80],
        "description": "领取全部按钮 - 中心(960, 1200)"
    },
    "friend_tab": {
        "screen_x": 1050,
        "screen_y": 550,
        "description": "好友标签页 - 中心(1050, 550)"
    },
    "one_click_button": {
        "screen_x": 960,
        "screen_y": 1050,
        "size": [200, 70],
        "description": "一键收送按钮 - 中心(960, 1050)"
    },
    "shop_tab": {
        "screen_x": 1350,
        "screen_y": 550,
        "description": "杂货铺标签页 - 中心(1350, 550)"
    },
    "treasure_box_1": {
        "screen_x": 750,
        "screen_y": 700,
        "description": "第一个宝箱 - 中心(750, 700)，每日限领1次"
    },
    "treasure_box_2": {
        "screen_x": 960,
        "screen_y": 700,
        "description": "第二个宝箱 - 中心(960, 700)"
    },
    "treasure_box_3": {
        "screen_x": 1170,
        "screen_y": 700,
        "description": "第三个宝箱 - 中心(1170, 700)"
    },
    "treasure_box_4": {
        "screen_x": 1380,
        "screen_y": 700,
        "description": "第四个宝箱 - 中心(1380, 700)"
    },
    "close_popup_low": {
        "x_range": [630, 1290],
        "y_range": [325, 600],
        "description": "关闭弹窗 - 点击Y<600区域"
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
    # 检查焦点是否丢失
    if check_focus_lost():
        print("\n[!] 检测到窗口失去焦点，任务中止", flush=True)
        stop_listening()
        return None, None
    
    offset_x = random.randint(-offset_range, offset_range)
    offset_y = random.randint(-offset_range, offset_range)
    target_x = x + offset_x
    target_y = y + offset_y
    
    if description:
        print(f"  {description}: 中心({x}, {y}) → 实际({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    return target_x, target_y


def close_popup(controller: MouseController, coords: dict, zone: str = "high"):
    """关闭弹窗 - 点击弹窗外区域"""
    # 检查焦点是否丢失
    if check_focus_lost():
        print("\n[!] 检测到窗口失去焦点，任务中止", flush=True)
        stop_listening()
        return
    
    close_popup = coords.get('close_popup', {})
    if zone == "low":
        x_range = close_popup.get('x_range', [630, 1290])
        y_range = [325, 600]
    else:
        x_range = close_popup.get('x_range', [630, 1290])
        y_options = close_popup.get('y_options', [[325, 695], [1070, 1520]])
        y_zone = random.choice(y_options)
        y_range = y_zone
    
    close_x = random.randint(x_range[0], x_range[1])
    close_y = random.randint(y_range[0], y_range[1])
    
    print(f"  关闭弹窗: ({close_x}, {close_y})", flush=True)
    controller.move_and_click(close_x, close_y)


def run_claim_more_task() -> bool:
    """执行领取更多任务"""
    print("=" * 50, flush=True)
    print("任务：领取更多", flush=True)
    print("=" * 50, flush=True)
    
    # 聚焦到游戏窗口
    print("\n[步骤] 请在3秒内切换到游戏窗口！", flush=True)
    print("[提示] 任务开始后，如需中止请切换到其他窗口", flush=True)
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
    
    # ========== 第一部分：邮件领取（不使用焦点检测）==========
    print("\n" + "=" * 30, flush=True)
    print("【第一部分】邮件领取", flush=True)
    print("=" * 30, flush=True)
    
    # 点击"领取更多"按钮
    claim_more = coords.get('claim_more_button', {})
    move_click_with_offset(controller, claim_more['screen_x'], claim_more['screen_y'],
                           offset_range=30, description="领取更多按钮")
    time.sleep(1.5)
    
    # 点击"邮件"标签页
    mail_tab = coords.get('mail_tab', {})
    move_click_with_offset(controller, mail_tab['screen_x'], mail_tab['screen_y'],
                           offset_range=10, description="邮件标签")
    time.sleep(1)
    
    # 点击"领取全部"按钮
    claim_all = coords.get('claim_all_button', {})
    move_click_with_offset(controller, claim_all['screen_x'], claim_all['screen_y'],
                           offset_range=10, description="领取全部")
    time.sleep(1.5)
    
    # 关闭提示弹窗
    close_popup(controller, coords, zone="low")
    time.sleep(0.8)
    
    # 关闭邮件弹窗
    close_popup(controller, coords, zone="high")
    time.sleep(0.5)
    
    # 邮件领取完成后，启动焦点监听（后续步骤将检测焦点）
    print("\n[焦点检测] 启用窗口焦点检测，切换窗口将中止任务", flush=True)
    start_listening()
    
    # ========== 第二部分：好友收送 ==========
    print("\n" + "=" * 30, flush=True)
    print("【第二部分】好友收送", flush=True)
    print("=" * 30, flush=True)
    
    # 重新点击"领取更多"按钮
    move_click_with_offset(controller, claim_more['screen_x'], claim_more['screen_y'],
                           offset_range=30, description="领取更多按钮")
    time.sleep(1.5)
    
    # 点击"好友"标签页
    friend_tab = coords.get('friend_tab', {})
    move_click_with_offset(controller, friend_tab['screen_x'], friend_tab['screen_y'],
                           offset_range=10, description="好友标签")
    time.sleep(1)
    
    # 点击"一键收送"按钮
    one_click = coords.get('one_click_button', {})
    move_click_with_offset(controller, one_click['screen_x'], one_click['screen_y'],
                           offset_range=10, description="一键收送")
    time.sleep(1.5)
    
    # 关闭提示弹窗
    close_popup(controller, coords, zone="low")
    time.sleep(0.8)
    
    # 关闭好友弹窗
    close_popup(controller, coords, zone="high")
    time.sleep(0.5)
    
    # ========== 第三部分：杂货铺宝箱 ==========
    print("\n" + "=" * 30, flush=True)
    print("【第三部分】杂货铺宝箱", flush=True)
    print("=" * 30, flush=True)
    
    # 重新点击"领取更多"按钮
    move_click_with_offset(controller, claim_more['screen_x'], claim_more['screen_y'],
                           offset_range=30, description="领取更多按钮")
    time.sleep(1.5)
    
    # 点击"杂货铺"标签页
    shop_tab = coords.get('shop_tab', {})
    move_click_with_offset(controller, shop_tab['screen_x'], shop_tab['screen_y'],
                           offset_range=10, description="杂货铺标签")
    time.sleep(1)
    
    # 第一个宝箱（每日限领1次）
    box_1 = coords.get('treasure_box_1', {})
    move_click_with_offset(controller, box_1['screen_x'], box_1['screen_y'],
                           offset_range=10, description="第一个宝箱(每日)")
    time.sleep(1.5)
    close_popup(controller, coords, zone="low")
    time.sleep(1)
    
    # 第二、三、四宝箱按 2→3→4 顺序循环3轮
    boxes = [
        coords.get('treasure_box_2', {}),
        coords.get('treasure_box_3', {}),
        coords.get('treasure_box_4', {})
    ]
    
    for round_num in range(1, 4):
        print(f"\n  --- 第{round_num}轮 ---", flush=True)
        
        for i, box in enumerate(boxes, start=2):
            move_click_with_offset(controller, box['screen_x'], box['screen_y'],
                                   offset_range=10, description=f"宝箱{i}")
            time.sleep(1.5)
            close_popup(controller, coords, zone="low")
            time.sleep(0.5)
        
        if round_num < 3:
            time.sleep(2)  # 轮次间隔
    
    # 返回主界面
    print("\n[返回] 返回主界面...", flush=True)
    back = coords.get('back_button', {})
    move_click_with_offset(controller, back['screen_x'], back['screen_y'],
                           offset_range=30, description="返回按钮")
    
    # 停止焦点监听
    stop_listening()
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！", flush=True)
    print("=" * 50, flush=True)
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='领取更多任务')
    parser.add_argument('--auto-focus', action='store_true', help='尝试自动聚焦窗口')
    
    args = parser.parse_args()
    
    try:
        run_claim_more_task()
    except Exception as e:
        print(f"\n[!] 任务出错: {e}", flush=True)
        stop_listening()
