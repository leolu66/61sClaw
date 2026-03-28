#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows TTS 语音生成脚本
使用 Windows 系统自带的 SAPI5 语音合成引擎
"""

import argparse
import os
import sys
import json
from pathlib import Path


def get_sapi_voices():
    """获取所有可用的 SAPI5 声音"""
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        voices = speaker.GetVoices()
        
        voice_list = []
        for i in range(voices.Count):
            voice = voices.Item(i)
            voice_list.append({
                "name": voice.GetAttribute("Name"),
                "id": i,
                "gender": voice.GetAttribute("Gender"),
                "language": voice.GetAttribute("Language"),
            })
        return voice_list
    except Exception as e:
        print(f"获取声音列表失败: {e}", file=sys.stderr)
        return []


def list_voices():
    """列出所有可用声音"""
    voices = get_sapi_voices()
    if not voices:
        print("没有找到可用的声音")
        return
    
    print("可用声音列表:")
    print("-" * 50)
    
    # 分类显示
    zh_voices = [v for v in voices if "Chinese" in v["language"] or "中文" in v["name"]]
    en_voices = [v for v in voices if "English" in v["language"]]
    other_voices = [v for v in voices if v not in zh_voices and v not in en_voices]
    
    if zh_voices:
        print("\n中文声音:")
        for v in zh_voices:
            print(f"  {v['name']} ({v['gender']})")
    
    if en_voices:
        print("\n英文声音:")
        for v in en_voices:
            print(f"  {v['name']} ({v['gender']})")
    
    if other_voices:
        print("\n其他声音:")
        for v in other_voices:
            print(f"  {v['name']} - {v['language']} ({v['gender']})")


def speak_text(text: str, voice_name: str = None, rate: int = 0, volume: int = 100):
    """使用 SAPI5 朗读文字"""
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # 设置语速 (-10 到 10)
        speaker.Rate = max(-10, min(10, rate))
        
        # 设置音量 (0 到 100)
        speaker.Volume = max(0, min(100, volume))
        
        # 设置声音
        if voice_name:
            voices = speaker.GetVoices()
            for i in range(voices.Count):
                voice = voices.Item(i)
                if voice_name.lower() in voice.GetAttribute("Name").lower():
                    speaker.Voice = voice
                    break
        
        # 朗读
        speaker.Speak(text)
        return True
        
    except Exception as e:
        raise Exception(f"语音合成失败: {e}")


def save_to_wav(text: str, output_path: str, voice_name: str = None, rate: int = 0, volume: int = 100):
    """将文字保存为 WAV 音频文件"""
    try:
        import win32com.client
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建 SAPI 语音对象
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # 创建文件流
        file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
        file_stream.Open(output_path, 3)  # 3 = SSFMCreateForWrite
        
        # 设置输出到文件
        speaker.AudioOutputStream = file_stream
        
        # 设置语速和音量
        speaker.Rate = max(-10, min(10, rate))
        speaker.Volume = max(0, min(100, volume))
        
        # 设置声音
        if voice_name:
            voices = speaker.GetVoices()
            for i in range(voices.Count):
                voice = voices.Item(i)
                if voice_name.lower() in voice.GetAttribute("Name").lower():
                    speaker.Voice = voice
                    break
        
        # 合成语音到文件
        speaker.Speak(text)
        
        # 关闭文件流
        file_stream.Close()
        
        return output_path
        
    except Exception as e:
        raise Exception(f"保存音频失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="Windows TTS 语音生成")
    parser.add_argument("text", nargs="?", help="要转换的文字")
    parser.add_argument("--voice", help="声音名称")
    parser.add_argument("--rate", type=int, default=0, help="语速 (-10 到 10, 默认 0)")
    parser.add_argument("--volume", type=int, default=100, help="音量 (0 到 100, 默认 100)")
    parser.add_argument("--output", "-o", help="输出为 WAV 文件")
    parser.add_argument("--list-voices", action="store_true", help="列出可用声音")
    
    args = parser.parse_args()
    
    # 列出可用声音
    if args.list_voices:
        list_voices()
        return
    
    # 检查参数
    if not args.text:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.output:
            # 保存到文件
            output_path = save_to_wav(
                args.text, 
                args.output, 
                args.voice, 
                args.rate, 
                args.volume
            )
            print(f"✓ 语音已保存到: {output_path}")
        else:
            # 直接播放
            print(f"正在朗读: {args.text}")
            if args.voice:
                print(f"  声音: {args.voice}")
            speak_text(args.text, args.voice, args.rate, args.volume)
            print("✓ 朗读完成")
        
    except ImportError:
        print("错误: 缺少 pywin32 模块", file=sys.stderr)
        print("请安装: pip install pywin32", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
