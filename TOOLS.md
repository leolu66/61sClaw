# TOOLS.md - Local Notes

## 日志目录
- **根目录**: logs/（相对于 workspace-main）
  - daily/     # 每日会话总结
  - tasks/     # 任务执行日志
  - errors/    # 错误反思记录
  - summary/   # 阶段性总结

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## ⚠️ 重要教训（别再犯错！）

### Git 分支问题

**默认分支是 `main`，不是 `master`！**

- ✅ 推送前检查：`git branch` 确认当前分支
- ✅ 推送到 main：`git push origin main` 或确保 master 跟踪 main
- ✅ 已配置：`git config push.default upstream`
- ❌ 不要再推到 master 让文件"消失"了！

**历史错误：**
- 2026-03-01: api-balance-checker 和 todo-manager 推到 master，GitHub 默认显示 main，导致用户看不到文件
