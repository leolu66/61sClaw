#!/usr/bin/env python3
"""
任务：领取PC端奖励
点击游戏区域上方的"PC端"图标领取奖励
"""

import sys
import json
import time
import random
from pathlib import Path

# 添加父目录到路径，以便导入其他模块
sys.path.insert(0, str(Path(__file__).parent))

from mouse_controller import MouseController
from browser_focus import focus_game_tab


# PC端图标坐标配置（相对于游戏区域的百分比）
# 这些坐标需要根据实际屏幕分辨率调整
DEFAULT_CONFIG = {
    "pc_icon": {
        "x_percent": 0.85,  # 在游戏区域宽度的85%位置（右侧）
        "y_percent": 0.08,  # 在游戏区域高度的8%位置（顶部状态栏）
        "description": "PC端图标位置"
    },
    "reward_button": {
        "x_percent": 0.5,   # 奖励弹窗按钮位置（中间）
        "y_percent": 0.6,
        "description": "领取奖励按钮位置"
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


def get_screen_coordinates(game_area: dict, x_percent: float, y_percent: float) -> tuple:
    """
    将百分比坐标转换为屏幕绝对坐标
    
    Args:
        game_area: 游戏区域信息 {x, y, width, height}
        x_percent: X轴百分比 (0-1)
        y_percent: Y轴百分比 (0-1)
    
    Returns:
        (screen_x, screen_y) 屏幕绝对坐标
    """
    screen_x = game_area['x'] + int(game_area['width'] * x_percent)
    screen_y = game_area['y'] + int(game_area['height'] * y_percent)
    return (screen_x, screen_y)


def detect_game_area() -> dict:
    """
    检测游戏区域在屏幕上的位置
    
    由于无法直接获取游戏画布位置，这里使用估算或手动配置
    实际使用时可以通过截图识别或手动标定
    
    Returns:
        游戏区域信息 {x, y, width, height}
    """
    import pyautogui
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    
    # 根据用户描述的游戏布局估算游戏区域
    # 顶部10%是支付宝信息栏，所以游戏区域从10%高度开始
    # 游戏区域占左下70%宽度 × 90%高度
    
    # 估算的游戏区域（基于全屏浏览器）
    game_area = {
        'x': 0,
        'y': int(screen_height * 0.10),  # 跳过顶部支付宝栏
        'width': int(screen_width * 0.70),  # 左下70%宽度
        'height': int(screen_height * 0.90)  # 90%高度
    }
    
    return game_area


def run_pc_reward_task(use_manual_focus: bool = True) -> bool:
    """
    执行领取PC端奖励任务
    
    Args:
        use_manual_focus: 是否使用手动聚焦模式
    
    Returns:
        任务是否成功完成
    """
    print("=" * 50, flush=True)
    print("任务：领取PC端奖励", flush=True)
    print("=" * 50, flush=True)
    
    # 步骤1：聚焦到游戏窗口
    print("\n[步骤1] 聚焦到游戏窗口...", flush=True)
    print("请在3秒内切换到游戏窗口！", flush=True)
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
    
    # 直接使用精确坐标
    pc_icon = coords.get('pc_icon', {})
    pc_x = pc_icon.get('screen_x', 990)
    pc_y = pc_icon.get('screen_y', 450)
    print(f"PC端按钮位置: ({pc_x}, {pc_y})", flush=True)
    
    # 步骤4：移动鼠标并点击PC端图标（带随机偏移）
    print("\n[步骤4] 移动鼠标到PC端图标并点击...", flush=True)
    print("（鼠标将模拟真人移动轨迹，点击位置带随机偏移）", flush=True)
    
    # 获取当前位置
    current_x, current_y = controller.get_position()
    print(f"当前鼠标位置: ({current_x}, {current_y})", flush=True)
    
    # 在中心点 ±10 像素范围内随机偏移
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    target_x = pc_x + offset_x
    target_y = pc_y + offset_y
    
    print(f"PC端按钮中心: ({pc_x}, {pc_y})", flush=True)
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    # 移动到PC端图标并点击
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击PC端图标", flush=True)
    
    # 步骤5：等待奖励弹窗并点击领取
    print("\n[步骤5] 等待奖励弹窗...", flush=True)
    time.sleep(2)  # 等待弹窗出现
    
    # 使用领取按钮的精确坐标
    reward_btn = coords.get('reward_button', {})
    btn_x = reward_btn.get('screen_x', 960)
    btn_y = reward_btn.get('screen_y', 1120)
    
    print(f"领取按钮中心: ({btn_x}, {btn_y})", flush=True)
    
    # 在中心点 ±10 像素范围内随机偏移
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    target_x = btn_x + offset_x
    target_y = btn_y + offset_y
    
    print(f"随机偏移: ({offset_x}, {offset_y})", flush=True)
    print(f"实际点击位置: ({target_x}, {target_y})", flush=True)
    
    controller.move_and_click(target_x, target_y)
    print("[OK] 已点击领取按钮", flush=True)
    
    # 步骤6：关闭恭喜画面弹窗
    print("\n[步骤6] 关闭恭喜画面弹窗...", flush=True)
    time.sleep(1.5)  # 等待弹窗出现
    
    close_popup = coords.get('close_popup', {})
    x_range = close_popup.get('x_range', [630, 1290])
    y_options = close_popup.get('y_options', [[325, 695], [1070, 1520]])
    
    # 随机选择X坐标
    close_x = random.randint(x_range[0], x_range[1])
    
    # 随机选择上方或下方区域
    y_zone = random.choice(y_options)
    close_y = random.randint(y_zone[0], y_zone[1])
    
    print(f"关闭弹窗点击位置: ({close_x}, {close_y})", flush=True)
    controller.move_and_click(close_x, close_y)
    print("[OK] 已关闭弹窗", flush=True)
    
    print("\n" + "=" * 50, flush=True)
    print("任务完成！", flush=True)
    print("=" * 50, flush=True)
    
    return True


def calibrate_coordinates():
    """
    坐标校准模式
    让用户手动移动鼠标到PC端图标位置，记录坐标
    """
    import pyautogui
    
    print("=" * 50)
    print("坐标校准模式")
    print("=" * 50)
    print("\n请按以下步骤操作：")
    print("1. 切换到游戏窗口")
    print("2. 将鼠标移动到 PC端 图标位置")
    print("3. 5秒后将自动记录坐标")
    print()
    
    for i in range(5, 0, -1):
        print(f"倒计时: {i}秒...", end='\r')
        time.sleep(1)
    
    x, y = pyautogui.position()
    print(f"\n记录到的坐标: ({x}, {y})")
    
    # 计算相对于游戏区域的百分比
    game_area = detect_game_area()
    x_percent = (x - game_area['x']) / game_area['width']
    y_percent = (y - game_area['y']) / game_area['height']
    
    print(f"\n百分比坐标:")
    print(f"  x_percent: {x_percent:.4f}")
    print(f"  y_percent: {y_percent:.4f}")
    
    print("\n请更新 config.json 中的坐标配置")
    
    return {
        'x': x,
        'y': y,
        'x_percent': x_percent,
        'y_percent': y_percent
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='领取PC端奖励任务')
    parser.add_argument('--calibrate', action='store_true', 
                       help='进入坐标校准模式')
    parser.add_argument('--auto-focus', action='store_true',
                       help='尝试自动聚焦窗口（默认手动）')
    
    args = parser.parse_args()
    
    if args.calibrate:
        calibrate_coordinates()
    else:
        run_pc_reward_task(use_manual_focus=not args.auto_focus)
