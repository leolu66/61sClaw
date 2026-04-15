#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Recommender - 模型推荐脚本
根据价格、场景推荐最合适的模型
"""

import json
import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 数据文件路径
DATA_FILE = "C:/Users/luzhe/.openclaw/workspace-main/skills/model-recommender/models-capabilities.json"

def load_models():
    """加载模型数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """主函数"""
    data = load_models()
    models = sorted(data['models'], key=lambda x: x['position'])
    
    print("="*90)
    print("💰 模型价格排行榜（完整版）")
    print("="*90)
    print()
    
    print(f"{'排名':<8} {'模型':<30} {'价格 (I/O)':<16} {'上下文':<10} {'特点':<30}")
    print("-"*90)
    
    for m in models:
        badge = m.get('badge', '•')
        price = f"¥{m['input']} / ¥{m['output']}"
        tags = ', '.join(m['tags'])
        print(f"{badge:<8} {m['name']:<30} {price:<16} {m['context']:<10} {tags:<30}")
    
    print()
    print("="*90)
    print("📊 按场景推荐")
    print("="*90)
    print()
    
    print("| 场景 | 首选 | 备选 | 高端 |")
    print("|------|------|------|------|")
    print("| 日常对话 | Doubao-Mini | QWen-Flash | - |")
    print("| 编程开发 | MiniMax-M2.5 | GLM-5 | Claude-Sonnet |")
    print("| 长文档 | QWen-Plus | QWen-Max | - |")
    print("| 视觉理解 | Doubao-Vision-Pro | Doubao-Vision-Lite | - |")
    print("| 性价比 | QWen-Flash | Doubao-Lite | - |")
    
    print()
    print("="*90)
    print("🎯 当前模型")
    print("="*90)
    print()
    print("当前使用：**QWen-Plus**")
    print()
    print("特点：")
    print("- 1M 超长上下文，适合处理长文档")
    print("- 支持多模态（图像 + 文本）")
    print("- 价格适中：¥2 / ¥12")
    print()

if __name__ == "__main__":
    main()
