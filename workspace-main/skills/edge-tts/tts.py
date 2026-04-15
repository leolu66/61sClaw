#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge TTS 语音生成脚本
使用微软 Edge 浏览器的在线 TTS 服务（免费）
"""

import asyncio
import argparse
import os
import sys
import json
import tempfile
from pathlib import Path

# 默认声音
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

# 常用中文声音
CHINESE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 晓晓，女声，温柔自然
    "yunxi": "zh-CN-YunxiNeural",            # 云希，男声，年轻活泼
    "yunjian": "zh-CN-YunjianNeural",        # 云健，男声，沉稳专业
    "xiaoyi": "zh-CN-XiaoyiNeural",          # 晓伊，女声，甜美可爱
    "yunyang": "zh-CN-YunyangNeural",        # 云扬，男声，新闻播报
}

# 常用英文声音
ENGLISH_VOICES = {
    "aria": "en-US-AriaNeural",              # Aria，女声
    "guy": "en-US-GuyNeural",                # Guy，男声
    "sonia": "en-GB-SoniaNeural",            # Sonia，女声（英式）
}


def get_voice_id(voice_name: str) -> str:
    """获取声音 ID"""
    voice_lower = voice_name.lower()
    if voice_lower in CHINESE_VOICES:
        return CHINESE_VOICES[voice_lower]
    if voice_lower in ENGLISH_VOICES:
        return ENGLISH_VOICES[voice_lower]
    # 如果传入的是完整 ID，直接返回
    return voice_name


async def text_to_speech(text: str, voice: str, output_path: str = None) -> str:
    """使用 edge-tts 生成语音"""
    try:
        import edge_tts
    except ImportError:
        raise ImportError("请先安装 edge-tts: pip install edge-tts")
    
    communicate = edge_tts.Communicate(text, voice)
    
    if output_path:
        await communicate.save(output_path)
        return output_path
    else:
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        await communicate.save(tmp_path)
        return tmp_path


def play_audio(file_path: str):
    """播放音频文件（跨平台）"""
    import platform
    import subprocess
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows 使用默认播放器
            os.startfile(file_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["afplay", file_path], check=True)
        else:  # Linux
            # 尝试多种播放器
            for player in ["mpg123", "ffplay", "cvlc"]:
                try:
                    if player == "ffplay":
                        subprocess.run([player, "-nodisp", "-autoexit", file_path], 
                                     check=True, capture_output=True)
                    else:
                        subprocess.run([player, file_path], check=True, capture_output=True)
                    break
                except:
                    continue
    except Exception as e:
        print(f"播放音频失败: {e}", file=sys.stderr)
        print(f"音频已保存到: {file_path}", file=sys.stderr)


async def list_voices():
    """列出所有可用声音"""
    try:
        import edge_tts
    except ImportError:
        print("请先安装 edge-tts: pip install edge-tts")
        return
    
    voices = await edge_tts.list_voices()
    
    # 筛选中文和英文声音
    zh_voices = [v for v in voices if v["Locale"].startswith("zh-")]
    en_voices = [v for v in voices if v["Locale"].startswith("en-")]
    
    print("中文声音:")
    for v in zh_voices[:10]:  # 只显示前10个
        print(f"  {v['ShortName']} - {v['FriendlyName']}")
    
    print("\n英文声音:")
    for v in en_voices[:10]:  # 只显示前10个
        print(f"  {v['ShortName']} - {v['FriendlyName']}")


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="Edge TTS 语音生成")
    parser.add_argument("text", nargs="?", help="要转换的文字")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="声音名称或 ID")
    parser.add_argument("--output", "-o", help="输出文件路径（默认自动播放）")
    parser.add_argument("--list-voices", action="store_true", help="列出可用声音")
    
    args = parser.parse_args()
    
    # 列出可用声音
    if args.list_voices:
        await list_voices()
        return
    
    # 检查参数
    if not args.text:
        parser.print_help()
        sys.exit(1)
    
    try:
        # 获取声音 ID
        voice_id = get_voice_id(args.voice)
        
        print(f"正在生成语音...")
        print(f"  文字: {args.text}")
        print(f"  声音: {voice_id}")
        
        # 生成语音
        if args.output:
            output_path = await text_to_speech(args.text, voice_id, args.output)
            print(f"✓ 语音已保存到: {output_path}")
        else:
            output_path = await text_to_speech(args.text, voice_id)
            print(f"✓ 语音生成完成，正在播放...")
            play_audio(output_path)
            
            # 清理临时文件
            try:
                os.unlink(output_path)
            except:
                pass
        
    except ImportError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """主函数入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
