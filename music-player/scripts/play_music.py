#!/usr/bin/env python3
"""
使用 PotPlayer 播放音乐文件
"""
import subprocess
import sys
import os

def play_music(file_path):
    """
    使用 PotPlayer 播放指定音乐文件
    
    Args:
        file_path: 音乐文件的完整路径
    """
    potplayer_path = r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe"
    
    # 检查 PotPlayer 是否存在
    if not os.path.exists(potplayer_path):
        print(f"错误：找不到 PotPlayer，请确认路径：{potplayer_path}")
        return False
    
    # 检查音乐文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：找不到音乐文件：{file_path}")
        return False
    
    try:
        # 使用 PotPlayer 播放音乐
        subprocess.Popen([potplayer_path, file_path], 
                        shell=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        print(f"正在播放：{file_path}")
        return True
    except Exception as e:
        print(f"播放失败：{e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python play_music.py <音乐文件路径>")
        print("示例: python play_music.py \"C:\\Users\\Music\\song.mp3\"")
        sys.exit(1)
    
    music_file = sys.argv[1]
    success = play_music(music_file)
    sys.exit(0 if success else 1)
