#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 命令入口 - 优先使用 Windows 系统自带 TTS
"""

import sys
import os

# 转发到 windows-tts
windows_tts_path = os.path.join(os.path.dirname(__file__), "..", "windows-tts", "index.py")

if __name__ == "__main__":
    # 将参数传递给 windows-tts
    sys.argv[0] = windows_tts_path
    with open(windows_tts_path, "r", encoding="utf-8") as f:
        exec(f.read())
