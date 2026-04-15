#!/usr/bin/env python3
"""
PotPlayer 音乐播放控制脚本
"""

import sys
import subprocess
import os
import glob
import random

import psutil

# PotPlayer 默认路径
POTPLAYER_PATH = r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe"

# 备用路径
POTPLAYER_ALT_PATHS = [
    r"C:\Program Files\PotPlayer64\PotPlayerMini64.exe",
    r"C:\Program Files (x86)\PotPlayer\PotPlayerMini.exe",
    r"D:\Program Files\PotPlayer64\PotPlayerMini64.exe",
]

# 用户音乐库路径
MUSIC_LIBRARY_PATH = r"E:\Music"
PLAYLIST_PATH = r"E:\Music\playlist.m3u"


def is_potplayer_running():
    """检查 PotPlayer 是否已经在运行"""
    for proc in psutil.process_iter(['name']):
        try:
            if 'PotPlayer' in proc.info['name']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def send_to_potplayer(file_path):
    """向已运行的 PotPlayer 发送文件播放"""
    potplayer = find_potplayer()
    if not potplayer:
        return False
    
    # 使用 /add 参数添加到播放列表并播放
    subprocess.Popen([potplayer, file_path, '/add'], shell=False)
    return True
    """查找 PotPlayer 可执行文件"""
    if os.path.exists(POTPLAYER_PATH):
        return POTPLAYER_PATH
    
    for path in POTPLAYER_ALT_PATHS:
        if os.path.exists(path):
            return path
    
    # 尝试从注册表查找
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\PotPlayerMini64.exe") as key:
            return winreg.QueryValue(key, None)
    except:
        pass
    
    return None


def play_file(file_path, add_to_playlist=False):
    """播放指定音乐文件"""
    potplayer = find_potplayer()
    if not potplayer:
        print("错误：未找到 PotPlayer，请确认已安装 PotPlayer 64-bit")
        return False
    
    # 如果路径是相对路径，尝试在 E:\Music 下查找
    if not os.path.isabs(file_path) and not os.path.exists(file_path):
        full_path = os.path.join(MUSIC_LIBRARY_PATH, file_path)
        if os.path.exists(full_path):
            file_path = full_path
    
    if not os.path.exists(file_path):
        print(f"错误：文件不存在 - {file_path}")
        return False
    
    # 检查 PotPlayer 是否已在运行
    if is_potplayer_running():
        print("PotPlayer 已在运行，添加到播放列表...")
        send_to_potplayer(file_path)
    else:
        cmd = [potplayer, file_path]
        if add_to_playlist:
            cmd.append("/add")
        subprocess.Popen(cmd, shell=False)
    
    print(f"正在播放: {file_path}")
    return True


def find_music_files(folder_path=None):
    """递归查找所有音乐文件"""
    if folder_path is None:
        folder_path = MUSIC_LIBRARY_PATH
    
    music_extensions = ['*.mp3', '*.flac', '*.wav', '*.aac', '*.ogg', '*.wma', '*.m4a']
    music_files = []
    
    for ext in music_extensions:
        pattern = os.path.join(folder_path, '**', ext)
        music_files.extend(glob.glob(pattern, recursive=True))
    
    return sorted(music_files)


