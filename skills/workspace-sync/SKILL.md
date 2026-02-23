# Workspace Sync Skill

将本地workspace同步到NAS共享目录，支持多设备共享。

## 功能
- 同步skills、memory等重要目录到Z盘
- 增量同步，只复制修改过的文件
- 同步完成后显示变更统计

## 使用方法
- "同步工作目录"、"备份到NAS"、"sync to Z"

## 配置
在 scripts/sync_config.json 中设置：
- target_name: 设备名称（如"小天才"、"小白"）
- target_dir: 目标目录（如"Z:\61sOpenClaw"）
