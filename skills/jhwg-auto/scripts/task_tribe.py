#!/usr/bin/env python3
"""
任务：部落 - 签到 + 4个子任务
点击部落按钮 -> 签到 -> 4个子任务
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


def click_tribe_task(controller, task_name, task_center, step_num):
    """
    点击部落子任务
    
    Args:
        controller: 鼠标控制器
        task_name: 任务名称
        task_center: 任务区域中心坐标 (x, y)
        step_num: 步骤编号
    """
    task_x, task_y = task_center
    
    print(f"\n[步骤{step_num}] 点击{task_name}...", flush=True)
    offset_x = random.randint(-200, 200)
    offset_y = random.randint(-70, 70)
    target_x = task_x + offset_x
    target_y = task_y + offset_y
    
    print(f"{task_name}中心: ({task_x}, {task_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print(f"[OK] 已点击{task_name}", flush=True)
    
    print(f"\n[步骤{step_num+1}] 等待响应...", flush=True)
    time.sleep(2)


def run_tribe_task() -> bool:
    """执行部落任务"""
    print("=" * 50, flush=True)
    print("任务：部落 - 签到 + 4个子任务", flush=True)
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
        
        # 步骤4：点击部落按钮
        print("\n[步骤4] 点击部落按钮...", flush=True)
        tribe_x = 900
        tribe_y = 1430
        tribe_radius = 18
        
        offset_x = random.randint(-int(tribe_radius*0.7), int(tribe_radius*0.7))
        offset_y = random.randint(-int(tribe_radius*0.7), int(tribe_radius*0.7))
        target_x = tribe_x + offset_x
        target_y = tribe_y + offset_y
        
        print(f"部落按钮中心: ({tribe_x}, {tribe_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击部落按钮", flush=True)
        
        # 步骤5：等待部落弹窗
        print("\n[步骤5] 等待部落弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤6：点击签到按钮
        print("\n[步骤6] 点击签到按钮...", flush=True)
        checkin_x = 970
        checkin_y = 620
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-30, 30)
        target_x = checkin_x + offset_x
        target_y = checkin_y + offset_y
        
        print(f"签到按钮中心: ({checkin_x}, {checkin_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击签到按钮", flush=True)
        
        # 步骤7：等待签到弹窗
        print("\n[步骤7] 等待签到弹窗...", flush=True)
        time.sleep(1.5)
        
        # 步骤8：点击签到奖励按钮
        print("\n[步骤8] 点击签到奖励按钮...", flush=True)
        reward_x = 960
        reward_y = 1290
        
        offset_x = random.randint(-80, 80)
        offset_y = random.randint(-20, 20)
        target_x = reward_x + offset_x
        target_y = reward_y + offset_y
        
        print(f"签到奖励按钮中心: ({reward_x}, {reward_y}) [180x60长方形]", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击签到奖励按钮", flush=True)
        
        # 步骤9：等待居中提示框
        print("\n[步骤9] 等待居中提示框...", flush=True)
        time.sleep(1.5)
        
        # 步骤10：关闭居中提示框（Y<500区域）
        print("\n[步骤10] 关闭居中提示框...", flush=True)
        close_x = random.randint(800, 1100)
        close_y = random.randint(350, 480)
        
        print(f"关闭提示框位置: ({close_x}, {close_y}) [Y<500区域]", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭居中提示框", flush=True)
        
        # 等待0.5秒后，在当前位置附近再点击一次关闭领取提示弹窗
        print("\n[步骤10.5] 关闭领取提示弹窗...", flush=True)
        time.sleep(0.5)
        close_x2 = close_x + random.randint(-20, 20)
        close_y2 = close_y + random.randint(-20, 20)
        print(f"关闭提示框位置: ({close_x2}, {close_y2})", flush=True)
        controller.move_and_click(close_x2, close_y2)
        print("[OK] 已关闭领取提示弹窗", flush=True)
        
        # 步骤11：等待关闭完成
        print("\n[步骤11] 等待关闭完成...", flush=True)
        time.sleep(1)
        
        # 步骤12：点击部落试炼
        print("\n" + "-" * 50, flush=True)
        print("【部落试炼】", flush=True)
        print("-" * 50, flush=True)
        
        print("\n[步骤12] 点击部落试炼...", flush=True)
        trial_x = 970
        trial_y = 780
        
        offset_x = random.randint(-200, 200)
        offset_y = random.randint(-70, 70)
        target_x = trial_x + offset_x
        target_y = trial_y + offset_y
        
        print(f"部落试炼中心: ({trial_x}, {trial_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击部落试炼", flush=True)
        
        # 步骤13：等待试炼弹出页面
        print("\n[步骤13] 等待试炼弹出页面...", flush=True)
        time.sleep(2)
        
        # 步骤14：点击挑战按钮
        print("\n[步骤14] 点击挑战按钮...", flush=True)
        challenge_x = 960
        challenge_y = 1450
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-20, 20)
        target_x = challenge_x + offset_x
        target_y = challenge_y + offset_y
        
        print(f"挑战按钮中心: ({challenge_x}, {challenge_y}) [160x60长方形]", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击挑战按钮", flush=True)
        
        # 步骤15：等待挑战页面弹出
        print("\n[步骤15] 等待挑战页面弹出...", flush=True)
        time.sleep(2)
        
        # 步骤16：点击开始战斗按钮
        print("\n[步骤16] 点击开始战斗按钮...", flush=True)
        battle_x = 960
        battle_y = 1450
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-20, 20)
        target_x = battle_x + offset_x
        target_y = battle_y + offset_y
        
        print(f"开始战斗按钮中心: ({battle_x}, {battle_y}) [160x60长方形]", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击开始战斗按钮", flush=True)
        
        # 步骤17：等待挑战完成（90秒）
        print("\n[步骤17] 挑战进行中，等待90秒...", flush=True)
        for i in range(90):
            if i % 10 == 0:
                print(f"  挑战进行中... {i}/90秒", flush=True)
            time.sleep(1)
        print("[OK] 挑战完成", flush=True)
        
        # 步骤18：等待挑战完成提示框
        print("\n[步骤18] 等待挑战完成提示框...", flush=True)
        time.sleep(5)  # 增加等待时间
        
        # 步骤19：点击确认按钮（160x40按钮，中心点960,1250）
        print("\n[步骤19] 点击确认按钮...", flush=True)
        confirm_x = 960
        confirm_y = 1250
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-15, 15)
        target_x = confirm_x + offset_x
        target_y = confirm_y + offset_y
        
        print(f"确认按钮中心: ({confirm_x}, {confirm_y}) [160x40长方形]", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击确认按钮", flush=True)
        
        # 步骤20：等待关闭完成
        print("\n[步骤20] 等待关闭完成...", flush=True)
        time.sleep(2)
        
        # 步骤21：点击返回按钮
        print("\n[步骤21] 点击返回按钮...", flush=True)
        back_x = 680
        back_y = 1450
        back_radius = 25
        
        offset_x = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        offset_y = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        target_x = back_x + offset_x
        target_y = back_y + offset_y
        
        print(f"返回按钮中心: ({back_x}, {back_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击返回按钮（回到部落页面）", flush=True)
        
        # 步骤22：等待页面切换
        print("\n[步骤22] 等待页面切换...", flush=True)
        time.sleep(2)
        
        # 步骤23：再次点击返回按钮（回到主页面）
        print("\n[步骤23] 再次点击返回按钮（回到主页面）...", flush=True)
        back_x = 680
        back_y = 1450
        back_radius = 25
        
        offset_x = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        offset_y = random.randint(-int(back_radius*0.7), int(back_radius*0.7))
        target_x = back_x + offset_x
        target_y = back_y + offset_y
        
        print(f"返回按钮中心: ({back_x}, {back_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击返回按钮（回到主页面）", flush=True)
    
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
    run_tribe_task()
