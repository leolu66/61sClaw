#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务：领取终生卡奖励
点击畅玩卡按钮 -> 点击终身卡 -> 领取奖励 -> 返回主界面
支持 Esc 键终止任务
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


def run_lifetime_card_task() -> bool:
    """
    执行领取终生卡奖励任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：领取终生卡奖励", flush=True)
    print("=" * 50, flush=True)
    
    # 启动键盘监听器
    keyboard_listener = start_keyboard_listener()
    
    try:
        # 步骤 1：聚焦到游戏窗口
        print("\n[步骤 1] 聚焦到游戏窗口...", flush=True)
        print("请在 3 秒内切换到游戏窗口！", flush=True)
        print("[💡 提示：按 Esc 键可随时终止任务]", flush=True)
        time.sleep(3)
        
        # 步骤 2：初始化鼠标控制器
        print("\n[步骤 2] 初始化鼠标控制器...", flush=True)
        config_path = Path(__file__).parent / "config.json"
        mouse_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mouse_config = json.load(f).get('settings', {})
        
        controller = MouseController(mouse_config)
        
        # 步骤 3：加载坐标配置
        print("\n[步骤 3] 加载坐标配置...", flush=True)
        coords = load_config()
        
        # 步骤 4：点击畅玩卡按钮
        playcard_btn = coords.get('playcard_button', {})
        playcard_x = playcard_btn.get('screen_x', 730)
        playcard_y = playcard_btn.get('screen_y', 590)
        playcard_radius = playcard_btn.get('radius', 30)
        
        print("\n[步骤 4] 点击畅玩卡按钮...", flush=True)
        
        offset_x = random.randint(-int(playcard_radius*0.7), int(playcard_radius*0.7))
        offset_y = random.randint(-int(playcard_radius*0.7), int(playcard_radius*0.7))
        target_x = playcard_x + offset_x
        target_y = playcard_y + offset_y
        
        print(f"畅玩卡按钮中心：({playcard_x}, {playcard_y})", flush=True)
        print(f"随机偏移：({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置：({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击畅玩卡按钮", flush=True)
        
        # 步骤 5：等待畅玩卡弹窗
        print("\n[步骤 5] 等待畅玩卡弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤 6：点击终身卡按钮
        lifetime_btn = coords.get('lifetime_card_button', {})
        lifetime_x = lifetime_btn.get('screen_x', 1200)
        lifetime_y = lifetime_btn.get('screen_y', 1300)
        lifetime_radius = lifetime_btn.get('radius', 30)
        
        print("\n[步骤 6] 点击终身卡按钮...", flush=True)
        
        offset_x = random.randint(-int(lifetime_radius*0.7), int(lifetime_radius*0.7))
        offset_y = random.randint(-int(lifetime_radius*0.7), int(lifetime_radius*0.7))
        target_x = lifetime_x + offset_x
        target_y = lifetime_y + offset_y
        
        print(f"终身卡按钮中心：({lifetime_x}, {lifetime_y})", flush=True)
        print(f"随机偏移：({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置：({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击终身卡按钮", flush=True)
        
        # 步骤 7：等待切换到终身卡页面
        print("\n[步骤 7] 等待切换到终身卡页面...", flush=True)
        time.sleep(2.5)
        print("[OK] 等待完成，继续执行", flush=True)
        
        # 步骤 8：点击领取按钮
        claim_btn = coords.get('lifetime_claim_button', {})
        claim_x = claim_btn.get('screen_x', 960)
        claim_y = claim_btn.get('screen_y', 1220)
        
        print("\n[步骤 8] 点击领取按钮...", flush=True)
        print(f"当前鼠标位置：{controller.get_position()}", flush=True)
        
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = claim_x + offset_x
        target_y = claim_y + offset_y
        
        print(f"领取按钮中心：({claim_x}, {claim_y})", flush=True)
        print(f"随机偏移：({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置：({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击领取按钮", flush=True)
        
        # 步骤 9：关闭成功领取提示框（在领取按钮位置点击）
        print("\n[步骤 9] 关闭成功领取提示框...", flush=True)
        time.sleep(0.5)  # 等待 0.5 秒
        
        # 在领取按钮位置附近点击关闭（向下偏移小范围）
        close_offset_x = random.randint(-10, 10)
        close_offset_y = random.randint(5, 20)  # 向下偏移 5-20 像素
        close_x = claim_x + close_offset_x
        close_y = claim_y + close_offset_y
        
        print(f"关闭弹窗点击位置：({close_x}, {close_y})", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭成功领取提示框", flush=True)
        time.sleep(0.5)
        
        # 步骤 9.5：再次点击当前位置关闭第二个提示框
        print("\n[步骤 9.5] 关闭第二个提示框...", flush=True)
        print(f"再次点击位置：({close_x}, {close_y})", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭第二个提示框", flush=True)
        time.sleep(0.5)
        
        # 步骤 10：点击返回按钮
        back_btn = coords.get('lifetime_back_button', {})
        back_x = 720
        back_y = 1300
        back_radius = 30  # 60x60 圆形
        
        print("\n[步骤 10] 点击返回按钮...", flush=True)
        
        offset_x = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        offset_y = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        target_x = back_x + offset_x
        target_y = back_y + offset_y
        
        print(f"返回按钮中心：({back_x}, {back_y})", flush=True)
        print(f"随机偏移：({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置：({target_x}, {target_y})", flush=True)
        
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
    run_lifetime_card_task()
