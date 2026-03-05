import sys
sys.path.insert(0, 'skills/claude-code-sender')
from scripts.claude_node_sdk import ClaudeNodeSDK
import json

sdk = ClaudeNodeSDK('claude')

# 构建任务指令
task_instruction = """# [TASK] 协同工作任务单

## 任务信息
- 任务ID: task-billing-20260305
- 发送者: kimi
- 发送时间: 2026-03-05 21:15
- 优先级: high

## 任务指令
请分析账单文件并生成专业报告：

1. 读取文件: D:\\projects\\workspace\\shared\\input\\billing_2026-02-09_2026-03-04.csv
2. 使用 billing-analyzer 技能分析账单数据
3. 生成完整的分析报告，包括：
   - 消费概览（总消费、日均消费、模型数量等）
   - 消费趋势分析
   - 模型消费排行
   - 提供商消费分布
   - 消费异常检测
   - 优化建议

## 输出要求
- 输出目录: D:\\projects\\workspace\\shared\\output\\task-billing-20260305\\
- 结果文件: result.json（必须包含状态、输出内容、生成文件列表）
- 报告文件: billing_report.md（完整的 Markdown 格式报告）
- 日志文件: execution.log（执行过程记录）

## result.json 格式
{
  "taskId": "task-billing-20260305",
  "status": "success/failed",
  "output": "执行结果摘要",
  "outputFiles": ["billing_report.md", "execution.log"],
  "executedAt": "2026-03-05T21:XX:00Z"
}

## 执行完成后
1. 创建 result.json 文件
2. 在回复中简要说明完成情况和生成文件
"""

print('正在发送任务给 Claude Code...')
result = sdk.send_task(
    instruction=task_instruction,
    output_dir='D:\\projects\\workspace\\shared\\output\\task-billing-20260305',
    max_turns=15
)

print(f'任务发送结果: {json.dumps(result, indent=2, ensure_ascii=False)}')
