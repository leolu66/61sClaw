# Game Auto Clicker - 游戏自动点击工具

模拟真人鼠标操作的游戏自动化工具，支持轨迹模拟、随机延迟等防检测机制。

## 功能特点

- 🖱️ **真人鼠标轨迹**：使用贝塞尔曲线模拟自然的鼠标移动
- ⏱️ **随机延迟**：移动速度、点击间隔都带有随机性
- 🎯 **坐标配置化**：按钮位置通过配置文件管理，便于调整
- 🔧 **模块化设计**：每个任务独立脚本，可单独运行

## 文件结构

```
game-auto-clicker/
├── config.json              # 配置文件（坐标、延迟参数）
├── mouse_controller.py      # 鼠标控制器核心模块
├── browser_focus.py         # 浏览器标签聚焦工具
├── task_pc_reward.py        # 任务：领取PC端奖励
└── README.md                # 本文件
```

## 安装依赖

```bash
pip install pyautogui
```

## 使用方法

### 1. 坐标校准（首次使用必须）

由于不同屏幕分辨率下按钮位置不同，需要先校准坐标：

```bash
python task_pc_reward.py --calibrate
```

按提示将鼠标移动到 **PC端图标** 位置，程序会记录坐标并输出百分比配置。

### 2. 更新配置

将校准得到的坐标更新到 `config.json`：

```json
{
  "coordinates": {
    "pc_icon": {
      "x_percent": 0.85,
      "y_percent": 0.08,
      "description": "PC端图标位置"
    }
  }
}
```

### 3. 运行任务

```bash
# 手动聚焦模式（推荐）
python task_pc_reward.py

# 自动聚焦模式（尝试自动切换到游戏窗口）
python task_pc_reward.py --auto-focus
```

## 坐标系统说明

游戏区域坐标采用**百分比系统**，适配不同分辨率：

- 原点 (0, 0)：游戏区域左上角
- X轴：从左到右，范围 0.0 ~ 1.0
- Y轴：从上到下，范围 0.0 ~ 1.0

例如：
- `x: 0.5, y: 0.5` = 游戏区域正中心
- `x: 0.85, y: 0.08` = 右上角附近（PC端图标位置）

## 开发新任务

参考 `task_pc_reward.py` 创建新的任务脚本：

```python
from mouse_controller import MouseController
from browser_focus import focus_game_tab

def run_my_task():
    # 1. 聚焦窗口
    focus_game_tab(use_manual=True)
    
    # 2. 初始化控制器
    controller = MouseController()
    
    # 3. 移动并点击
    controller.move_and_click(target_x, target_y)
    
    # 4. 后续操作...

if __name__ == '__main__':
    run_my_task()
```

## 防检测机制

1. **贝塞尔曲线移动**：鼠标沿曲线移动，不是直线瞬移
2. **随机速度**：每次移动时间不同（0.3~0.8秒基础时间）
3. **距离自适应**：移动距离越远，耗时越长
4. **点击延迟**：点击前有随机停顿（0.1~0.3秒）
5. **缓动函数**：移动速度先慢后快再慢，更像真人

## 注意事项

- ⚠️ **安全设置**：鼠标移到屏幕四角会触发紧急停止（pyautogui.FAILSAFE）
- 🖥️ **分辨率变化**：如果换了显示器或调整了窗口大小，需要重新校准坐标
- 🎮 **游戏更新**：游戏界面改版后可能需要重新校准

## 待完善功能

- [ ] 图像识别自动定位按钮（无需手动校准坐标）
- [ ] 支持 OpenClaw Browser Relay 自动切换标签页
- [ ] 更多游戏任务脚本
- [ ] 任务调度器（定时执行多个任务）
