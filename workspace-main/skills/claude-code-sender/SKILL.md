---
name: claude-code-sender
description: 通过 SDK 向 Claude Code 进程发送协同工作任务单，支持任务分配、执行监控、结果检查和改进反馈的完整工作流。当需要让 Claude Code 作为子节点执行协同任务、自动化代码任务、多轮对话直到任务完成时使用此技能。
---

# Claude Code SDK 发送器

## 概述

本技能提供通过 SDK 向 Claude Code 进程发送**协同工作任务单**的能力，支持完整的任务生命周期：

```
发送任务单 → Claude Code 识别并执行 → 输出结果到共享目录 → 检查结果 → 
[结果 OK] → 关闭会话
[结果有问题] → 反馈改进要求 → 重新执行 → 再次检查
```

## 重要：权限配置（必须）

### 1. 目录授权

**D:\projects 是共享工作目录**，需要在 Claude Code 中配置为允许访问：

```bash
claude
/allowed-dirs add D:\projects
/allowed-dirs list  # 验证
```

### 2. 权限模式（关键）

**必须使用 `--permission-mode acceptEdits`** 参数，否则 Claude Code 会拒绝文件操作：

```bash
# ❌ 错误方式（会失败）
claude -p "创建文件..."

# ✅ 正确方式
claude -p "创建文件..." --permission-mode acceptEdits
```

### 为什么需要这些配置

| 配置项 | 作用 | 不配置的后果 |
|--------|------|-------------|
| `/allowed-dirs` | 允许访问工作目录 | 无法读写任何文件 |
| `--permission-mode acceptEdits` | 自动接受编辑权限 | 每次操作都需要人工确认 |

**这两个配置缺一不可。**

---

## 核心功能

### 1. 任务单格式

发送给 Claude Code 的消息使用标准任务单格式：

```markdown
# [TASK] 协同工作任务单

## 任务信息
- 任务ID: task-{timestamp}
- 发送者: {sender_id}
- 发送时间: {timestamp}
- 优先级: high/medium/low

## 任务指令
{具体的任务描述}

## 输出要求
- 输出目录: D:\projects\workspace\shared\output\{task_id}\
- 结果文件: result.json（必须包含状态、输出内容、生成文件列表）
- 日志文件: execution.log（执行过程记录）

## 执行完成后
1. 创建 result.json 文件，格式如下：
   {
     "taskId": "task-xxx",
     "status": "success/failed",
     "output": "执行结果摘要",
     "outputFiles": ["file1.txt", "file2.py"],
     "executedAt": "2026-03-04T21:00:00Z"
   }

2. 在回复中简要说明：
   - 完成了什么
   - 生成了哪些文件
   - 是否成功

## 注意事项
- 这是协同工作任务，请严格按照输出要求执行
- 结果文件必须创建，否则主节点无法确认完成
- 如有问题请在 result.json 中 status 设为 failed 并说明原因
```

### 2. 完整工作流

```python
from claude_code_sender.scripts.claude_task_coordinator import TaskCoordinator

coordinator = TaskCoordinator()

# 发送任务并等待完成
result = coordinator.send_task_and_wait(
    node_id="claude",
    instruction="创建一个 Python 计算器类",
    output_dir="D:\\projects\\workspace\\shared\\output\\task-001",
    check_callback=my_check_function,  # 自定义检查函数
    max_retries=2  # 失败时最多重试2次
)
```

### 3. 会话管理

- **保持会话**：使用 `--continue` 维持对话上下文
- **检查完成**：读取共享目录中的 result.json
- **反馈改进**：结果有问题时在同一会话中要求改进
- **关闭会话**：任务完成且结果 OK 后关闭

## 使用方式

### 方式1: 使用 TaskCoordinator（推荐）

```python
from claude_code_sender.scripts.claude_task_coordinator import TaskCoordinator

coordinator = TaskCoordinator()

# 简单任务
result = coordinator.send_task(
    node_id="claude",
    instruction="创建一个简单的 HTTP 客户端类",
    output_dir="D:\\projects\\workspace\\shared\\output\\task-http"
)

# 带检查的任务
result = coordinator.send_task_and_wait(
    node_id="claude",
    instruction="分析这个日志文件并生成报告",
    file_path="logs/app.log",
    output_dir="D:\\projects\\workspace\\shared\\output\\task-analysis",
    check_callback=lambda r: "error" not in r.get("output", "").lower(),
    max_retries=2
)
```

### 方式2: 使用 ClaudeNodeSDK

```python
from claude_code_sender.scripts.claude_node_sdk import ClaudeNodeSDK

sdk = ClaudeNodeSDK("claude")

# 发送任务单格式消息
result = sdk.send_task(
    instruction="创建一个数据处理器",
    output_dir="D:\\projects\\workspace\\shared\\output\\task-001",
    max_turns=10
)

# 检查结果
if result["success"]:
    # 检查 result.json
    import json
    result_file = Path("D:\\projects\\workspace\\shared\\output\\task-001\\result.json")
    if result_file.exists():
        task_result = json.loads(result_file.read_text())
        if task_result["status"] == "success":
            print("任务完成！")
```

