#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ElevenLabs TTS 技能入口
通过 OpenClaw 工具调用
"""

import json
import sys
import os

# 添加脚本所在目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tts import text_to_speech, get_first_available_voice, save_audio, play_audio, API_KEY, DEFAULT_MODEL, get_voices


def main():
    """主函数 - 处理 OpenClaw 传入的参数"""
    try:
        # 检查 API Key
        if not API_KEY:
            result = {
                "success": False,
                "error": "未设置 ELEVENLABS_API_KEY 环境变量",
                "message": "请先设置环境变量: $env:ELEVENLABS_API_KEY='your-api-key'"
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
        voice_id = sys.argv[2] if len(sys.argv) > 2 else None
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        # 如果没有指定声音，获取第一个可用声音
        if not voice_id:
            voice_id = get_first_available_voice()
            if not voice_id:
                result = {
                    "success": False,
                    "error": "没有找到可用的声音",
                    "message": "请先创建声音，免费用户只能使用自己创建的声音"
                }
                print(json.dumps(result, ensure_ascii=False))
                sys.exit(1)
        
        # 生成语音
        audio_data = text_to_speech(text, voice_id, DEFAULT_MODEL)
        
        # 处理输出
        if output_file:
            output_path = save_audio(audio_data, output_file)
            result = {
                "success": True,
                "message": f"语音已保存到: {output_path}",
                "file_path": output_path,
                "text": text,
                "voice": voice_id
            }
        else:
            # 保存到临时文件并播放
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            # 播放音频
            play_audio(tmp_path)
            
            # 清理临时文件
            try:
                os.unlink(tmp_path)
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


if __name__ == "__main__":
    main()
