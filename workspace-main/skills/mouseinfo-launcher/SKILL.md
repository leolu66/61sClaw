---
name: mouseinfo-launcher
description: 启动 mouseinfo 工具获取鼠标坐标和屏幕颜色。当用户说"启动mouseinfo"、"打开mouseinfo"、"mouseinfo"、"获取鼠标坐标"、"查看鼠标位置"、"取色器"等指令时触发此技能。mouseinfo 是一个 Python 图形界面工具，可以实时显示鼠标坐标和像素颜色。
---

# MouseInfo 启动器

## 功能

启动 mouseinfo 图形界面工具，用于：
- 实时获取鼠标指针的屏幕坐标 (X, Y)
- 获取当前像素的颜色值 (RGB)
- 方便进行 UI 自动化、截图定位等任务

## 使用方法

直接启动 mouseinfo：

```bash
python -c "import mouseinfo; mouseinfo.mouseInfo()"
```

## 说明

- 启动后会弹出一个图形窗口
- 鼠标移动时，窗口会实时显示当前坐标和颜色
- 按 F1 可以将当前坐标复制到剪贴板
- 按 F2 可以将当前颜色复制到剪贴板
- 按 F3 可以将当前坐标和颜色一起复制
- 按 Esc 退出程序

## 安装

如果未安装，先执行：
```bash
pip install mouseinfo
```
