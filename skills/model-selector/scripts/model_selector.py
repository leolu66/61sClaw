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

# 模型配置（完整版，包含所有可用模型）
MODELS = [
    # WhaleCloud 代理（公司结算）- 🏢
    {"name": "qwen3.5-flash", "alias": "QWen-Flash", "input": 0.8, "output": 8, "context": "1M", "tag": "性价比之王 🥇", "source": "whalecloud"},
    {"name": "doubao-seed-2.0-mini", "alias": "Doubao-Mini", "input": 0.8, "output": 8, "context": "256K", "tag": "轻量快速 🥈", "source": "whalecloud"},
    {"name": "MiniMax-M2.5", "alias": "MiniMax-M2.5", "input": 2.1, "output": 8.4, "context": "200K", "tag": "编程首选 🥉", "source": "whalecloud"},
    {"name": "doubao-seed-2.0-lite", "alias": "Doubao-Lite", "input": 1.8, "output": 10.8, "context": "256K", "tag": "均衡性价比", "source": "whalecloud"},
    {"name": "qwen3.5-plus", "alias": "QWen-Plus", "input": 2, "output": 12, "context": "1M", "tag": "长文多模态", "source": "whalecloud"},
    {"name": "glm-4.7", "alias": "GLM-4.7", "input": 4, "output": 16, "context": "200K", "tag": "中文 Agentic", "source": "whalecloud"},
    {"name": "glm-5", "alias": "GLM-5", "input": 6, "output": 22, "context": "200K", "tag": "旗舰编程 SOTA", "source": "whalecloud"},
    {"name": "kimi-k2.5", "alias": "Kimi-K2.5", "input": 4, "output": 21, "context": "256K", "tag": "长输出多模态", "source": "whalecloud"},
    {"name": "doubao-seed-2.0-code", "alias": "Doubao-Code", "input": 9.6, "output": 48, "context": "256K", "tag": "专业编程", "source": "whalecloud"},
    {"name": "doubao-seed-2.0-pro", "alias": "Doubao-Pro", "input": 20, "output": 80, "context": "256K", "tag": "高端选择", "source": "whalecloud"},
    {"name": "claude-4.5-haiku", "alias": "Claude-4.5-Haiku", "input": 30, "output": 120, "context": "200K", "tag": "快速 Claude", "source": "whalecloud"},
    {"name": "claude-4.5-sonnet", "alias": "Claude-4.5-Sonnet", "input": 60, "output": 240, "context": "200K", "tag": "最强 Claude", "source": "whalecloud"},
    {"name": "qwen3.5-max", "alias": "QWen-Max", "input": 16, "output": 48, "context": "256K", "tag": "QWen 旗舰", "source": "whalecloud"},
    {"name": "doubao-vision-pro", "alias": "Doubao-Vision-Pro", "input": 12, "output": 48, "context": "256K", "tag": "视觉理解", "source": "whalecloud"},
    {"name": "doubao-vision-lite", "alias": "Doubao-Vision-Lite", "input": 3, "output": 12, "context": "256K", "tag": "视觉性价比", "source": "whalecloud"},
    # 外部直连（自费）- 🌐
    {"name": "moonshot/kimi-k2.5", "alias": "Kimi-K2.5 (Moonshot 直连)", "input": 4, "output": 21, "context": "256K", "tag": "长输出多模态", "source": "external"},
    {"name": "zhipu/glm-4.7", "alias": "GLM-4.7 (智谱直连)", "input": None, "output": None, "context": "200K", "tag": "资源包已购", "source": "external"},
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
    print("🧠 可用模型列表\n")
    print(f"{'序号':<6} {'模型名称':<35} {'价格 (I/O)':<16} {'上下文':<10} {'来源':<8} {'定位':<20}")
    print("-"*100)
    
    for i, model in enumerate(MODELS, 1):
        # 处理资源包模型（无价格）
        if model.get('input') is None or model.get('output') is None:
            price = "资源包"
        else:
            price = f"¥{model['input']} / ¥{model['output']}"
        
        current_marker = " [当前使用]" if model['name'] in current_model or model['alias'] in current_model else ""
        source_icon = "🌐" if model.get('source') == 'external' else "🏢"
        print(f"{i:<6} {model['alias']:<35} {price:<16} {model['context']:<10} {source_icon:<8} {model['tag']:<20}{current_marker}")
    
    print("-"*100)
    print(f"\n**当前使用**: {current_model}")
    print("\n💡 **提示**: 直接回复序号 (如 `5`) 即可切换模型")
    print("🏢 = WhaleCloud 代理（公司结算） | 🌐 = 外部直连（自费/资源包）")
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
