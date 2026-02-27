# 七牛云同步 Skill

将本地workspace内容同步到七牛云存储空间61sopenclaw。

## 功能
- 将skills同步到七牛云 /skills 目录
- 将memory（记忆/日志）同步到七牛云 /logs 目录
- 将数据文件同步到七牛云 /data 目录
- 其他文件同步到根目录

## 使用方法
- "共享到云上"、"同步到七牛云"、"七牛云同步"

## 同步规则
| 本地目录/文件 | 七牛云目录 |
|--------------|-----------|
| skills/ | /skills |
| memory/ | /logs |
| *.db | /data |
| 其他 | / |

## 配置
在 scripts/config.json 中设置：
- workspace_path: 本地工作目录路径
