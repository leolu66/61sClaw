# Cross Device Message - 跨设备通信技能

实现小天才（笔记本）和小白（台式机）之间的任务协作。

## 功能

- **消息队列**：通过 NAS Z 盘传递消息
- **局域网检测**：自动检测是否在同一 WiFi
- **任务分发**：向对方设备发送任务并接收结果
- **自动执行**：接收任务后自动执行并返回结果

## 文件结构

```
agfiles/cross-device-msg/
├── design.md          # 设计方案
├── msg_queue.py       # 消息队列核心
├── network_detect.py  # 网络检测
├── server.py          # HTTP 服务（小白运行）
├── client.py          # 客户端（小天才运行）
├── executor.py        # 任务执行器
└── scheduler.py       # 调度器
```

## 使用方法

### 在小白（台式机）上运行

```bash
# 1. 启动 HTTP 服务（可选，局域网模式需要）
python server.py

# 2. 启动任务调度器（必须）
python scheduler.py
```

### 在小天才（笔记本）上使用

```python
from client import run_on_xiaobai, ping

# 检测小白是否在线
if ping():
    print("小白在线！")

# 在小白上执行任务
result = run_on_xiaobai("ping", {})
print(result)

# 运行脚本
result = run_on_xiaobai("run_script", {"script_path": "test.py"})

# 列出文件
result = run_on_xiaobai("list_files", {"path": "C:/Users"})
```

## 任务类型

| 动作 | 说明 | 参数 |
|------|------|------|
| ping | 测试连接 | - |
| echo | 回显消息 | `message` |
| run_script | 运行脚本 | `script_path` |
| list_files | 列出目录 | `path` |

## 通信模式

1. **在家模式**：同一 WiFi 下，HTTP 直连，实时
2. **出门模式**：通过 NAS Z 盘消息队列，非实时

## 配置

修改以下文件中的设备名称和 IP：

- `client.py`: `XIAOBAI_HOST`, `DEVICE_NAME`
- `server.py`: `DEVICE_NAME`
- `scheduler.py`: `DEVICE_NAME`
- `network_detect.py`: `XIAOBAI_HOST`
