#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ElevenLabs TTS 语音生成脚本
"""

import argparse
import os
import sys
import json
import requests
from pathlib import Path

# ElevenLabs API 配置
API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
BASE_URL = "https://api.elevenlabs.io/v1"

# 默认模型
DEFAULT_MODEL = "eleven_multilingual_v2"


def get_voices():
    """获取用户可用的声音列表"""
    if not API_KEY:
        return []
    
    url = f"{BASE_URL}/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": API_KEY,
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("voices", [])
    
    return []


def get_first_available_voice():
    """获取第一个可用的声音"""
    voices = get_voices()
    if voices:
        return voices[0]["voice_id"]
    return None


def text_to_speech(text: str, voice_id: str, model_id: str = DEFAULT_MODEL) -> bytes:
    """调用 ElevenLabs API 生成语音"""
    if not API_KEY:
        raise ValueError("未设置 ELEVENLABS_API_KEY 环境变量")
    
    url = f"{BASE_URL}/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,
    }
    
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
        }
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=60)
    
    if response.status_code != 200:
        error_msg = f"API 请求失败: {response.status_code}"
        try:
            error_detail = response.json()
            error_msg += f" - {error_detail.get('detail', {}).get('message', response.text)}"
        except:
            error_msg += f" - {response.text}"
        raise Exception(error_msg)
    
    return response.content


def save_audio(audio_data: bytes, output_path: str) -> str:
    """保存音频文件"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_data)
    return output_path


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
            subprocess.run(["mpg123", file_path], check=False)
            # 如果 mpg123 不可用，尝试其他播放器
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path], check=False)
    except Exception as e:
        print(f"播放音频失败: {e}", file=sys.stderr)
        print(f"音频已保存到: {file_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="ElevenLabs TTS 语音生成")
    parser.add_argument("text", nargs="?", help="要转换的文字")
    parser.add_argument("--voice", help="声音 ID（默认使用第一个可用声音）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型 ID")
    parser.add_argument("--output", "-o", help="输出文件路径（默认自动播放）")
    parser.add_argument("--list-voices", action="store_true", help="列出可用声音")
    
    args = parser.parse_args()
    
    # 列出可用声音
    if args.list_voices:
        voices = get_voices()
        if voices:
            print("可用声音列表:")
            for voice in voices:
                print(f"  {voice['name']}: {voice['voice_id']}")
        else:
            print("没有可用的声音，请先创建声音或检查 API Key")
        return
    
    # 检查参数
    if not args.text:
        parser.print_help()
        sys.exit(1)
    
    # 检查 API Key
    if not API_KEY:
        print("错误: 未设置 ELEVENLABS_API_KEY 环境变量", file=sys.stderr)
        print("请设置环境变量后再试:", file=sys.stderr)
        print('  $env:ELEVENLABS_API_KEY="your-api-key"', file=sys.stderr)
        sys.exit(1)
    
    try:
        # 获取声音 ID
        if args.voice:
            voice_id = args.voice
        else:
            voice_id = get_first_available_voice()
            if not voice_id:
                print("错误: 没有找到可用的声音", file=sys.stderr)
                print("请先创建声音或使用 --list-voices 查看可用声音", file=sys.stderr)
                sys.exit(1)
        
        print(f"正在生成语音...")
        print(f"  文字: {args.text}")
        print(f"  声音: {voice_id}")
        print(f"  模型: {args.model}")
        
        # 生成语音
        audio_data = text_to_speech(args.text, voice_id, args.model)
        
        # 保存或播放
        if args.output:
            output_path = save_audio(audio_data, args.output)
            print(f"✓ 语音已保存到: {output_path}")
        else:
            # 保存到临时文件并播放
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            print(f"✓ 语音生成完成，正在播放...")
            play_audio(tmp_path)
            
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
