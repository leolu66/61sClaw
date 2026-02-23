#!/usr/bin/env python3
"""
任务：领取更多 - 邮件领取 + 好友收送 + 杂货铺领取（4个宝箱，每个重复3次）
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
from keyboard_listener import start_keyboard_listener, stop_keyboard_listener, check_esc_key


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


def claim_shop_box(controller, box_center, box_num, claim_center, step_base):
    """
    领取杂货铺宝箱（可重复3次）
    
    Args:
        controller: 鼠标控制器
        box_center: 宝箱按钮中心坐标 (x, y)
        box_num: 宝箱编号
        claim_center: 领取按钮中心坐标 (x, y)
        step_base: 步骤编号基数
    """
    box_x, box_y = box_center
    claim_x, claim_y = claim_center
    
    # 每个宝箱领取3次，间隔5秒
    for round_num in range(1, 4):
        print(f"\n[步骤{step_base + (round_num-1)*4}] 点击第{box_num}个宝箱（第{round_num}次）...", flush=True)
        
        # 点击宝箱按钮
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
        print(f"\n[步骤{step_base + (round_num-1)*4 + 1}] 等待领取弹窗...", flush=True)
        time.sleep(1.5)
        
        # 点击领取按钮
        print(f"\n[步骤{step_base + (round_num-1)*4 + 2}] 点击领取按钮...", flush=True)
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
        print(f"\n[步骤{step_base + (round_num-1)*4 + 3}] 等待领取完成...", flush=True)
        time.sleep(2)
        
        # 关闭通知提示框
        close_notification(controller, step_base + (round_num-1)*4 + 4)
        
        # 如果不是最后一次，等待5秒再领
        if round_num < 3:
            print(f"\n[等待] 等待5秒后再次领取...", flush=True)
            time.sleep(5)


def run_claim_more_task() -> bool:
    """执行领取更多任务"""
    print("=" * 50, flush=True)
    print("任务：领取更多 - 邮件领取 + 好友收送 + 杂货铺", flush=True)
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
        coords = load_config()
        
        # ========== 第一部分：邮件领取 ==========
        print("\n" + "-" * 50, flush=True)
        print("【第一部分：邮件领取】", flush=True)
        print("-" * 50, flush=True)
        
        click_more_button(controller)
        
        # 步骤5：点击邮件按钮
        print("\n[步骤5] 点击邮件按钮...", flush=True)
        mail_x = 1140
        mail_y = 840
        mail_radius = 25
        
        offset_x = random.randint(-int(mail_radius*0.7), int(mail_radius*0.7))
        offset_y = random.randint(-int(mail_radius*0.7), int(mail_radius*0.7))
        target_x = mail_x + offset_x
        target_y = mail_y + offset_y
        
        print(f"邮件按钮中心: ({mail_x}, {mail_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击邮件按钮", flush=True)
        
        # 步骤6：等待邮件弹窗
        print("\n[步骤6] 等待邮件弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤7：点击领取全部按钮
        print("\n[步骤7] 点击领取全部按钮...", flush=True)
        claim_all_x = 1090
        claim_all_y = 1365
        
        offset_x = random.randint(-70, 70)
        offset_y = random.randint(-20, 20)
        target_x = claim_all_x + offset_x
        target_y = claim_all_y + offset_y
        
        print(f"领取全部按钮中心: ({claim_all_x}, {claim_all_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击领取全部按钮", flush=True)
        
        # 步骤8：等待领取完成
        print("\n[步骤8] 等待领取完成...", flush=True)
        time.sleep(2)
        
        # 步骤9：关闭成功提示框
        print("\n[步骤9] 关闭成功提示框...", flush=True)
        close_x = random.randint(800, 1200)
        close_y = random.randint(1120, 1450)
        
        print(f"关闭提示点击位置: ({close_x}, {close_y}) [Y>1100区域]", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭成功提示框", flush=True)
        
        # 步骤10：关闭邮件弹窗
        print("\n[步骤10] 关闭邮件弹窗...", flush=True)
        close_btn_x = 1235
        close_btn_y = 470
        
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        target_x = close_btn_x + offset_x
        target_y = close_btn_y + offset_y
        
        print(f"关闭按钮中心: ({close_btn_x}, {close_btn_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭邮件弹窗", flush=True)
        
        # ========== 第二部分：好友收送 ==========
        print("\n" + "-" * 50, flush=True)
        print("【第二部分：好友收送】", flush=True)
        print("-" * 50, flush=True)
        
        click_more_button(controller)
        
        # 步骤12：点击好友按钮
        print("\n[步骤12] 点击好友按钮...", flush=True)
        friend_x = 1140
        friend_y = 1300
        friend_radius = 25
        
        offset_x = random.randint(-int(friend_radius*0.7), int(friend_radius*0.7))
        offset_y = random.randint(-int(friend_radius*0.7), int(friend_radius*0.7))
        target_x = friend_x + offset_x
        target_y = friend_y + offset_y
        
        print(f"好友按钮中心: ({friend_x}, {friend_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击好友按钮", flush=True)
        
        # 步骤13：等待好友弹窗
        print("\n[步骤13] 等待好友弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤14：点击一键收送按钮
        print("\n[步骤14] 点击一键收送按钮...", flush=True)
        one_click_x = 1175
        one_click_y = 1260
        
        offset_x = random.randint(-50, 50)
        offset_y = random.randint(-15, 15)
        target_x = one_click_x + offset_x
        target_y = one_click_y + offset_y
        
        print(f"一键收送按钮中心: ({one_click_x}, {one_click_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击一键收送按钮", flush=True)
        
        # 步骤15：等待收送完成
        print("\n[步骤15] 等待收送完成...", flush=True)
        time.sleep(2)
        
        # 步骤16：关闭领取成功提示框
        print("\n[步骤16] 关闭领取成功提示框...", flush=True)
        close_x = random.randint(800, 1200)
        close_y = random.randint(350, 490)
        
        print(f"关闭提示点击位置: ({close_x}, {close_y}) [Y<500区域]", flush=True)
        controller.move_and_click(close_x, close_y)
        print("[OK] 已关闭领取成功提示框", flush=True)
        
        # 步骤17：关闭好友弹窗
        print("\n[步骤17] 关闭好友弹窗...", flush=True)
        close_btn_x = 1235
        close_btn_y = 470
        
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        target_x = close_btn_x + offset_x
        target_y = close_btn_y + offset_y
        
        print(f"关闭按钮中心: ({close_btn_x}, {close_btn_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭好友弹窗", flush=True)
    
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
    run_claim_more_task()
