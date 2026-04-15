#!/usr/bin/env python3
"""
任务：竞技 - 挑战碾压对手（每日有限制次数）
点击竞技 -> 挑战 -> 碾压 -> 关闭 -> 重复3次
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


def run_arena_task() -> bool:
    """
    执行竞技挑战任务（每日有限制次数）
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：竞技 - 挑战碾压对手（3次）", flush=True)
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
        
        # 重复3次挑战
        for round_num in range(1, 4):
            print("\n" + "=" * 40, flush=True)
            print(f"【第{round_num}次挑战】", flush=True)
            print("=" * 40, flush=True)
            
            # 第1次挑战需要点击竞技按钮进入，后续挑战只需点击挑战按钮
            if round_num == 1:
                # 步骤4：点击竞技按钮
                print("\n[步骤4] 点击竞技按钮...", flush=True)
                arena_x = 690
                arena_y = 1120
                arena_radius = 40
                
                offset_x = random.randint(-int(arena_radius*0.7), int(arena_radius*0.7))
                offset_y = random.randint(-int(arena_radius*0.7), int(arena_radius*0.7))
                target_x = arena_x + offset_x
                target_y = arena_y + offset_y
                
                print(f"竞技按钮中心: ({arena_x}, {arena_y})", flush=True)
                print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
                print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
                
                controller.move_and_click(target_x, target_y)
                print("[OK] 已点击竞技按钮", flush=True)
                
                # 步骤5：等待竞技弹窗
                print("\n[步骤5] 等待竞技弹窗...", flush=True)
                time.sleep(2)
            
            # 步骤6/第N次：点击挑战按钮
            step_num = 6 if round_num == 1 else (6 + (round_num - 1) * 4)
            print(f"\n[步骤{step_num}] 点击挑战按钮...", flush=True)
            challenge_x = 960
            challenge_y = 1320
            
            offset_x = random.randint(-80, 80)  # 160宽度，一半是80
            offset_y = random.randint(-30, 30)  # 60高度，一半是30
            target_x = challenge_x + offset_x
            target_y = challenge_y + offset_y
            
            print(f"挑战按钮中心: ({challenge_x}, {challenge_y})", flush=True)
            print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
            print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
            
            controller.move_and_click(target_x, target_y)
            print("[OK] 已点击挑战按钮", flush=True)
            
            # 步骤7/第N+1次：等待碾压界面
            wait_step = step_num + 1
            print(f"\n[步骤{wait_step}] 等待碾压界面...", flush=True)
            time.sleep(2)
            
            # 步骤8/第N+2次：点击碾压按钮（Y浮动控制在2以内）
            click_step = wait_step + 1
            print(f"\n[步骤{click_step}] 点击碾压按钮...", flush=True)
            crush_x = 1167
            crush_y = 1392
            
            # Y浮动控制在2以内
            offset_x = random.randint(-50, 50)  # 100宽度，一半是50
            offset_y = random.randint(-2, 2)   # Y浮动控制在2以内
            target_x = crush_x + offset_x
            target_y = crush_y + offset_y
            
            print(f"碾压按钮中心: ({crush_x}, {crush_y})", flush=True)
            print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
            print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
            
            controller.move_and_click(target_x, target_y)
            print("[OK] 已点击碾压按钮", flush=True)
            
            # 步骤9/第N+3次：等待0.5秒，在原位置点击关闭提示框
            close_step = click_step + 1
            print(f"\n[步骤{close_step}] 等待0.5秒后关闭提示框...", flush=True)
            time.sleep(0.5)
            
            # 在原位置点击关闭（不移动鼠标）
            close_x = target_x + random.randint(-30, 30)
            close_y = target_y + random.randint(10, 30)
            
            print(f"关闭提示点击位置: ({close_x}, {close_y}) [原位置附近]", flush=True)
            controller.move_and_click(close_x, close_y)
            print("[OK] 已关闭成功提示框", flush=True)
            
            # 每次挑战后等待1秒
            if round_num < 3:
                print(f"\n[等待] 第{round_num}次完成，等待1秒后继续...", flush=True)
                time.sleep(1)
        
        # 步骤最后：点击返回按钮回到主界面
        print("\n[步骤最后] 点击返回按钮...", flush=True)
        return_x = 690
        return_y = 1450
        return_radius = 30
        
        offset_x = random.randint(-int(return_radius*0.7), int(return_radius*0.7))
        offset_y = random.randint(-int(return_radius*0.7), int(return_radius*0.7))
        target_x = return_x + offset_x
        target_y = return_y + offset_y
        
        print(f"返回按钮中心: ({return_x}, {return_y})", flush=True)
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
    run_arena_task()
