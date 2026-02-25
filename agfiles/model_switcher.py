#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw Model Switcher - 外部模型切换工具

功能：
1. 显示可用模型列表（带序号）
2. 通过序号切换主模型
3. 可选：重启 OpenClaw Gateway

用法：
    python model_switcher.py              # 交互式选择模型
    python model_switcher.py --list       # 仅显示可用模型
    python model_switcher.py 1            # 通过序号切换模型
    python model_switcher.py --model "moonshot/kimi-k2.5"  # 通过名称指定模型
    python model_switcher.py --restart    # 切换后重启 Gateway
"""

import subprocess
import sys
import os
import json

# 设置控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 可用模型列表（完整名称）
AVAILABLE_MODELS = [
    {"id": "whalecloud/MiniMax-M2.5", "name": "WhaleCloud MiniMax-M2.5"},
    {"id": "moonshot/kimi-k2.5", "name": "Moonshot Kimi-K2.5"},
    {"id": "whalecloud/glm-4.7", "name": "WhaleCloud GLM-4.7"},
    {"id": "whalecloud/kimi-k2.5", "name": "WhaleCloud Kimi-K2.5"},
    {"id": "whalecloud/doubao-seed-2.0-pro", "name": "WhaleCloud Doubao-Pro"},
    {"id": "whalecloud/doubao-seed-2.0-mini", "name": "WhaleCloud Doubao-Mini"},
    {"id": "whalecloud/doubao-seed-2.0-lite", "name": "WhaleCloud Doubao-Lite"},
    {"id": "whalecloud/claude-4.5-sonnet", "name": "WhaleCloud Claude-4.5-Sonnet"},
    {"id": "whalecloud/claude-4.5-haiku", "name": "WhaleCloud Claude-4.5-Haiku"},
    {"id": "zhipu/glm-4.7", "name": "Zhipu GLM-4.7"},
]


def run_cmd(cmd: str) -> tuple:
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def get_current_model() -> str:
    """获取当前主模型"""
    code, stdout, stderr = run_cmd('openclaw config get agents.defaults.model.primary')
    if code == 0 and stdout.strip():
        return stdout.strip().strip('"')
    return ""


def list_models():
    """显示可用模型列表"""
    current = get_current_model()
    
    print("\n" + "=" * 80)
    print("可用模型列表:")
    print("-" * 80)
    
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        marker = "  [当前使用]" if model["id"] == current else ""
        print(f"  {i:2}. {model['name']:<40} {model['id']:<30}{marker}")
    
    print("-" * 80)
    if current:
        # 查找当前模型的全称
        current_name = current
        for m in AVAILABLE_MODELS:
            if m["id"] == current:
                current_name = m["name"]
                break
        print(f"当前使用: {current_name} ({current})")
    else:
        print("未设置主模型")
    print("=" * 80)
    print()


def switch_model_by_index(index: int, restart: bool = False) -> bool:
    """
    通过序号切换模型
    
    Args:
        index: 模型序号（从1开始）
        restart: 是否在切换后重启 Gateway
    
    Returns:
        是否成功
    """
    if index < 1 or index > len(AVAILABLE_MODELS):
        print(f"[X] 无效的序号: {index}")
        print(f"有效范围: 1 - {len(AVAILABLE_MODELS)}")
        return False
    
    model = AVAILABLE_MODELS[index - 1]
    return switch_model(model["id"], restart)


def switch_model(model_id: str, restart: bool = False) -> bool:
    """
    切换主模型
    
    Args:
        model_id: 模型 ID
        restart: 是否在切换后重启 Gateway
    
    Returns:
        是否成功
    """
    # 验证模型是否可用
    model_info = None
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            model_info = m
            break
    
    if not model_info:
        print(f"[X] 无效的模型: {model_id}")
        print(f"可用模型: {[m['id'] for m in AVAILABLE_MODELS]}")
        return False
    
    # 获取当前模型
    old_model = get_current_model()
    
    # 跳过如果已经是当前模型
    if old_model == model_id:
        print(f"[*] 当前已使用该模型: {model_info['name']}")
        return True
    
    # 使用 openclaw config set 命令更新配置
    print(f"[*] 正在切换主模型...")
    print(f"    {old_model} -> {model_id}")
    
    code, stdout, stderr = run_cmd(f'openclaw config set agents.defaults.model.primary "{model_id}"')
    
    if code != 0:
        print(f"[X] 设置模型失败: {stderr}")
        return False
    
    print(f"[OK] 已切换主模型: {model_info['name']}")
    print(f"     ({model_id})")
    
    # 可选：重启 Gateway
    if restart:
        print("\n[*] 正在重启 OpenClaw Gateway...")
        code, stdout, stderr = run_cmd("openclaw gateway restart")
        if code == 0:
            print("[OK] Gateway 重启完成")
        else:
            print(f"[!] 重启命令执行失败: {stderr}")
            print("    请手动运行: openclaw gateway restart")
    
    return True


def interactive_select():
    """交互式选择模型"""
    current = get_current_model()
    
    print("\n" + "=" * 80)
    print("请选择主模型（输入序号）:")
    print("-" * 80)
    
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        marker = "  <- 当前使用" if model["id"] == current else ""
        print(f"  {i:2}. {model['name']:<40}{marker}")
    
    print("-" * 80)
    print("   0. 退出")
    print("=" * 80)
    print()
    
    while True:
        try:
            choice = input("请输入编号 [0-{}]: ".format(len(AVAILABLE_MODELS))).strip()
            if choice == "0":
                print("已退出")
                return False
            
            try:
                idx = int(choice)
                if 1 <= idx <= len(AVAILABLE_MODELS):
                    model = AVAILABLE_MODELS[idx - 1]
                    return switch_model(model["id"], restart=True)
                else:
                    print("无效选择，请重新输入")
            except ValueError:
                print("请输入数字")
        except KeyboardInterrupt:
            print("\n已退出")
            return False


def main():
    # 解析参数
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    # 检查参数
    if len(sys.argv) == 1:
        # 无参数，交互式选择
        interactive_select()
        return
    
    if "--list" in sys.argv:
        list_models()
        return
    
    # 解析参数
    restart = False
    model_arg = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--restart":
            restart = True
        elif arg == "--model" and i + 1 < len(sys.argv):
            model_arg = sys.argv[i + 1]
            i += 2
            continue
        elif arg.isdigit():
            # 数字参数作为序号处理
            idx = int(arg)
            switch_model_by_index(idx, restart)
            return
        else:
            # 尝试作为模型ID处理
            model_arg = arg
        
        i += 1
    
    if model_arg:
        switch_model(model_arg, restart)
    else:
        list_models()


if __name__ == "__main__":
    main()
