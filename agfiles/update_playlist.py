#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新精选播放清单
检查 E:\Music\精选 目录，如果有新增歌曲则更新 M3U 文件
"""
import os
import codecs
import json
from datetime import datetime

MUSIC_DIR = r'E:\Music\精选'
PLAYLIST_FILE = r'E:\Music\精选.m3u'
STATE_FILE = r'C:\Users\luzhe\.openclaw\workspace-main\datas\playlist_state.json'

def get_music_files():
    """获取目录下的所有音乐文件"""
    extensions = ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma', '.m4a']
    files = []
    for root, dirs, filenames in os.walk(MUSIC_DIR):
        for f in filenames:
            if os.path.splitext(f)[1].lower() in extensions:
                files.append(os.path.join(root, f))
    return sorted(files)

def load_state():
    """加载上次状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'last_files': [], 'last_date': ''}

def save_state(files):
    """保存当前状态"""
    state = {
        'last_files': files,
        'last_date': datetime.now().strftime('%Y-%m-%d')
    }
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False)

def update_playlist():
    """检查并更新播放清单"""
    today = datetime.now().strftime('%Y-%m-%d')
    state = load_state()
    
    # 检查今天是否已检查过
    if state.get('last_date') == today:
        return False, '今日已检查' 
    
    current_files = get_music_files()
    
    # 检查是否有新增或删除
    old_files = set(state.get('last_files', []))
    new_files = set(current_files)
    
    added = new_files - old_files
    removed = old_files - new_files
    
    if added or removed:
        # 重新生成 M3U
        with codecs.open(PLAYLIST_FILE, 'w', 'utf-8-sig') as f:
            f.write('#EXTM3U\n')
            for file in current_files:
                f.write(file + '\n')
        
        save_state(current_files)
        
        msg = []
        if added:
            msg.append(f'+{len(added)} 新增')
        if removed:
            msg.append(f'-{len(removed)} 删除')
        return True, ', '.join(msg)
    else:
        return False, '无变化'

if __name__ == '__main__':
    updated, msg = update_playlist()
    if updated:
        print(f'播放清单已更新: {msg}')
    else:
        print(f'播放清单无变化')
