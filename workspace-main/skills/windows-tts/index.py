#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows TTS 技能入口
通过 OpenClaw 工具调用
"""

import json
import sys
import os

# 添加脚本所在目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tts import speak_text, save_to_wav, get_sapi_voices


def main():
    """主函数 - 处理 OpenClaw 传入的参数"""
    try:
        # 检查 pywin32 是否安装
        try:
            import win32com.client
        except ImportError:
            result = {
                "success": False,
                "error": "未安装 pywin32",
                "message": "请先安装依赖: pip install pywin32"
            }
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)
        
        # 从命令行参数获取输入
        if len(sys.argv) < 2:
            result = {
                "success": False,
                "error": "缺少参数",
                "message": "请提供要转换的文字"
            }
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)
        
        # 解析参数
        text = sys.argv[1]
        voice_name = sys.argv[2] if len(sys.argv) > 2 else None
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        # 执行 TTS
        if output_file:
            # 保存到文件
            output_path = save_to_wav(text, output_file, voice_name)
            result = {
                "success": True,
                "message": f"语音已保存到: {output_path}",
                "file_path": output_path,
                "text": text,
                "voice": voice_name or "default"
            }
        else:
            # 直接播放
            speak_text(text, voice_name)
            result = {
                "success": True,
                "message": "语音播放完成",
                "text": text,
                "voice": voice_name or "default"
            }
        
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "message": f"语音合成失败: {e}"
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
