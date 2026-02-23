#!/usr/bin/env python3
"""
任务：杂货铺宝箱 - 领取杂货铺的4个宝箱（每个重复3轮）
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


def click_more_button(controller):
    """点击领取更多按钮"""
    print("\n[步骤] 点击领取更多按钮...", flush=True)
    more_x = 1258
    more_y = 1440
    more_radius = 25
    
    offset_x = random.randint(-int(more_radius*0.7), int(more_radius*0.7))
    offset_y = random.randint(-int(more_radius*0.7), int(more_radius*0.7))
    target_x = more_x + offset_x
    target_y = more_y + offset_y
    
    print(f"领取更多按钮中心: ({more_x}, {more_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击领取更多按钮", flush=True)
    
    print("\n[步骤] 等待菜单条弹出...", flush=True)
    time.sleep(1.5)


def close_notification(controller, step_num):
    """关闭通知提示框（Y<600区域）"""
    print(f"\n[步骤{step_num}] 关闭通知提示框...", flush=True)
    close_x = random.randint(800, 1200)
    close_y = random.randint(450, 590)
    
    print(f"关闭提示点击位置: ({close_x}, {close_y}) [Y<600区域]", flush=True)
    controller.move_and_click(close_x, close_y)
    print("[OK] 已关闭通知提示框", flush=True)


def run_grocery_shop_task() -> bool:
    """执行杂货铺宝箱任务"""
    print("=" * 50, flush=True)
    print("任务：杂货铺宝箱 - 4个宝箱，每个3轮", flush=True)
    print("=" * 50, flush=True)
    
    # 启动键盘监听器
    keyboard_listener = start_keyboard_listener()
    
    try:
        # 步骤1：聚焦到游戏窗口
        print("\n[步骤1] 聚焦到游戏窗口...", flush=True)
        print("请在3秒内切换到游戏窗口！", flush=True)
        print("[💡 提示: 按Esc键可随时终止任务]", flush=True)
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
        
        # 点击更多按钮
        click_more_button(controller)
        
        # 步骤4：点击杂货铺按钮
        print("\n[步骤4] 点击杂货铺按钮...", flush=True)
        shop_x = 1140
        shop_y = 1070
        shop_radius = 25
        
        offset_x = random.randint(-int(shop_radius*0.7), int(shop_radius*0.7))
        offset_y = random.randint(-int(shop_radius*0.7), int(shop_radius*0.7))
        target_x = shop_x + offset_x
        target_y = shop_y + offset_y
        
        print(f"杂货铺按钮中心: ({shop_x}, {shop_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击杂货铺按钮", flush=True)
        
        # 步骤5：等待杂货铺页面
        print("\n[步骤5] 等待杂货铺页面...", flush=True)
        time.sleep(2)
        
        # 步骤6-9：第一个宝箱（免费1）
        print("\n" + "=" * 40, flush=True)
        print("【第一个宝箱（免费1）】", flush=True)
        print("=" * 40, flush=True)
        
        print("\n[步骤6] 点击免费1按钮...", flush=True)
        free1_x = 730
        free1_y = 880
        
        offset_x = random.randint(-40, 40)
        offset_y = random.randint(-10, 10)
        target_x = free1_x + offset_x
        target_y = free1_y + offset_y
        
        print(f"免费1按钮中心: ({free1_x}, {free1_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击免费1按钮", flush=True)
        
        print("\n[步骤7] 等待领取弹框...", flush=True)
        time.sleep(1.5)
        
        print("\n[步骤8] 点击弹框中间的免费按钮...", flush=True)
        free_btn_x = 960
        free_btn_y = 1075
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-20, 20)
        target_x = free_btn_x + offset_x
        target_y = free_btn_y + offset_y
        
        print(f"免费按钮中心: ({free_btn_x}, {free_btn_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击免费按钮", flush=True)
        
        print("\n[步骤9] 等待领取完成...", flush=True)
        time.sleep(2)
        
        close_notification(controller, 10)
        
        # 第二、三、四宝箱（按2->3->4顺序循环3轮）
        boxes = [
            (2, (880, 880)),
            (3, (1040, 880)),
            (4, (1195, 880))
        ]
        
        step_num = 11
        for round_num in range(1, 4):
            print("\n" + "=" * 40, flush=True)
            print(f"【第{round_num}轮：按2->3->4顺序领取】", flush=True)
            print("=" * 40, flush=True)
            
            for box_num, box_center in boxes:
                box_x, box_y = box_center
                
                # 点击宝箱按钮
                print(f"\n[步骤{step_num}] 点击第{box_num}个宝箱（第{round_num}轮）...", flush=True)
                box_radius = 25
                offset_x = random.randint(-int(box_radius*0.7), int(box_radius*0.7))
                offset_y = random.randint(-int(box_radius*0.7), int(box_radius*0.7))
                target_x = box_x + offset_x
                target_y = box_y + offset_y
                
                print(f"宝箱按钮中心: ({box_x}, {box_y})", flush=True)
                print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
                print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
                
                controller.move_and_click(target_x, target_y)
                print(f"[OK] 已点击第{box_num}个宝箱", flush=True)
                
                # 等待领取弹窗
                print(f"\n[步骤{step_num+1}] 等待领取弹窗...", flush=True)
                time.sleep(1.5)
                
                # 点击领取按钮（确认提示框的"免费"按钮）
                print(f"\n[步骤{step_num+2}] 点击免费按钮...", flush=True)
                claim_x, claim_y = 960, 1160
                offset_x = random.randint(-70, 70)
                offset_y = random.randint(-15, 15)
                target_x = claim_x + offset_x
                target_y = claim_y + offset_y
                
                print(f"领取按钮中心: ({claim_x}, {claim_y})", flush=True)
                print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
                print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
                
                controller.move_and_click(target_x, target_y)
                print("[OK] 已点击领取按钮", flush=True)
                
                # 等待领取完成
                print(f"\n[步骤{step_num+3}] 等待领取完成...", flush=True)
                time.sleep(2)
                
                # 关闭通知提示框
                close_notification(controller, step_num+4)
                
                step_num += 5
            
            # 每轮结束后等待2秒（除了最后一轮）
            if round_num < 3:
                print(f"\n[等待] 第{round_num}轮完成，等待2秒后继续下一轮...", flush=True)
                time.sleep(2)
        
        # 步骤56：关闭杂货铺弹窗
        print("\n[步骤56] 关闭杂货铺弹窗...", flush=True)
        close_btn_x = 1240
        close_btn_y = 470
        
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        target_x = close_btn_x + offset_x
        target_y = close_btn_y + offset_y
        
        print(f"关闭按钮中心: ({close_btn_x}, {close_btn_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭杂货铺弹窗", flush=True)
        
        print("\n" + "=" * 50, flush=True)
        print("任务完成！", flush=True)
        print("=" * 50, flush=True)
        
        return True
    
    except KeyboardInterrupt:
        print("\n" + "=" * 50, flush=True)
        print("任务被用户终止！", flush=True)
        print("=" * 50, flush=True)
        return False
    
    finally:
        # 停止键盘监听器
        stop_keyboard_listener()
    
    return True


if __name__ == '__main__':
    run_grocery_shop_task()
