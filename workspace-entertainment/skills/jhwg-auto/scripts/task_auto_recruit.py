#!/usr/bin/env python3
"""
任务：自动招募
点击招募按钮 -> 普通招募 -> 领取2次 -> 确认 -> 返回主界面
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


def click_claim_and_confirm(controller, claim_x, claim_y, confirm_x, confirm_y, round_num):
    """
    执行领取和确认的通用函数
    
    Args:
        controller: 鼠标控制器
        claim_x, claim_y: 领取按钮坐标
        confirm_x, confirm_y: 确认按钮坐标
        round_num: 第几次领取
    """
    # 点击领取按钮
    print(f"\n[步骤] 点击领取按钮（第{round_num}次）...", flush=True)
    offset_x = random.randint(-70, 70)
    offset_y = random.randint(-30, 30)
    target_x = claim_x + offset_x
    target_y = claim_y + offset_y
    
    print(f"领取按钮中心: ({claim_x}, {claim_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print(f"[OK] 已点击领取按钮（第{round_num}次）", flush=True)
    
    # 等待确认页面
    print("\n[步骤] 等待确认页面...", flush=True)
    time.sleep(1.5)
    
    # 点击确认按钮
    print("\n[步骤] 点击确认按钮...", flush=True)
    offset_x = random.randint(-70, 70)
    offset_y = random.randint(-30, 30)
    target_x = confirm_x + offset_x
    target_y = confirm_y + offset_y
    
    print(f"确认按钮中心: ({confirm_x}, {confirm_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击确认按钮", flush=True)
    
    # 等待领取完成
    print("\n[步骤] 等待领取完成...", flush=True)
    time.sleep(3.5)


def run_auto_recruit_task() -> bool:
    """
    执行自动招募任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：自动招募", flush=True)
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
        
        # 步骤4：点击招募按钮
        print("\n[步骤4] 点击招募按钮...", flush=True)
        recruit_x = 685
        recruit_y = 1435
        recruit_radius = 35
        
        offset_x = random.randint(-int(recruit_radius*0.7), int(recruit_radius*0.7))
        offset_y = random.randint(-int(recruit_radius*0.7), int(recruit_radius*0.7))
        target_x = recruit_x + offset_x
        target_y = recruit_y + offset_y
        
        print(f"招募按钮中心: ({recruit_x}, {recruit_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击招募按钮", flush=True)
        
        # 步骤5：等待招募弹窗
        print("\n[步骤5] 等待招募弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤6：点击普通招募按钮
        print("\n[步骤6] 点击普通招募按钮...", flush=True)
        normal_recruit_x = 820
        normal_recruit_y = 1330
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-30, 30)
        target_x = normal_recruit_x + offset_x
        target_y = normal_recruit_y + offset_y
        
        print(f"普通招募按钮中心: ({normal_recruit_x}, {normal_recruit_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击普通招募按钮", flush=True)
        
        # 步骤7：等待普通招募页签打开
        print("\n[步骤7] 等待普通招募页签打开...", flush=True)
        time.sleep(2)
        
        # 坐标定义
        claim_x = 960
        claim_y = 1170
        confirm_x = 960
        confirm_y = 1420
        
        # 第一次领取
        click_claim_and_confirm(controller, claim_x, claim_y, confirm_x, confirm_y, 1)
        
        # 第二次领取
        click_claim_and_confirm(controller, claim_x, claim_y, confirm_x, confirm_y, 2)
        
        # 步骤8：点击返回按钮
        print("\n[步骤8] 点击返回按钮...", flush=True)
        back_x = 680
        back_y = 1455
        back_radius = 30
        
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
    run_auto_recruit_task()
