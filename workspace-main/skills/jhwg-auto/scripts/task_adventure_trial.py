#!/usr/bin/env python3
"""
任务：冒险 - 试炼之地
点击冒险按钮 -> 试炼之地 -> 领取5个子任务（每个2次免费）
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


def close_adventure_popup(controller):
    """关闭冒险弹窗"""
    print("\n[步骤] 关闭冒险弹窗...", flush=True)
    close_x = 1215
    close_y = 1450
    
    offset_x = random.randint(-20, 20)
    offset_y = random.randint(-12, 12)
    target_x = close_x + offset_x
    target_y = close_y + offset_y
    
    print(f"关闭按钮中心: ({close_x}, {close_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已关闭冒险弹窗", flush=True)


def claim_trial_task(controller, task_name, task_center, step_num, round_num, close_popup=True):
    """
    领取试炼之地子任务
    
    Args:
        controller: 鼠标控制器
        task_name: 任务名称
        task_center: 任务区域中心坐标 (x, y, y_range)
        step_num: 步骤编号基数
        round_num: 第几次领取
        close_popup: 是否关闭子任务弹窗（最后一次领取后关闭）
    """
    task_x, task_y = task_center[0], task_center[1]
    # 获取Y轴偏移限制，默认为70
    y_limit = task_center[2] if len(task_center) > 2 else 70
    
    # 点击任务区域
    print(f"\n[步骤{step_num}] 点击{task_name}（第{round_num}次）...", flush=True)
    offset_x = random.randint(-200, 200)
    offset_y = random.randint(-y_limit, y_limit)
    target_x = task_x + offset_x
    target_y = task_y + offset_y
    
    print(f"{task_name}中心: ({task_x}, {task_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print(f"[OK] 已点击{task_name}", flush=True)
    
    # 等待弹窗/响应
    print(f"\n[步骤{step_num+1}] 等待响应...", flush=True)
    time.sleep(2)
    
    # 检查Esc键
    if check_esc_key():
        print("\n[⚠️ 检测到Esc键，终止任务...]")
        raise KeyboardInterrupt("用户按Esc终止")
    
    # 点击领取按钮 - 统一使用 (960, 1180)
    print(f"\n[步骤{step_num+2}] 点击领取按钮...", flush=True)
    claim_x, claim_y = 960, 1180
    offset_x = random.randint(-80, 80)
    offset_y = random.randint(-20, 20)
    target_x = claim_x + offset_x
    target_y = claim_y + offset_y
    
    print(f"领取按钮中心: ({claim_x}, {claim_y}) [180x60长方形]", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击领取按钮", flush=True)
    
    # 等待领取完成
    print(f"\n[步骤{step_num+3}] 等待领取完成...", flush=True)
    time.sleep(2)
    
    # 检查Esc键
    if check_esc_key():
        print("\n[⚠️ 检测到Esc键，终止任务...]")
        raise KeyboardInterrupt("用户按Esc终止")
    
    # 步骤N+4：关闭成功提示框（在领取按钮位置附近点击）
    print(f"\n[步骤{step_num+4}] 关闭成功提示框...", flush=True)
    time.sleep(1)  # 等待1秒
    
    # 在领取按钮位置附近点击关闭
    claim_x, claim_y = 960, 1180
    close_offset_x = random.randint(-30, 30)
    close_offset_y = random.randint(-20, 20)
    close_x = claim_x + close_offset_x
    close_y = claim_y + close_offset_y
    
    print(f"关闭提示框位置: ({close_x}, {close_y})", flush=True)
    controller.move_and_click(close_x, close_y)
    print("[OK] 已关闭成功提示框", flush=True)
    
    # 等待关闭完成
    print(f"\n[步骤{step_num+5}] 等待关闭完成...", flush=True)
    time.sleep(0.5)
    
    # 检查Esc键
    if check_esc_key():
        print("\n[⚠️ 检测到Esc键，终止任务...]")
        raise KeyboardInterrupt("用户按Esc终止")
    
    # 步骤N+6：关闭子任务弹窗（右上角20x20按钮）
    # 如果是最后一次领取，则不关闭弹窗，留给 close_task_popup 处理
    if close_popup:
        print(f"\n[步骤{step_num+6}] 关闭子任务弹窗...", flush=True)
        popup_close_x = 1230
        popup_close_y = 680
        
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        target_x = popup_close_x + offset_x
        target_y = popup_close_y + offset_y
        
        print(f"子任务弹窗关闭按钮中心: ({popup_close_x}, {popup_close_y}) [20x20正方形]", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已关闭子任务弹窗", flush=True)
        
        # 等待关闭完成
        print(f"\n[步骤{step_num+7}] 等待弹窗关闭完成...", flush=True)
        time.sleep(1.5)
    else:
        # 不关闭弹窗，等待一下让界面稳定
        time.sleep(0.5)
    
    # 检查Esc键
    if check_esc_key():
        print("\n[⚠️ 检测到Esc键，终止任务...]")
        raise KeyboardInterrupt("用户按Esc终止")


def close_task_popup(controller, step_num):
    """
    关闭任务弹窗（每个任务2次领取后调用）
    
    Args:
        controller: 鼠标控制器
        step_num: 步骤编号
    """
    # 步骤N：关闭子任务弹窗（右上角20x20按钮）
    print(f"\n[步骤{step_num}] 关闭子任务弹窗...", flush=True)
    popup_close_x = 1230
    popup_close_y = 680
    
    offset_x = random.randint(-8, 8)
    offset_y = random.randint(-8, 8)
    target_x = popup_close_x + offset_x
    target_y = popup_close_y + offset_y
    
    print(f"子任务弹窗关闭按钮中心: ({popup_close_x}, {popup_close_y}) [20x20正方形]", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已关闭子任务弹窗", flush=True)
    
    # 步骤N+1：等待弹窗关闭完成
    print(f"\n[步骤{step_num+1}] 等待弹窗关闭完成...", flush=True)
    time.sleep(1.5)


def run_adventure_trial_task() -> bool:
    """执行冒险-试炼之地任务"""
    print("=" * 50, flush=True)
    print("任务：冒险 - 试炼之地", flush=True)
    print("=" * 50, flush=True)
    
    # 启动键盘监听器
    keyboard_listener = start_keyboard_listener()
    
    try:
        # 步骤1：聚焦到游戏窗口
        print("\n[步骤1] 聚焦到游戏窗口...", flush=True)
        print("请在3秒内切换到游戏窗口！", flush=True)
        print("[提示: 按Esc键可随时终止任务]", flush=True)
        time.sleep(3)
        
        # 检查Esc键
        if check_esc_key():
            print("\n[⚠️ 检测到Esc键，终止任务...]")
            raise KeyboardInterrupt("用户按Esc终止")
        
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
        
        # 步骤4：点击冒险按钮
        print("\n[步骤4] 点击冒险按钮...", flush=True)
        adventure_x = 680
        adventure_y = 1230
        adventure_radius = 18
        
        offset_x = random.randint(-int(adventure_radius*0.7), int(adventure_radius*0.7))
        offset_y = random.randint(-int(adventure_radius*0.7), int(adventure_radius*0.7))
        target_x = adventure_x + offset_x
        target_y = adventure_y + offset_y
        
        print(f"冒险按钮中心: ({adventure_x}, {adventure_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击冒险按钮", flush=True)
        
        # 步骤5：等待冒险弹窗
        print("\n[步骤5] 等待冒险弹窗...", flush=True)
        time.sleep(2)
        
        # 检查Esc键
        if check_esc_key():
            print("\n[⚠️ 检测到Esc键，终止任务...]")
            raise KeyboardInterrupt("用户按Esc终止")
        
        # 步骤6：点击试炼之地
        print("\n[步骤6] 点击试炼之地...", flush=True)
        trial_x = 1010
        trial_y = 520
        
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-50, 50)
        target_x = trial_x + offset_x
        target_y = trial_y + offset_y
        
        print(f"试炼之地中心: ({trial_x}, {trial_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击试炼之地", flush=True)
        
        # 步骤7：等待试炼之地弹窗
        print("\n[步骤7] 等待试炼之地弹窗...", flush=True)
        time.sleep(2)
        
        # 检查Esc键
        if check_esc_key():
            print("\n[⚠️ 检测到Esc键，终止任务...]")
            raise KeyboardInterrupt("用户按Esc终止")
        
        # 5个子任务，每个领取2次免费
        # 格式: (任务名, (x, y, y_limit))
        # y_limit: Y轴偏移限制，宝石矿洞使用20，其他使用70
        tasks = [
            ("废弃矿山", (970, 610, 70)),
            ("远古战场", (970, 840, 70)),
            ("神秘森林", (970, 1090, 70)),
            ("月光神殿", (970, 1330, 70)),
            ("宝石矿洞", (980, 1490, 20)),  # Y轴偏移限制为20
        ]
        
        # 优化执行顺序：每个任务重复2次，再执行下一个任务
        step_num = 8
        for task_name, task_center in tasks:
            print("\n" + "=" * 50, flush=True)
            print(f"【{task_name}】执行2次", flush=True)
            print("=" * 50, flush=True)
            
            # 每个任务执行2次
            for round_num in range(1, 3):
                claim_trial_task(controller, task_name, task_center, step_num, round_num, close_popup=(round_num==2))
                step_num += 8  # 每个任务8个步骤
            
            # 任务完成后关闭弹窗
            close_task_popup(controller, step_num)
            step_num += 2  # 关闭弹窗2个步骤
        
        # 关闭试炼之地弹窗
        close_adventure_popup(controller)
    
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
    run_adventure_trial_task()
