---
name: feishu-uploader
description: |
  上传本地文件到飞书云盘，支持自动分类（src/videos/recordings/temp/appdatas/images/documents）。
  基于 lark-drive skill 实现上传下载功能。
  当用户说"上传文件到飞书"、"备份到飞书云盘"、"同步文件到飞书"、"从飞书下载文件"时触发。
triggers:
  - "上传文件到飞书"
  - "备份到飞书云盘"
  - "同步文件到飞书"
  - "从飞书下载文件"
  - "飞书上传"
  - "飞书下载"
---

# 飞书云盘文件上传工具

自动将本地文件上传到飞书云盘，按文件类型智能分类存放。

**基于 lark-drive skill 实现** - 使用 `lark-cli drive +upload` 和 `+download` 命令。

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

### 1. 扫描并上传目录

```bash
# 扫描目录
python feishu_uploader.py E:\feishudoc

# 上传（基于扫描结果）
python upload_to_feishu.py scan_result.json
```

### 2. 上传到指定文件夹

```bash
# 上传到指定的飞书文件夹
python upload_to_feishu.py scan_result.json fldbc_xxxxxxxx
```

### 3. 下载文件

```bash
# 通过 file_token 下载
python download_from_feishu.py boxbc_xxx ./downloads/file.pdf

# 通过 URL 下载
python download_from_feishu.py --url "https://xxx.feishu.cn/drive/file/boxbc_xxx" ./downloads/file.pdf
```

## 前置条件

1. **安装 lark-cli 和 lark-drive skill**:
   ```bash
   npm install -g @larksuite/cli
   npx skills add larksuite/cli -y -g
   ```

2. **完成飞书认证**:
   ```bash
   lark-cli config init --new
   lark-cli auth login --recommend
   ```

## 文件说明

| 文件 | 功能 |
|------|------|
| `feishu_uploader.py` | 文件分类扫描器 |
| `upload_to_feishu.py` | 上传实现（调用 lark-drive +upload） |
| `download_from_feishu.py` | 下载实现（调用 lark-drive +download） |
| `scan_result.json` | 扫描结果缓存 |

## 技术实现

### 上传流程
1. `feishu_uploader.py` 扫描本地目录，按文件类型分类
2. `upload_to_feishu.py` 调用 `lark-cli drive +upload` 上传
3. 自动创建分类文件夹（如果不存在）

### 下载流程
1. `download_from_feishu.py` 调用 `lark-cli drive +download`
2. 支持 file_token 和 URL 两种方式

## 依赖

- Python 3.6+
- lark-cli (已安装 lark-drive skill)
- 飞书应用认证完成

## 权限要求

- `drive:drive:read` - 读取云盘
- `drive:file:read` - 读取文件
- `drive:file:write` - 上传文件
