---
name: jhwg-auto
description: |
  几何王国游戏自动点击工具 - 模拟真人鼠标操作完成游戏日常任务。
  支持领取PC端奖励、商店免费福利、终生卡奖励、巡逻奖励、自动钓鱼等任务。
  
  触发命令：
  - 代玩几何王国
  - 几何王国
  - 玩jhwg / 玩JHWG
  - play jhwg / play JHWG
  - 领取PC端奖励
  - 领取商店福利
  - 领取终生卡
  - 领取巡逻奖励
  - 开启自动钓鱼
  
  当用户需要自动完成几何王国游戏日常任务、代玩游戏、或领取游戏奖励时使用此技能。
---

# 几何王国自动任务

自动化完成《几何王国》支付宝小游戏的日常任务，模拟真人鼠标操作，带防检测机制。

## 功能特性

- 🖱️ **真人鼠标轨迹**：贝塞尔曲线移动，非直线瞬移
- ⏱️ **随机延迟**：移动速度、点击间隔带随机性
- 🎯 **随机偏移**：点击位置在中心点附近随机偏移（防检测）
- 🔢 **任务编号**：每个任务都有数字编号，方便快速选择
- 📋 **策略执行**：支持批量执行多个任务（日常/快速/全部等策略）
- 🔧 **模块化设计**：每个任务独立脚本，可单独运行

## 任务列表（带编号）

### 日常任务

| 编号 | 任务 | 脚本 | 说明 | 耗时 |
|------|------|------|------|------|
| 1 | 🖥️ PC端奖励 | `task_pc_reward.py` | 点击PC端图标 → 领取 → 关闭弹窗 | ~10秒 |
| 2 | 🏪 商店免费福利 | `task_shop_free_reward.py` | 商店 → 领取 → 返回 | ~10秒 |
| 3 | 💳 终生卡奖励 | `task_lifetime_card.py` | 畅玩卡 → 终身卡 → 领取 → 返回 | ~15秒 |
| 4 | 🚓 巡逻奖励 | `task_patrol_reward.py` | 巡逻奖励 → 领取全部 → 关闭弹窗 | ~15秒 |
| 5 | 🎣 自动钓鱼 | `task_auto_fishing.py` | 钓鱼 → 自动 → 开始 → 返回 | ~15秒 |
| 7 | 🎲 自动招募 | `task_auto_recruit.py` | 普通招募 → 领取2次 → 确认 → 返回 | ~20秒 |
| 9 | 📦 更多领取 | `task_claim_more.py` | 邮件 + 好友收送 + 杂货铺宝箱 | ~120秒 |

### 挑战任务

| 编号 | 任务 | 脚本 | 说明 | 耗时 |
|------|------|------|------|------|
| 6 | 🎯 冒险试炼 | `task_adventure_trial.py` | 试炼之地5个地点，每个2次免费 | ~60秒 |
| 8 | 🏕️ 部落任务 | `task_tribe.py` | 部落签到 + 4个子任务 | ~30秒 |

## 策略列表

| 策略ID | 名称 | 包含任务 | 说明 |
|--------|------|----------|------|
| `all` | 全部任务 | 1,2,3,4,5,6,7,8,9 | 执行所有9个任务（约5-6分钟） |
| `daily` | 日常任务 | 1,2,3,4,5,7,9 | 每日必做的基础任务（约3-4分钟） |
| `quick` | 快速任务 | 1,2,3,4 | 耗时最短的几个任务（约1分钟） |
| `challenge` | 挑战任务 | 6,8 | 副本和挑战类任务（约2分钟） |
| `resource` | 资源收集 | 5,7,9 | 收集各类资源的任务（约3分钟） |

## 脚本路径

所有脚本位于：`C:\Users\luzhe\.openclaw\workspace-main\skills\jhwg-auto\scripts\`

### 前置要求

1. 安装依赖：`pip install pyautogui`
2. 游戏在Chrome浏览器中运行
3. 已登录支付宝账号

### 使用任务管理器

```bash
cd C:\Users\luzhe\.openclaw\workspace-main\skills\jhwg-auto\scripts