### 方式3: 命令行方式

**必须添加 `--permission-mode acceptEdits`** 才能自动接受文件操作权限：

```bash
# ✅ 正确：发送任务（带权限参数）
claude -p "# [TASK] 协同工作任务单

## 任务信息
- 任务ID: task-001
- 发送者: kimi

## 任务指令
创建一个 Python 计算器类，支持加减乘除

## 输出要求
- 输出目录: D:\projects\workspace\shared\output\task-001\
- 结果文件: result.json

## 执行完成后
请创建 result.json 文件并说明完成情况。" \
--permission-mode acceptEdits \
--output-format json

# 检查结果后，如有问题继续改进
claude --continue "结果有问题，请修复以下问题：缺少异常处理"
```

**常用参数**：
- `--permission-mode acceptEdits` - 自动接受编辑权限（**必须**）
- `--output-format json` - JSON 格式输出
- `--max-turns 5` - 限制对话轮数
- `--cwd <path>` - 设置工作目录

## 任务结果检查

### 自动检查流程

```python
def check_task_result(output_dir: str) -> dict:
    """检查任务执行结果"""
    result_file = Path(output_dir) / "result.json"
    
    if not result_file.exists():
        return {"ok": False, "error": "结果文件不存在"}
    
    result = json.loads(result_file.read_text())
    
    if result["status"] != "success":
        return {"ok": False, "error": result.get("output", "未知错误")}
    
    # 检查输出文件是否存在
    for f in result.get("outputFiles", []):
        if not (Path(output_dir) / f).exists():
            return {"ok": False, "error": f"输出文件不存在: {f}"}
    
    return {"ok": True, "result": result}
```

### 检查结果后的处理

```python
# 检查结果
status = check_task_result(output_dir)

if status["ok"]:
    print("任务完成，关闭会话")
    # 会话结束
else:
    print(f"结果有问题: {status['error']}")
    # 在同一会话中要求改进
    improvement = f"结果检查失败: {status['error']}\n请修复问题并重新输出结果。"
    sdk.send_task_with_continue(improvement)
```

## 前置条件

1. 安装 Claude Code CLI:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. 设置 API 密钥:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

3. 创建共享目录:
   ```bash
   mkdir -p D:\projects\workspace\shared\output
   ```

## 脚本资源

### scripts/claude_sender.py
基础 SDK 封装，提供 `send_to_claude()` 和 `ClaudeCodeOptions`。

### scripts/claude_node_sdk.py
节点 SDK 封装，提供 `ClaudeNodeSDK` 和 `MultiNodeCoordinator`。

### scripts/claude_task_coordinator.py
任务协调器，提供完整的任务生命周期管理：
- `send_task()` - 发送任务
- `send_task_and_wait()` - 发送任务并等待完成
- `check_result()` - 检查结果
- `request_improvement()` - 要求改进
- `close_session()` - 关闭会话

## 完整示例

```python
from claude_code_sender.scripts.claude_task_coordinator import TaskCoordinator
import time

coordinator = TaskCoordinator()

# 定义结果检查函数
def check_calculator_result(output_dir: str) -> dict:
    """检查计算器实现是否正确"""
    result_file = Path(output_dir) / "result.json"
    if not result_file.exists():
        return {"ok": False, "error": "结果文件不存在"}
    
    result = json.loads(result_file.read_text())
    
    # 检查是否包含必要的文件
    code_file = Path(output_dir) / "calculator.py"
    if not code_file.exists():
        return {"ok": False, "error": "缺少 calculator.py 文件"}
    
    # 检查代码内容
    code = code_file.read_text()
    required_methods = ["add", "subtract", "multiply", "divide"]
    for method in required_methods:
        if f"def {method}" not in code:
            return {"ok": False, "error": f"缺少 {method} 方法"}
    
    return {"ok": True, "result": result}

# 发送任务并等待完成
result = coordinator.send_task_and_wait(
    node_id="claude",
    instruction="""创建一个 Python 计算器类 Calculator，要求：
1. 支持加减乘除四个基本运算
2. 每个运算都是一个独立的方法
3. 除法要处理除零错误
4. 添加简单的使用示例""",
    output_dir="D:\\projects\\workspace\\shared\\output\\task-calc",
    check_callback=check_calculator_result,
    max_retries=2,
    timeout=300
)

if result["success"]:
    print(f"任务完成！生成文件: {result['output_files']}")
else:
    print(f"任务失败: {result['error']}")
```

## 最佳实践

1. **始终使用任务单格式** - 让 Claude Code 明确识别这是协同任务
2. **指定明确的输出目录** - 便于结果检查和文件管理
3. **要求创建 result.json** - 标准化的结果确认方式
4. **保持会话直到确认完成** - 不要提前关闭会话
5. **检查结果后再关闭** - 确保任务真正完成且质量 OK
6. **有问题时要求改进** - 在同一会话中反馈问题并等待修复
