---
name: feishu-uploader
description: 上传本地文件到飞书云盘，支持自动分类（src/videos/recordings/temp/appdatas/images/documents）。当用户说"上传文件到飞书"、"备份到飞书云盘"、"同步文件到飞书"时触发。
---

# 飞书云盘文件上传工具

自动将本地文件上传到飞书云盘，按文件类型智能分类存放。

## 文件夹结构

| 文件夹 | 用途 | 存放文件类型 |
|--------|------|-------------|
| `src` | 源代码 | .py, .js, .java, .cpp, .h, .html, .css, .json, .xml, .yaml, .yml, .sql, .sh, .bat, .ps1 |
| `videos` | 视频 | .mp4, .avi, .mov, .wmv, .flv, .mkv, .webm, .m4v, .3gp |
| `recordings` | 录音 | .mp3, .wav, .wma, .aac, .ogg, .flac, .m4a, .opus, .amr |
| `images` | 图片 | .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg, .ico, .tiff, .raw, .heic |
| `documents` | 文档 | .doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf, .txt, .md, .csv, .rtf, .odt, .ods, .odp |
| `appdatas` | 应用数据 | .db, .sqlite, .log, .cache, .config, .ini, .properties, .env |
| `temp` | 临时文件 | 其他未分类文件 |

## 使用方法

### 上传单个文件
```
上传文件 E:\feishudoc\report.pdf 到飞书
```

### 上传整个目录
```
上传目录 E:\feishudoc 到飞书云盘
```

### 按类型上传
```
上传 E:\feishudoc 的所有图片到飞书
上传 E:\feishudoc 的所有文档到飞书
```

## 技术实现

使用飞书 OpenAPI 的文件上传接口：
1. 获取文件夹 token（如果不存在则创建）
2. 分片上传大文件（>20MB）
3. 支持断点续传
4. 自动重试机制

## 配置

需要以下飞书权限：
- `drive:file` - 访问云盘
- `drive:file:upload` - 上传文件
- `drive:file:readonly` - 读取文件列表
