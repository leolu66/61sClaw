# 2026-03-26 工作日志

## 任务概述
- **时间**: 2026-03-26 13:20 - 19:10
- **主要工作**: 飞书插件问题排查与文件上传技能开发

## 完成的工作

### 1. OpenClaw 启动问题排查
- **问题**: 启动时报错 `Cannot find module 'openclaw/plugin-sdk/channel-config-schema'`
- **原因**: `openclaw-weixin` 插件缺少 `openclaw` 依赖
- **解决**: 执行 `npm link openclaw` 建立符号链接
- **结果**: 插件加载成功，微信渠道正常工作

### 2. 飞书插件重复注册问题分析
- **现象**: 日志中飞书工具被重复注册多次
- **原因**: 配置了 2 个飞书账号（default + openclawd），每个账号独立注册工具
- **结论**: 这是预期行为，不是 bug

### 3. 飞书云盘文件上传技能开发
- **创建技能**: `feishu-uploader`
- **功能**:
  - 自动扫描本地目录并按类型分类（src/videos/recordings/images/documents/appdatas/temp）
  - 调用飞书 OpenAPI 上传文件
  - 支持自动创建文件夹和指定目标文件夹
- **技术实现**:
  - 使用 `tenant_access_token` 认证
  - 调用 `/drive/v1/files/upload_all` 接口上传
  - 支持小文件（<20MB）直接上传
- **测试结果**: 成功上传多个测试文件到飞书云盘

### 4. 飞书文件下载测试
- 验证了只要有 `access_token` 和 `file_token` 就可以下载文件
- 测试了应用上传的文件和用户手动上传的文件，都能成功下载
- **结论**: `file_token` 是文件的唯一标识，与所有者无关

## 遇到的问题

### 问题1: 文件夹创建失败
- **错误**: `field validation failed`，`folder_token is required`
- **解决**: 必须先获取根目录 token，然后作为 `folder_token` 参数创建子文件夹

### 问题2: 文件上传参数错误
- **错误**: `params error`，缺少 `size` 参数
- **解决**: 添加 `size` 参数（文件大小，字节）

### 问题3: 文件所有者隔离
- **现象**: 应用上传的文件在飞书网页版看不到
- **原因**: 应用上传的文件归应用所有，与用户文件隔离
- **解决**: 应用自动共享给用户，或用户手动查看"应用文件"

## 经验总结

1. **飞书 API 规范**: 严格按照官方 API 文档传参，注意必填字段
2. **权限管理**: 飞书云盘文件有严格的所有者隔离机制
3. **Token 机制**: `file_token` 是文件的唯一标识，可用于下载和分享
4. **技能开发**: 使用 Python 脚本 + OpenClaw 工具组合，快速实现自动化

## 新增文件
- `skills/feishu-uploader/SKILL.md`
- `skills/feishu-uploader/feishu_uploader.py`
- `skills/feishu-uploader/upload_to_feishu.py`
- `skills/feishu-uploader/test_download.py`
- `skills/feishu-uploader/config.json`

## Git 提交
- 待提交: 新增 feishu-uploader 技能及相关文件
