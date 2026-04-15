---
name: imagemagick-cli
description: |
  使用 ImageMagick CLI 命令处理图片，支持格式转换、尺寸调整、裁剪、压缩、旋转、添加水印等功能。
  当用户说"转换图片格式"、"调整图片大小"、"压缩图片"、"裁剪图片"、"旋转图片"、
  "添加水印"、"批量处理图片"时使用此技能。
---

# ImageMagick CLI 技能

使用 ImageMagick 命令行工具处理图片，支持常见图片操作。

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "转换图片格式"
- "调整图片大小"
- "压缩图片"
- "裁剪图片"
- "旋转图片"
- "添加水印"
- "批量处理图片"
- "imagemagick"

### 功能描述
通过调用 ImageMagick CLI 命令（magick/convert）实现图片处理功能：
- 格式转换（PNG/JPG/WebP/GIF/BMP/TIFF 等）
- 尺寸调整（缩放、固定宽高、等比缩放）
- 图片裁剪（指定区域、居中裁剪）
- 质量压缩（调整压缩率）
- 图片旋转（任意角度）
- 添加水印（文字/图片水印）
- 批量处理（目录内批量转换）

### 输入/输出
- **输入**: 图片文件路径或目录路径
- **输出**: 处理后的图片文件（默认保存到原目录或指定输出目录）

### 依赖条件
- ImageMagick 已安装（默认路径：`D:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe`）
- 支持 Windows PowerShell 环境

### 边界情况
- 文件不存在时返回错误提示
- 输出目录不存在时自动创建
- 批量处理时跳过非图片文件
- 同名文件默认覆盖（可通过参数控制）

---

## 使用方法

### 1. 格式转换

```bash
python scripts/convert.py input.png output.jpg
```

### 2. 调整尺寸

```bash
# 等比缩放，最大宽度 800px
python scripts/resize.py input.jpg output.jpg --width 800

# 等比缩放，最大高度 600px
python scripts/resize.py input.jpg output.jpg --height 600

# 固定尺寸（可能变形）
python scripts/resize.py input.jpg output.jpg --width 800 --height 600 --exact

# 按百分比缩放
python scripts/resize.py input.jpg output.jpg --percent 50
```

### 3. 裁剪图片

```bash
# 从坐标 (100, 100) 开始裁剪 300x200 区域
python scripts/crop.py input.jpg output.jpg --x 100 --y 100 --width 300 --height 200

# 居中裁剪 800x600 区域
python scripts/crop.py input.jpg output.jpg --width 800 --height 600 --center
```

### 4. 压缩图片

```bash
# JPEG 质量设为 80%（默认 90）
python scripts/compress.py input.jpg output.jpg --quality 80

# WebP 格式压缩
python scripts/compress.py input.png output.webp --quality 85
```

### 5. 旋转图片

```bash
# 顺时针旋转 90 度
python scripts/rotate.py input.jpg output.jpg --angle 90

# 逆时针旋转 45 度
python scripts/rotate.py input.jpg output.jpg --angle -45
```

### 6. 添加文字水印

```bash
# 右下角添加文字水印
python scripts/watermark.py input.jpg output.jpg --text "Copyright 2026" --position southeast

# 自定义字体大小和颜色
python scripts/watermark.py input.jpg output.jpg --text "Sample" --position center --fontsize 48 --color "rgba(255,255,255,0.5)"
```

### 7. 批量处理

```bash
# 批量转换目录内所有 PNG 为 JPG
python scripts/batch.py --input-dir ./images --output-dir ./output --format jpg

# 批量调整尺寸
python scripts/batch.py --input-dir ./images --output-dir ./output --resize --width 800

# 批量压缩
python scripts/batch.py --input-dir ./images --output-dir ./output --compress --quality 80
```

---

## 配置说明

配置文件路径：`scripts/config.json`

```json
{
  "imagemagick_path": "D:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe",
  "default_quality": 90,
  "default_format": "jpg"
}
```

如果 ImageMagick 安装在其他位置，修改 `imagemagick_path` 配置项。

---

## 相关文件

- `scripts/convert.py` - 格式转换
- `scripts/resize.py` - 尺寸调整
- `scripts/crop.py` - 图片裁剪
- `scripts/compress.py` - 质量压缩
- `scripts/rotate.py` - 图片旋转
- `scripts/watermark.py` - 添加水印
- `scripts/batch.py` - 批量处理
- `scripts/config.json` - 配置文件
- `scripts/utils.py` - 公共工具函数

---

## 注意事项

- 默认使用 ImageMagick 7 的 `magick` 命令，如果安装的是旧版本（使用 `convert`），请修改配置
- 批量处理时建议先测试单张图片效果
- 大尺寸图片处理可能需要较长时间
- 文字水印需要系统安装对应字体

---

## DoD 检查表

**开发日期**: 2026-04-11
**开发者**: 小天才

### 1. SRS 文档
- [x] 触发条件明确
- [x] 功能描述完整
- [x] 输入输出说明
- [x] 依赖条件列出
- [x] 边界情况处理

### 2. 技能文件和代码
- [x] 目录结构规范
- [x] 使用相对路径
- [x] 配置外置
- [x] 无 .skill 文件

### 3. 测试通过
- [x] 功能测试通过
- [x] 触发测试通过

### 4. GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露

**状态**: ✅ 完成
