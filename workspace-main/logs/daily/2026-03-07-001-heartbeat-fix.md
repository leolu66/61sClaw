# 2026-03-07 工作日志

## 时间
21:06

## 事件
心跳告警路由问题排查

## 问题
- 现象：小天才（general-agent）的心跳告警被发到了小白的飞书（OpenClaw 机器人）
- 期望：告警应该发到当前会话（web UI）和六一自己的飞书（oc_xbot）

## 尝试的修复
- 在 bindings 配置中添加 `accountId: "oc_xbot"` 到 general-agent
- 结果：OpenClaw 启动失败，提示 `Unrecognized key: "accountId"`
- 教训：bindings 不支持 accountId 字段

## 经验教训
- bindings 配置不支持 accountId 字段
- 需要查文档确认正确的配置方式，或者换其他方案

## 待处理
- 查找 OpenClaw 文档，确认如何控制不同 agent 使用不同的飞书账户发送消息
