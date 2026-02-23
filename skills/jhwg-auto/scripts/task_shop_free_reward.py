#!/usr/bin/env python3
"""
任务：领取商店免费福利
点击商店按钮 -> 领取免费福利 -> 领取英雄礼包 -> 返回主界面
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


def run_shop_free_reward_task() -> bool:
    """
    执行领取商店免费福利任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：领取商店免费福利", flush=True)
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
        
        # 步骤4：点击商店按钮
        shop_btn = coords.get('shop_button', {})
        shop_x = shop_btn.get('screen_x', 690)
        shop_y = shop_btn.get('screen_y', 530)
        shop_radius = shop_btn.get('radius', 40)
        
        print("\n[步骤4] 点击商店按钮...", flush=True)
        
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
        
        # 步骤8：关闭领取成功提示窗（在Y>1360的位置点击）
        print("\n[步骤8] 关闭领取成功提示窗...", flush=True)
        # 在屏幕下方Y>1360的随机位置点击
        target_x = random.randint(800, 1200)
        target_y = random.randint(1380, 1450)
        
        print(f"点击位置: ({target_x}, {target_y}) [Y>1360区域]", flush=True)
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭领取成功提示窗", flush=True)
        time.sleep(1)
        
        # 步骤9：点击英雄礼包按钮
        print("\n[步骤9] 点击英雄礼包按钮...", flush=True)
        hero_gift_x = 925
        hero_gift_y = 1455
        hero_gift_radius = 30  # 直径60，半径30
        
        offset_x = random.randint(-int(hero_gift_radius*0.7), int(hero_gift_radius*0.7))
        offset_y = random.randint(-int(hero_gift_radius*0.7), int(hero_gift_radius*0.7))
        target_x = hero_gift_x + offset_x
        target_y = hero_gift_y + offset_y
        
        print(f"英雄礼包按钮中心: ({hero_gift_x}, {hero_gift_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击英雄礼包按钮", flush=True)
        time.sleep(1.5)
        
        # 步骤10：点击选择英雄按钮
        print("\n[步骤10] 点击选择英雄按钮...", flush=True)
        select_hero_x = 1185
        select_hero_y = 585
        # 150x60的长方形，中心(1185,585)，范围：x:1110-1260, y:555-615
        
        offset_x = random.randint(-60, 60)
        offset_y = random.randint(-25, 25)
        target_x = select_hero_x + offset_x
        target_y = select_hero_y + offset_y
        
        print(f"选择英雄按钮中心: ({select_hero_x}, {select_hero_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击选择英雄按钮", flush=True)
        time.sleep(1.5)
        
        # 步骤10.5：关闭提示框
        print("\n[步骤10.5] 关闭提示框...", flush=True)
        time.sleep(0.5)
        import pyautogui
        pyautogui.click()
        print("[OK] 已关闭提示框", flush=True)
        time.sleep(0.5)
        
        # 步骤11：等待选择英雄弹窗出现，随机选择一个英雄头像
        print("\n[步骤11] 选择英雄...", flush=True)
        time.sleep(1)
        
        # 第一排和第二排的英雄中心点（共8个）
        hero_positions = [
            (750, 960), (890, 960), (1030, 960), (1170, 960),  # 第一排
            (750, 1100), (890, 1100), (1030, 1100), (1170, 1100)  # 第二排
        ]
        
        # 随机选择一个英雄
        hero_x, hero_y = random.choice(hero_positions)
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)
        target_x = hero_x + offset_x
        target_y = hero_y + offset_y
        
        print(f"英雄头像中心: ({hero_x}, {hero_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已选择英雄", flush=True)
        time.sleep(1)
        
        # 步骤12：点击确认框中的"保存"按钮
        print("\n[步骤12] 点击保存按钮...", flush=True)
        save_x = 960
        save_y = 1330
        # 160x60的按钮，中心点(960,1330)
        
        offset_x = random.randint(-30, 30)
        offset_y = random.randint(-15, 15)
        target_x = save_x + offset_x
        target_y = save_y + offset_y
        
        print(f"保存按钮中心: ({save_x}, {save_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击保存按钮", flush=True)
        time.sleep(1)
        
        # 步骤13：关闭成功提示框（在Y<600的位置点击）
        print("\n[步骤13] 关闭成功提示框...", flush=True)
        # 在屏幕上方Y<600的随机位置点击
        target_x = random.randint(900, 1100)
        target_y = random.randint(500, 590)
        
        print(f"点击位置: ({target_x}, {target_y}) [Y<600区域]", flush=True)
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭成功提示框", flush=True)
        time.sleep(1)
        
        # 步骤14：关闭选择英雄弹窗（点击小叉，右上方20x20）
        print("\n[步骤14] 关闭选择英雄弹窗...", flush=True)
        close_x = 1230
        close_y = 510
        # 20x20的小正方形，给一个小的偏移范围 ±8
        
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        target_x = close_x + offset_x
        target_y = close_y + offset_y
        
        print(f"关闭按钮中心: ({close_x}, {close_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭选择英雄弹窗", flush=True)
        time.sleep(1)
        
        # 步骤15：返回主界面
        print("\n[步骤15] 返回主界面...", flush=True)
        back_btn = coords.get('shop_back_button', {})
        back_x = back_btn.get('screen_x', 680)
        back_y = back_btn.get('screen_y', 1455)
        back_radius = back_btn.get('radius', 30)
        
        offset_x = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        offset_y = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        target_x = back_x + offset_x
        target_y = back_y + offset_y
        
        print(f"返回按钮中心: ({back_x}, {back_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已返回主界面", flush=True)
    
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
    run_shop_free_reward_task()
