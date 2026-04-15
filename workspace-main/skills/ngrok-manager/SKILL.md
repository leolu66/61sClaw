# ngrok-manager - Ngrok 公网映射管理技能

## 需求说明（SRS）

### 触发条件
用户说以下指令时触发此技能：
- "启动 webhook" / "开启 webhook" / "启动公网映射" / "启动 ngrok"
- "关闭 webhook" / "关闭公网映射" / "关闭 ngrok" / "停止 ngrok"
- "查看 ngrok 状态" / "ngrok 状态"

### 功能描述
管理 ngrok 公网映射服务，用于将本地 OpenClaw Gateway (端口 18789) 暴露到公网，实现远程访问 Control UI。

- **启动**: 在后台启动 ngrok，映射本地 18789 端口到公网
- **关闭**: 查找并终止 ngrok 进程
- **状态**: 检查 ngrok 是否正在运行

### 输入/输出
- **输入**: 操作类型（启动/关闭/状态）
- **输出**: 操作结果和公网 URL（如果是启动）

### 依赖条件
- ngrok 已安装并添加到系统 PATH
- ngrok 已配置 authtoken
- OpenClaw Gateway 运行在 18789 端口

### 边界情况
- ngrok 未安装：提示用户安装
- 端口已被占用：尝试关闭现有进程后重新启动
- 启动失败：显示错误信息

---

## 使用方法

### 启动 ngrok

```bash
python scripts/ngrok-manager.py start
```

输出示例：
```
✅ ngrok 已启动
🌐 公网地址: https://xxxx.ngrok-free.app
📍 本地映射: 127.0.0.1:18789 → 公网
💡 使用此地址远程访问 OpenClaw Control UI
```

### 关闭 ngrok

```bash
python scripts/ngrok-manager.py stop
```

输出示例：
```
✅ ngrok 已停止
🔍 终止进程: ngrok.exe (PID: 12345)
```

### 查看状态

```bash
python scripts/ngrok-manager.py status
```

输出示例：
```
📊 ngrok 状态: 运行中
🌐 公网地址: https://xxxx.ngrok-free.app
🔌 本地端口: 18789
```

---

## 相关文件

- `scripts/ngrok-manager.py` - 主脚本

---

## 注意事项

- ngrok 免费版每次启动会分配新的随机域名
- 确保 ngrok 已配置 authtoken: `ngrok config add-authtoken <token>`
- 免费版有连接数和时间限制
- 生产环境建议使用付费版或自建内网穿透

---

## DoD 检查表

- [x] 需求说明（SRS）完整
- [x] 触发条件明确
- [x] 使用方法文档化
- [x] 边界情况说明
- [x] 输出格式规范
