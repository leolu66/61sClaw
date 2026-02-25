#!/usr/bin/env python3
"""
任务：黑暗之门 - 冒险任务中的挑战
点击冒险 -> 黑暗之门 -> 开始挑战 -> 确认开始
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


def run_dark_portal_task() -> bool:
    """
    执行黑暗之门任务
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：黑暗之门 - 冒险挑战", flush=True)
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
        
        # 步骤4：点击冒险按钮
        print("\n[步骤4] 点击冒险按钮...", flush=True)
        adventure_x = 690
        adventure_y = 1230
        adventure_radius = 40
        
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
        
        # 步骤6：点击黑暗之门区域
        print("\n[步骤6] 点击黑暗之门区域...", flush=True)
        dark_portal_x = 1010
        dark_portal_y = 1040
        
        # 200x90区域，一半是100x45
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-45, 45)
        target_x = dark_portal_x + offset_x
        target_y = dark_portal_y + offset_y
        
        print(f"黑暗之门中心: ({dark_portal_x}, {dark_portal_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击黑暗之门", flush=True)
        
        # 步骤7：等待黑暗之门任务弹窗
        print("\n[步骤7] 等待黑暗之门任务弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤8：点击开始挑战按钮
        print("\n[步骤8] 点击开始挑战按钮...", flush=True)
        start_x = 960
        start_y = 960
        
        # 100x20区域，一半是50x10
        offset_x = random.randint(-50, 50)
        offset_y = random.randint(-10, 10)
        target_x = start_x + offset_x
        target_y = start_y + offset_y
        
        print(f"开始挑战按钮中心: ({start_x}, {start_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击开始挑战按钮", flush=True)
        
        # 步骤9：等待确认页面
        print("\n[步骤9] 等待确认页面...", flush=True)
        time.sleep(2)
        
        # 步骤10：点击确认页面的开始挑战按钮
        print("\n[步骤10] 点击确认页面的开始挑战按钮...", flush=True)
        confirm_x = 960
        confirm_y = 1450
        
        # 160x40区域，一半是80x20
        offset_x = random.randint(-80, 80)
        offset_y = random.randint(-20, 20)
        target_x = confirm_x + offset_x
        target_y = confirm_y + offset_y
        
        print(f"确认开始按钮中心: ({confirm_x}, {confirm_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击确认开始按钮", flush=True)
        
        # 步骤11：等待局数确认弹窗
        print("\n[步骤11] 等待局数确认弹窗...", flush=True)
        time.sleep(2)
        
        # 步骤12：点击确认按钮
        print("\n[步骤12] 点击确认按钮...", flush=True)
        confirm_btn_x = 1100
        confirm_btn_y = 1050
        
        # 120x40区域，一半是60x20
        offset_x = random.randint(-60, 60)
        offset_y = random.randint(-20, 20)
        target_x = confirm_btn_x + offset_x
        target_y = confirm_btn_y + offset_y
        
        print(f"确认按钮中心: ({confirm_btn_x}, {confirm_btn_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_and_click(target_x, target_y)
        print("[OK] 已点击确认按钮", flush=True)
        
        # ========== 战斗阶段 ==========
        print("\n" + "=" * 50, flush=True)
        print("【战斗阶段】", flush=True)
        print("=" * 50, flush=True)
        
        # 步骤13：移动鼠标到出战技能按钮
        print("\n[步骤13] 移动鼠标到出战技能按钮...", flush=True)
        skill_x = 690
        skill_y = 1040
        skill_radius = 15  # 直径30，一半是15
        
        offset_x = random.randint(-int(skill_radius*0.7), int(skill_radius*0.7))
        offset_y = random.randint(-int(skill_radius*0.7), int(skill_radius*0.7))
        target_x = skill_x + offset_x
        target_y = skill_y + offset_y
        
        print(f"出战技能按钮中心: ({skill_x}, {skill_y})", flush=True)
        print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
        print(f"鼠标移动位置: ({target_x}, {target_y})", flush=True)
        
        controller.move_to(target_x, target_y)
        print("[OK] 已移动到出战技能按钮", flush=True)
        
        # 等待2秒后开始点击
        print("\n[等待] 等待2秒后开始点击...", flush=True)
        time.sleep(2)
        
        # 战斗阶段：重复点击技能4次（每次间隔24秒冷却）
        # 第1次点击
        print("\n[步骤14] 第1次点击技能...", flush=True)
        controller.click()
        print("[OK] 已点击技能", flush=True)
        
        # 等待24秒冷却
        print("\n[等待] 等待24秒技能冷却...", flush=True)
        time.sleep(24)
        
        # 第2次点击
        print("\n[步骤15] 第2次点击技能...", flush=True)
        controller.click()
        print("[OK] 已点击技能", flush=True)
        
        # 等待24秒冷却
        print("\n[等待] 等待24秒技能冷却...", flush=True)
        time.sleep(24)
        
        # 第3次点击
        print("\n[步骤16] 第3次点击技能...", flush=True)
        controller.click()
        print("[OK] 已点击技能", flush=True)
        
        # 等待24秒冷却
        print("\n[等待] 等待24秒技能冷却...", flush=True)
        time.sleep(24)
        
        # 第4次点击
        print("\n[步骤17] 第4次点击技能...", flush=True)
        controller.click()
        print("[OK] 已点击技能", flush=True)
    
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
    run_dark_portal_task()
