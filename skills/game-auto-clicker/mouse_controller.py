#!/usr/bin/env python3
"""
鼠标控制器 - 模拟真人鼠标操作
带轨迹模拟，避免被检测为外挂
"""

import pyautogui
import random
import time
import math
from typing import Tuple, List

# 安全设置：鼠标移到屏幕角落会触发异常（紧急停止）
pyautogui.FAILSAFE = True


class MouseController:
    """鼠标控制器，模拟真人操作"""
    
    def __init__(self, config: dict = None):
        """
        初始化鼠标控制器
        
        Args:
            config: 配置字典，包含延迟参数
        """
        self.config = config or {}
        self.move_duration_min = self.config.get('move_duration_min', 0.3)
        self.move_duration_max = self.config.get('move_duration_max', 0.8)
        self.click_delay_min = self.config.get('click_delay_min', 0.1)
        self.click_delay_max = self.config.get('click_delay_max', 0.3)
        self.post_click_delay = self.config.get('post_click_delay', 2.0)
    
    def _bezier_curve(self, p0: Tuple[int, int], p1: Tuple[int, int], 
                      p2: Tuple[int, int], t: float) -> Tuple[int, int]:
        """
        二次贝塞尔曲线计算
        
        Args:
            p0: 起点
            p1: 控制点
            p2: 终点
            t: 插值参数 (0-1)
        
        Returns:
            曲线上的点坐标
        """
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        return (int(x), int(y))
    
    def _generate_control_point(self, start: Tuple[int, int], 
                                end: Tuple[int, int]) -> Tuple[int, int]:
        """
        生成随机控制点，使鼠标轨迹更自然
        
        Args:
            start: 起点
            end: 终点
        
        Returns:
            控制点坐标
        """
        # 计算中点
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # 计算距离
        distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
        
        # 随机偏移量（偏移距离为总距离的10%-30%）
        offset_range = distance * 0.2
        offset_x = random.uniform(-offset_range, offset_range)
        offset_y = random.uniform(-offset_range, offset_range)
        
        # 添加一些随机性，让轨迹有时向上凸有时向下凸
        if random.random() > 0.5:
            offset_x += random.uniform(-50, 50)
        
        return (int(mid_x + offset_x), int(mid_y + offset_y))
    
    def move_to(self, target_x: int, target_y: int, 
                duration: float = None) -> None:
        """
        模拟真人移动鼠标到目标位置
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            duration: 移动持续时间（秒），None则使用随机值
        """
        # 获取当前位置
        start_x, start_y = pyautogui.position()
        start = (start_x, start_y)
        end = (target_x, target_y)
        
        # 如果已经在目标位置附近，直接返回
        if abs(start_x - target_x) < 5 and abs(start_y - target_y) < 5:
            return
        
        # 确定移动时间
        if duration is None:
            duration = random.uniform(self.move_duration_min, self.move_duration_max)
        
        # 根据距离调整时间（距离越远，移动时间越长）
        distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
        duration = duration * (1 + distance / 1000)  # 距离越远时间越长
        
        # 生成控制点
        control = self._generate_control_point(start, end)
        
        # 计算步数（每秒60帧）
        steps = max(int(duration * 60), 10)
        
        # 执行贝塞尔曲线移动
        for i in range(steps + 1):
            t = i / steps
            # 使用缓动函数让移动更自然
            t = self._ease_in_out_cubic(t)
            
            x, y = self._bezier_curve(start, control, end, t)
            pyautogui.moveTo(x, y)
            
            # 每步的延迟
            time.sleep(duration / steps)
        
        # 最后确保到达目标位置
        pyautogui.moveTo(target_x, target_y)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """缓动函数：先慢后快再慢，更像真人操作"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def click(self, button: str = 'left') -> None:
        """
        模拟点击，带随机延迟
        
        Args:
            button: 鼠标按钮，'left' 或 'right'
        """
        # 点击前随机停顿（模拟人的反应时间）
        delay = random.uniform(self.click_delay_min, self.click_delay_max)
        time.sleep(delay)
        
        # 执行点击
        pyautogui.click(button=button)
        
        # 点击后停顿
        time.sleep(self.post_click_delay)
    
    def move_and_click(self, target_x: int, target_y: int, 
                       button: str = 'left', duration: float = None) -> None:
        """
        移动到目标位置并点击（一站式操作）
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            button: 鼠标按钮
            duration: 移动持续时间
        """
        self.move_to(target_x, target_y, duration)
        self.click(button)
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        return pyautogui.position()
    
    def random_idle_movement(self, center_x: int, center_y: int, 
                            radius: int = 20) -> None:
        """
        在目标位置附近随机小幅度移动（模拟人等待时的微小动作）
        
        Args:
            center_x: 中心X坐标
            center_y: 中心Y坐标
            radius: 移动半径
        """
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, radius)
        
        offset_x = int(distance * math.cos(angle))
        offset_y = int(distance * math.sin(angle))
        
        pyautogui.moveTo(center_x + offset_x, center_y + offset_y, 
                        duration=random.uniform(0.1, 0.3))


if __name__ == '__main__':
    # 测试代码
    print("鼠标控制器测试")
    print("3秒后将移动到屏幕中心...")
    time.sleep(3)
    
    controller = MouseController()
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2
    
    print(f"屏幕尺寸: {screen_width}x{screen_height}")
    print(f"当前位置: {controller.get_position()}")
    
    # 测试移动到中心
    print(f"移动到中心: ({center_x}, {center_y})")
    controller.move_to(center_x, center_y)
    
    print(f"移动后位置: {controller.get_position()}")
    print("测试完成！")
