#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Selector - 交互式模型选择器
显示所有可用模型清单，支持通过序号快速切换模型
"""

import json
import os
import sys
import subprocess
from pathlib import Path

# 模型数据文件路径（从 model-recommender 复制）
MODELS_FILE = Path(__file__).parent.parent / "model-recommender" / "models-capabilities.json"

# 模型配置（简化版，包含常用模型）
MODELS = [
    {"name": "qwen3.5-flash", "alias": "WhaleCloud QWen-Flash", "input": 0.8, "output": 8, "context": "1M", "tag": "性价比之王 🥇"},
    {"name": "doubao-seed-2.0-mini", "alias": "WhaleCloud Doubao-Mini", "input": 0.8, "output": 8, "context": "256K", "tag": "轻量快速 🥈"},
    {"name": "MiniMax-M2.5", "alias": "WhaleCloud MiniMax-M2.5", "input": 2.1, "output": 8.4, "context": "200K", "tag": "编程首选 🥉"},
    {"name": "glm-4.7", "alias": "WhaleCloud GLM-4.7", "input": 4, "output": 16, "context": "256K", "tag": "平衡之选"},
    {"name": "kimi-k2.5", "alias": "WhaleCloud Kimi-K2.5", "input": 12, "output": 48, "context": "256K", "tag": "长文本处理"},
    {"name": "doubao-seed-2.0-pro", "alias": "WhaleCloud Doubao-Pro", "input": 20, "output": 80, "context": "256K", "tag": "高端选择"},
    {"name": "claude-4.5-haiku", "alias": "WhaleCloud Claude-4.5-Haiku", "input": 30, "output": 120, "context": "200K", "tag": "快速 Claude"},
    {"name": "claude-4.5-sonnet", "alias": "WhaleCloud Claude-4.5-Sonnet", "input": 60, "output": 240, "context": "200K", "tag": "最强 Claude"},
    {"name": "qwen3.5-plus", "alias": "WhaleCloud QWen-Plus", "input": 4, "output": 16, "context": "256K", "tag": "均衡 Qwen"},
]

# 默认模型
DEFAULT_MODEL = "whalecloud/qwen3.5-plus"


def get_current_model():
    """获取当前使用的模型"""
    try:
        # 从环境变量或配置获取
        model = os.getenv("OPENCLAW_MODEL", DEFAULT_MODEL)
        return model
    except:
        return DEFAULT_MODEL


def display_models(current_model):
    """显示模型列表"""
    print("\n" + "="*100)
    print("🧠 " * 20)
    print("="*100)
    print("\n## 可用模型列表\n")
    print(f"{'序号':<6} {'模型名称':<35} {'价格 (输入/输出)':<20} {'上下文':<10} {'定位':<15}")
    print("-"*100)
    
    for i, model in enumerate(MODELS, 1):
        price = f"¥{model['input']} / ¥{model['output']}"
        current_marker = " [当前使用]" if model['name'] in current_model or model['alias'] in current_model else ""
        print(f"{i:<6} {model['alias']:<35} {price:<20} {model['context']:<10} {model['tag']:<15}{current_marker}")
    
    print("-"*100)
    print(f"\n**当前使用**: {current_model}")
    print("\n💡 **提示**: 输入序号 (如 `5`) 然后回车即可切换模型，输入 `0` 退出")
    print("="*100)


def switch_model(model_name):
    """切换模型"""
    print(f"\n🔄 正在切换到 {model_name}...")
    
    try:
        # 方法 1: 使用 session_status 工具（如果可用）
        # 这里调用 OpenClaw 的 session_status 命令
        cmd = f"openclaw session_status --model {model_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ 成功切换到 {model_name}")
            
            # 重启 Gateway
            print("🔄 重启 Gateway 以使新模型生效...")
            subprocess.run("openclaw gateway restart", shell=True, capture_output=True, timeout=30)
            print("✅ Gateway 已重启，新模型已生效！")
            return True
        else:
            print(f"❌ 切换失败：{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 切换失败：{e}")
        print("\n💡 手动切换方法:")
        print(f"   1. 编辑 openclaw.json 配置文件")
        print(f"   2. 修改 model 字段为：{model_name}")
        print(f"   3. 运行：openclaw gateway restart")
        return False


def main():
    """主函数"""
    current_model = get_current_model()
    
    # 显示模型列表
    display_models(current_model)
    
    # 如果提供了命令行参数，直接切换
    if len(sys.argv) > 1:
        model_index = sys.argv[1]
        try:
            idx = int(model_index)
            if 1 <= idx <= len(MODELS):
                model_name = MODELS[idx-1]['name']
                switch_model(model_name)
            elif idx == 0:
                print("👋 已退出")
                sys.exit(0)
            else:
                print(f"❌ 无效序号：{idx}，请输入 1-{len(MODELS)} 之间的数字")
        except ValueError:
            print(f"❌ 无效输入：{model_index}，请输入数字")
        return
    
    # 交互模式：等待用户输入
    while True:
        try:
            user_input = input("\n请输入模型序号 (0 退出): ").strip()
            
            if not user_input:
                continue
            
            if user_input == '0':
                print("👋 已退出")
                break
            
            idx = int(user_input)
            
            if 1 <= idx <= len(MODELS):
                model_name = MODELS[idx-1]['name']
                if switch_model(model_name):
                    # 切换成功后退出
                    break
            else:
                print(f"❌ 无效序号：{idx}，请输入 1-{len(MODELS)} 之间的数字")
                
        except ValueError:
            print("❌ 无效输入，请输入数字")
        except KeyboardInterrupt:
            print("\n👋 已退出")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            break


if __name__ == "__main__":
    # 设置 UTF-8 编码
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    
    main()
