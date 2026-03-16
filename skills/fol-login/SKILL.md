---
name: fol-login
description: |
  自动登录公司财务报销系统（FOL）。
  访问 https://fol.iwhalecloud.com/，检测登录状态，如需登录则自动填入凭据。
  当用户说"登录报销系统"、"打开FOL"、"财务报销"时触发。
triggers:
  - "登录报销系统"
  - "打开FOL"
  - "打开fol"
  - "财务报销"
  - "报销系统"
version: 1.0
---

# FOL 财务报销系统登录

自动登录公司财务报销系统。

## 触发方式

- "登录报销系统"
- "打开FOL"
- "财务报销"
- "报销系统"

## 功能

1. 访问 https://fol.iwhalecloud.com/
2. 检测登录状态（检查是否存在登录表单）
3. 如未登录，自动填入工号密码并登录
4. 如已登录，直接进入主页

## 使用方式

```bash
# 登录财务报销系统
python ~/.openclaw/workspace-main/skills/fol-login/login.py
```

## 凭据来源

- 工号：从公司邮箱地址提取（0027025600）
- 密码：从密码箱（vault）获取公司邮箱密码

## 登录流程

1. 打开浏览器访问 FOL 系统
2. 检测是否为登录页面（检查"财务在线"标题和工号输入框）
3. 填写工号（input[placeholder*="工号"]）
4. 填写密码（#edt_pwd）
5. 点击"登录财务在线"按钮
6. 等待 SSO 跳转完成
7. 进入 FOL 主页

## 技术实现

- 使用 Playwright 进行浏览器自动化
- 支持 Chrome/Edge 浏览器
- 自动检测登录状态
- 从 vault 安全获取密码

## 注意事项

- 需要安装 Playwright: `pip install playwright && playwright install chromium`
- 浏览器保持打开状态，需手动关闭
- 如已登录过，会自动跳过登录步骤