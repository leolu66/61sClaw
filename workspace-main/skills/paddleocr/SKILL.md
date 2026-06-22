---
name: "paddleocr"
description: "本地PaddleOCR文字识别(PP-OCRv6)。支持图片/PDF OCR、表格识别、版面分析、公式识别。触发词：OCR、文字识别。"
---

# PaddleOCR - 本地文字识别

基于百度飞桨 PaddleOCR 3.7.0 + PP-OCRv6 Medium 模型的本地 OCR 引擎。

## ⛔ 必读规则

1. **首次使用会有模型下载**：PaddleOCR 首次调用会自动从 ModelScope 下载模型到 `~/.paddlex/official_models/`，需等待数分钟
2. **环境变量加速启动**：设置 `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` 可跳过联网检查
3. **GPU 不可用则 CPU**：当前环境无 GPU，自动使用 CPU 推理
4. **大图处理**：图片分辨率过高时可能 OOM，建议先告知用户预计耗时
5. **结果直接展示**：OCR 结果以可读格式展示，不输出原始 JSON 除非用户要求

## 环境信息

```
Python: 3.12.3
PaddlePaddle: 3.3.1
PaddleOCR: 3.7.0
默认模型: PP-OCRv6_medium_det + PP-OCRv6_medium_rec
模型缓存: ~/.paddlex/official_models/
```

## 使用方式

### 方式 A：命令行（单图快速 OCR）

```bash
paddleocr --image_path "<图片路径>" --output <输出目录>
```

常用参数:
- `--image_path`: 图片文件或目录路径
- `--output`: 输出结果保存目录
- `--use_gpu`: 是否使用 GPU（默认 false）

### 方式 B：Python 脚本（灵活控制）

```python
from paddlex import create_pipeline

# 创建 OCR pipeline
pipeline = create_pipeline('OCR')

# 预测
output = pipeline.predict(
    input="<图片路径>",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
)

# 遍历结果
for res in output:
    res.print()
    res.save_to_img(save_path="./output")
```

输出字段:
- `res.text`: 识别到的文本内容
- `res.rec_texts`: 按行识别的文本列表
- `res.dt_polys`: 文本框坐标列表
- `res.rec_scores`: 每行置信度

### 方式 C：Python 脚本（自定义模型）

```python
from paddlex import create_pipeline

# 使用 Tiny 模型（轻量快速）
pipeline = create_pipeline('OCR', 
    det_model_name="PP-OCRv6_tiny_det",
    rec_model_name="PP-OCRv6_tiny_rec"
)

# 仅检测不识别
pipeline = create_pipeline('OCR', det_model_name="PP-OCRv6_medium_det", rec_model_name=None)

# 仅识别（需要预先裁切好的文字行图片）
pipeline = create_pipeline('OCR', det_model_name=None, rec_model_name="PP-OCRv6_medium_rec")
```

### 可用模型列表

| 模型 | 类型 | 大小 | 说明 |
|------|------|------|------|
| PP-OCRv6_tiny_det | 检测 | 1.5M | Tiny 文字检测 |
| PP-OCRv6_small_det | 检测 | 7.7M | Small 文字检测 |
| PP-OCRv6_medium_det | 检测 | 34.5M | Medium 文字检测（默认） |
| PP-OCRv6_tiny_rec | 识别 | ~2.5M | Tiny 文字识别 |
| PP-OCRv6_small_rec | 识别 | ~8M | Small 文字识别 |
| PP-OCRv6_medium_rec | 识别 | ~20M | Medium 文字识别（默认） |

### 高级功能

#### 1. 版面分析（PP-StructureV3）

```python
pipeline = create_pipeline('PP-StructureV3')
output = pipeline.predict(input="<图片路径>")
for res in output:
    res.print()
    res.save_to_markdown(save_path="./output")
```

支持: 文字、表格、图片、公式区域检测与结构化输出。

#### 2. 文档解析（PaddleOCR-VL）

```python
pipeline = create_pipeline('PaddleOCR-VL')
output = pipeline.predict(input="<图片路径>")
for res in output:
    res.print()
```

#### 3. 表格识别

版面分析后表格自动提取为 HTML/Markdown 格式。

#### 4. 文档方向校正

```python
output = pipeline.predict(
    input="<图片路径>",
    use_doc_orientation_classify=True,  # 自动旋转倒置图片
    use_doc_unwarping=True,             # 自动展平弯曲文档
)
```

## 操作流程

### 场景：用户要求 OCR 识别图片

1. 确认图片路径（支持 png/jpg/jpeg/bmp/webp/tiff/pdf）
2. 运行 `paddleocr --image_path "<path>"` 或 Python 脚本
3. 解析输出，以整洁格式展示结果
4. 告知用户置信度低的区域（如有）

### 场景：用户要求提取表格

1. 使用 PP-StructureV3 pipeline
2. 结果以 Markdown 表格形式展示

### 场景：用户要求提取 PDF 文字

1. 先检查 PDF 是否为扫描件
2. 扫描件直接 OCR；文字型 PDF 建议用 markitdown 更高效
3. 告知用户：多页 PDF 逐页处理，可能较慢

## 错误处理

| 错误 | 含义 | 处理 |
|------|------|------|
| `ModuleNotFoundError: paddle` | PaddlePaddle 未安装 | `pip install paddlepaddle` |
| `Model not found` | 模型未下载 | 等待自动下载或手动下载 |
| `CUDA error` | GPU 不可用 | 自动回退 CPU |
| `OOM` | 图片过大 | 建议缩小图片后重试 |
| 识别结果乱码 | 图片方向错误 | 启用 `use_doc_orientation_classify=True` |

## 性能参考

- Medium 模型 CPU 推理: 单图 ~2-5 秒（视图片大小）
- Tiny 模型 CPU 推理: 单图 ~0.5-1 秒
- 支持 50+ 语言（中/英/日/拉丁语系等）