# 列出所有任务
python task_manager.py --list

# 列出所有策略
python task_manager.py --strategies

# 执行单个任务（通过编号）
python task_manager.py 1
python task_manager.py 3

# 执行单个任务（通过名称）
python task_manager.py PC端奖励
python task_manager.py 巡逻

# 执行策略
python task_manager.py --strategy all      # 全部任务
python task_manager.py --strategy daily    # 日常任务
python task_manager.py --strategy quick    # 快速任务
python task_manager.py --strategy challenge # 挑战任务
```

### 直接运行单个任务脚本

```bash
cd C:\Users\luzhe\.openclaw\workspace-main\skills\jhwg-auto\scripts
python task_pc_reward.py
python task_shop_free_reward.py
python task_lifetime_card.py
python task_patrol_reward.py
python task_auto_fishing.py
python task_adventure_trial.py
python task_auto_recruit.py
python task_tribe.py
python task_claim_more.py
```

### 运行流程

1. 脚本启动后，有3秒倒计时切换到游戏窗口
2. 鼠标自动移动并点击目标位置
3. 完成任务后自动返回主界面
4. **按 Esc 键可随时终止任务**

## 坐标配置

坐标存储在 `scripts/config.json` 中，包含：
- 游戏画面区域范围
- 各按钮的精确坐标（基于 2553x1377 分辨率）
- 鼠标移动速度参数
- 任务编号和策略配置

如需调整坐标，修改 `config.json` 中的对应值。

## 防检测机制

1. **贝塞尔曲线移动**：鼠标沿曲线移动，模拟真人轨迹
2. **随机速度**：移动时间 0.15~0.4 秒随机
3. **点击前停顿**：0.1~0.3 秒随机延迟
4. **位置随机偏移**：
   - 圆形按钮：在半径范围内随机偏移
   - 长方形按钮：中心点 ±10 像素随机偏移
5. **点击后暂停**：0.5 秒

## 文件结构

```
skills/jhwg-auto/scripts/
├── config.json              # 坐标配置和策略配置
├── mouse_controller.py      # 鼠标控制器（贝塞尔曲线）
├── keyboard_listener.py     # 键盘监听器（Esc终止）
├── browser_focus.py         # 窗口聚焦工具
├── task_manager.py          # 任务管理器（编号+策略）
├── task_pc_reward.py        # 任务1：PC端奖励
├── task_shop_free_reward.py # 任务2：商店免费福利
├── task_lifetime_card.py    # 任务3：终生卡奖励
├── task_patrol_reward.py    # 任务4：巡逻奖励
├── task_auto_fishing.py     # 任务5：自动钓鱼
├── task_adventure_trial.py  # 任务6：冒险试炼
├── task_auto_recruit.py     # 任务7：自动招募
├── task_tribe.py            # 任务8：部落任务
└── task_claim_more.py       # 任务9：更多领取
```

## 注意事项

- 鼠标移到屏幕四角会触发紧急停止（pyautogui.FAILSAFE）
- 如果换了显示器或调整窗口大小，需要重新校准坐标
- 游戏界面改版后可能需要更新坐标
- **所有任务都支持 Esc 键终止**

## 扩展开发

添加新任务的步骤：
1. 复制 `task_pc_reward.py` 作为模板
2. 修改任务名称和坐标配置
3. 在 `config.json` 中添加新任务（指定编号、名称、分类）
4. 在 `task_manager.py` 的 `TASKS` 字典中添加任务
5. 测试并调整

添加新策略的步骤：
1. 在 `config.json` 的 `strategies` 中添加策略配置
2. 指定策略ID、名称、描述、任务列表、间隔时间
3. 使用 `python task_manager.py --strategy <策略ID>` 执行