def play_folder(folder_path=None, random_play=False):
    """播放文件夹中的所有音乐（递归包含子目录）"""
    potplayer = find_potplayer()
    if not potplayer:
        print("错误：未找到 PotPlayer")
        return False
    
    # 默认使用 E:\Music
    if folder_path is None:
        folder_path = MUSIC_LIBRARY_PATH
    
    # 如果路径是相对路径，尝试在 E:\Music 下查找
    if not os.path.isabs(folder_path) and not os.path.exists(folder_path):
        full_path = os.path.join(MUSIC_LIBRARY_PATH, folder_path)
        if os.path.exists(full_path):
            folder_path = full_path
    
    if not os.path.isdir(folder_path):
        print(f"错误：文件夹不存在 - {folder_path}")
        return False
    
    # 递归查找音乐文件
    music_files = find_music_files(folder_path)
    
    if not music_files:
        print(f"错误：文件夹中没有找到音乐文件 - {folder_path}")
        return False
    
    # 检查 PotPlayer 是否已在运行
    if is_potplayer_running():
        print("PotPlayer 已在运行，添加音乐到播放列表...")
        # 创建临时播放列表并发送
        temp_playlist = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'temp_playlist.m3u')
        with open(temp_playlist, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for music_file in music_files:
                f.write(f"{music_file}\n")
        send_to_potplayer(temp_playlist)
    else:
        cmd = [potplayer, folder_path]
        if random_play:
            cmd.append("/random")
        subprocess.Popen(cmd, shell=False)
    
    print(f"正在播放文件夹 ({len(music_files)} 首): {folder_path}")
    return True


def play_playlist(playlist_path=None):
    """播放 M3U 播放列表"""
    if playlist_path is None:
        playlist_path = PLAYLIST_PATH
    
    potplayer = find_potplayer()
    if not potplayer:
        print("错误：未找到 PotPlayer")
        return False
    
    if not os.path.exists(playlist_path):
        print(f"错误：播放列表不存在 - {playlist_path}")
        return False
    
    # 检查 PotPlayer 是否已在运行
    if is_potplayer_running():
        print("PotPlayer 已在运行，切换到新播放列表...")
        send_to_potplayer(playlist_path)
    else:
        subprocess.Popen([potplayer, playlist_path], shell=False)
    
    print(f"正在播放播放列表: {playlist_path}")
    return True


def create_playlist_from_folder(folder_path=None, output_path=None):
    """从文件夹创建 M3U 播放列表"""
    if folder_path is None:
        folder_path = MUSIC_LIBRARY_PATH
    if output_path is None:
        output_path = PLAYLIST_PATH
    
    music_files = find_music_files(folder_path)
    
    if not music_files:
        print(f"错误：没有找到音乐文件 - {folder_path}")
        return False
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for music_file in music_files:
            f.write(f"{music_file}\n")
    
    print(f"播放列表已创建: {output_path} ({len(music_files)} 首)")
    return True


def control_playback(action):
    """控制播放（暂停/停止/下一首/上一首）"""
    potplayer = find_potplayer()
    if not potplayer:
        print("错误：未找到 PotPlayer")
        return False
    
    action_params = {
        'play': '/play',
        'pause': '/pause',
        'stop': '/stop',
        'next': '/next',
        'prev': '/prev',
        'previous': '/prev',
    }
    
    param = action_params.get(action.lower())
    if not param:
        print(f"错误：未知操作 - {action}")
        return False
    
    subprocess.Popen([potplayer, param], shell=False)
    print(f"执行操作: {action}")
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python play_music.py <音乐文件或文件夹路径>")
        print("      python play_music.py --control <play|pause|stop|next|prev>")
        print("      python play_music.py --random [文件夹路径]")
        print("      python play_music.py --playlist [播放列表路径]")
        print("      python play_music.py --create-playlist [文件夹路径] [输出路径]")
        print("      python play_music.py --list [文件夹路径]")
        sys.exit(1)
    
    arg1 = sys.argv[1]
    
    if arg1 == "--control" and len(sys.argv) >= 3:
        control_playback(sys.argv[2])
    elif arg1 == "--random":
        folder = sys.argv[2] if len(sys.argv) > 2 else None
        play_folder(folder, random_play=True)
    elif arg1 == "--playlist":
        playlist = sys.argv[2] if len(sys.argv) > 2 else None
        play_playlist(playlist)
    elif arg1 == "--create-playlist":
        folder = sys.argv[2] if len(sys.argv) > 2 else None
        output = sys.argv[3] if len(sys.argv) > 3 else None
        create_playlist_from_folder(folder, output)
    elif arg1 == "--list":
        folder = sys.argv[2] if len(sys.argv) > 2 else None
        files = find_music_files(folder)
        print(f"找到 {len(files)} 首音乐:")
        for i, f in enumerate(files[:20], 1):
            print(f"  {i}. {os.path.basename(f)}")
        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 首")
    elif arg1 == "--default" or arg1 == "--home":
        # 播放默认音乐库
        play_folder(MUSIC_LIBRARY_PATH)
    elif os.path.isfile(arg1):
        play_file(arg1)
    elif os.path.isdir(arg1):
        play_folder(arg1)
    else:
        # 尝试作为相对路径在 E:\Music 下查找
        full_path = os.path.join(MUSIC_LIBRARY_PATH, arg1)
        if os.path.exists(full_path):
            if os.path.isfile(full_path):
                play_file(full_path)
            else:
                play_folder(full_path)
        else:
            print(f"错误：路径不存在 - {arg1}")
            sys.exit(1)


if __name__ == "__main__":
    main()
