#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge TTS 技能入口
通过 OpenClaw 工具调用
"""

import asyncio
import json
import sys
import os
import tempfile

# 添加脚本所在目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tts import text_to_speech, get_voice_id, play_audio, DEFAULT_VOICE


async def main_async():
    """异步主函数 - 处理 OpenClaw 传入的参数"""
    try:
        # 检查 edge-tts 是否安装
        try:
            import edge_tts
        except ImportError:
            result = {
                "success": False,
                "error": "未安装 edge-tts",
                "message": "请先安装依赖: pip install edge-tts"
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
        voice = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_VOICE
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        # 获取声音 ID
        voice_id = get_voice_id(voice)
        
        # 生成语音
        if output_file:
            output_path = await text_to_speech(text, voice_id, output_file)
            result = {
                "success": True,
                "message": f"语音已保存到: {output_path}",
                "file_path": output_path,
                "text": text,
                "voice": voice_id
            }
        else:
            # 保存到临时文件并播放
            output_path = await text_to_speech(text, voice_id)
            
            # 播放音频
            play_audio(output_path)
            
            # 清理临时文件
            try:
                os.unlink(output_path)
            except:
                pass
            
            result = {
                "success": True,
                "message": "语音生成并播放完成",
                "text": text,
                "voice": voice_id
            }
        
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "message": f"生成语音失败: {e}"
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)


def main():
    """主函数入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
