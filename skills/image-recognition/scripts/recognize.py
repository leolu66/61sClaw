#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像识别技能 - 场景判断模块
主 Agent 调用此脚本判断识别场景，然后直接使用视觉能力分析图片
"""

import json
import sys
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def detect_scene(user_text: str, config: dict) -> str:
    """
    根据用户文本判断识别场景
    
    Args:
        user_text: 用户的指令文本
        config: 配置对象
    
    Returns:
        场景名称: ocr / object / ppt
    """
    text = user_text.lower()
    scenes = config.get("scenes", {})
    
    # 计算每个场景的匹配分数
    scores = {}
    for scene_key, scene_config in scenes.items():
        keywords = scene_config.get("keywords", [])
        score = sum(1 for keyword in keywords if keyword.lower() in text)
        scores[scene_key] = score
    
    # 返回得分最高的场景，如果没有匹配则返回 object（通用识别）
    if scores:
        best_scene = max(scores, key=scores.get)
        if scores[best_scene] > 0:
            return best_scene
    
    return "object"  # 默认使用物体识别

def get_scene_prompt(scene: str, config: dict) -> str:
    """获取场景对应的提示词"""
    scenes = config.get("scenes", {})
    scene_config = scenes.get(scene, {})
    return scene_config.get("prompt", "请描述图片内容")

def get_scene_name(scene: str, config: dict) -> str:
    """获取场景的中文名称"""
    scenes = config.get("scenes", {})
    scene_config = scenes.get(scene, {})
    return scene_config.get("name", "通用识别")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python recognize.py '<用户指令>'")
        sys.exit(1)
    
    user_text = sys.argv[1]
    
    try:
        config = load_config()
        scene = detect_scene(user_text, config)
        prompt = get_scene_prompt(scene, config)
        scene_name = get_scene_name(scene, config)
        
        result = {
            "scene": scene,
            "scene_name": scene_name,
            "prompt": prompt
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "scene": "object",
            "scene_name": "通用识别",
            "prompt": "请描述图片内容"
        }, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
