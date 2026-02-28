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


def get_configured_models():
    """从 OpenClaw 配置获取实际可用的模型列表"""
    try:
        result = subprocess.run(
            "openclaw models status",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return [], None
        
        models = []
        current_model = None
        
        # 解析 Configured models 行
        for line in result.stdout.split('\n'):
            if line.startswith('Default'):
                current_model = line.split(':', 1)[1].strip()
            elif line.startswith('Configured models'):
                # 提取冒号后的模型列表
                models_part = line.split(':', 1)[1].strip()
                # 解析逗号分隔的模型列表
                for model in models_part.split(','):
                    model = model.strip()
                    if model:
                        models.append(model)
        
        return models, current_model
    except Exception as e:
        print(f"⚠️ 无法获取配置模型：{e}")
        return [], None


# 模型别名和价格信息（用于展示）
MODEL_INFO = {
    "whalecloud/qwen3.5-flash": {"alias": "QWen-Flash", "input": 0.8, "output": 8, "context": "1M", "tag": "性价比之王 🥇"},
    "whalecloud/doubao-seed-2.0-mini": {"alias": "Doubao-Mini", "input": 0.8, "output": 8, "context": "256K", "tag": "轻量快速 🥈"},
    "whalecloud/doubao-seed-2.0-lite": {"alias": "Doubao-Lite", "input": 1.8, "output": 10.8, "context": "256K", "tag": "均衡性价比"},
    "whalecloud/MiniMax-M2.5": {"alias": "MiniMax-M2.5", "input": 2.1, "output": 8.4, "context": "200K", "tag": "编程首选 🥉"},
    "whalecloud/qwen3.5-plus": {"alias": "QWen-Plus", "input": 2, "output": 12, "context": "1M", "tag": "长文多模态"},
    "whalecloud/glm-4.7": {"alias": "GLM-4.7", "input": 4, "output": 16, "context": "200K", "tag": "中文 Agentic"},
    "whalecloud/kimi-k2.5": {"alias": "Kimi", "input": 4, "output": 21, "context": "256K", "tag": "长输出多模态"},
    "whalecloud/glm-5": {"alias": "GLM-5", "input": 6, "output": 22, "context": "200K", "tag": "旗舰编程 SOTA"},
    "whalecloud/doubao-seed-2.0-code": {"alias": "Doubao-Code", "input": 9.6, "output": 48, "context": "256K", "tag": "专业编程"},
    "whalecloud/doubao-seed-2.0-pro": {"alias": "Doubao-Pro", "input": 9.6, "output": 48, "context": "256K", "tag": "旗舰全能"},
    "whalecloud/doubao-vision-lite": {"alias": "Doubao-Vision-Lite", "input": 3, "output": 12, "context": "256K", "tag": "视觉性价比"},
    "whalecloud/doubao-vision-pro": {"alias": "Doubao-Vision-Pro", "input": 12, "output": 48, "context": "256K", "tag": "视觉理解"},
    "whalecloud/qwen3.5-max": {"alias": "QWen-Max", "input": 16, "output": 48, "context": "256K", "tag": "QWen 旗舰"},
    "whalecloud/claude-4.5-haiku": {"alias": "Claude-4.5-Haiku", "input": 30, "output": 120, "context": "200K", "tag": "快速 Claude"},
    "whalecloud/claude-4.5-sonnet": {"alias": "Claude-4.5-Sonnet", "input": 60, "output": 240, "context": "200K", "tag": "最强 Claude"},
    "whalecloud/claude-4.6-sonnet": {"alias": "Claude-4.6-Sonnet", "input": 24, "output": 120, "context": "200K", "tag": "高端专业"},
    "moonshot/kimi-k2.5": {"alias": "Kimi (Moonshot 直连)", "input": 4, "output": 21, "context": "256K", "tag": "长输出多模态", "source": "external"},
    "zhipu/glm-4.7": {"alias": "GLM-4.7 (智谱直连)", "input": None, "output": None, "context": "200K", "tag": "资源包已购", "source": "external"},
    "zhipu/glm-5": {"alias": "GLM-5 (智谱直连)", "input": None, "output": None, "context": "256K", "tag": "资源包/自费", "source": "external"},
}


def get_model_display_info(model_id):
    """获取模型的展示信息（别名、价格等）"""
    info = MODEL_INFO.get(model_id, {})
    alias = info.get('alias', model_id.split('/')[-1])
    input_price = info.get('input')
    output_price = info.get('output')
    context = info.get('context', '未知')
    tag = info.get('tag', '')
    source = info.get('source', 'whalecloud')
    
    # 处理价格显示
    if input_price is None or output_price is None:
        price = "资源包"
    else:
        price = f"¥{input_price} / ¥{output_price}"
    
    # 处理来源图标
    source_icon = "🌐" if source == 'external' else "🏢"
    
    return {
        'id': model_id,
        'alias': alias,
        'price': price,
        'context': context,
        'tag': tag,
        'source_icon': source_icon
    }


def display_models(models, current_model):
    """显示模型列表"""
    if not models:
        print("⚠️ 无法获取可用模型列表")
        return
    
    print("\n" + "="*100)
    print("🧠 可用模型列表\n")
    print(f"{'序号':<6} {'模型名称':<35} {'价格 (I/O)':<16} {'上下文':<10} {'来源':<8} {'定位':<20}")
    print("-"*100)
    
    for i, model_id in enumerate(models, 1):
        info = get_model_display_info(model_id)
        current_marker = " [当前使用]" if model_id == current_model else ""
        print(f"{i:<6} {info['alias']:<35} {info['price']:<16} {info['context']:<10} {info['source_icon']:<8} {info['tag']:<20}{current_marker}")
    
    print("-"*100)
    print(f"\n**当前使用**: {current_model or '未知'}")
    print(f"**可用模型数**: {len(models)}")
    print("\n💡 **提示**: 直接回复序号 (如 `5`) 即可切换模型")
    print("🏢 = WhaleCloud 代理（公司结算） | 🌐 = 外部直连（自费/资源包）")
    print("="*100)


def switch_model(model_name):
    """切换模型"""
    print(f"\n🔄 正在切换到 {model_name}...")

    try:
        # 使用 openclaw models set 命令切换模型
        cmd = f"openclaw models set {model_name}"
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
        print(f"   运行命令：openclaw models set {model_name}")
        print(f"   然后重启：openclaw gateway restart")
        return False


def main():
    """主函数"""
    # 动态获取实际配置的模型列表和当前模型
    models, current_model = get_configured_models()
    
    if not models:
        print("❌ 无法获取可用模型列表，请检查 OpenClaw 配置")
        return
    
    # 显示模型列表
    display_models(models, current_model)
    
    # 如果提供了命令行参数，直接切换
    if len(sys.argv) > 1:
        model_index = sys.argv[1]
        try:
            idx = int(model_index)
            if 1 <= idx <= len(models):
                model_name = models[idx-1]
                switch_model(model_name)
            elif idx == 0:
                print("👋 已退出")
                sys.exit(0)
            else:
                print(f"❌ 无效序号：{idx}，请输入 1-{len(models)} 之间的数字")
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
            
            if 1 <= idx <= len(models):
                model_name = models[idx-1]
                if switch_model(model_name):
                    # 切换成功后退出
                    break
            else:
                print(f"❌ 无效序号：{idx}，请输入 1-{len(models)} 之间的数字")
                
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
