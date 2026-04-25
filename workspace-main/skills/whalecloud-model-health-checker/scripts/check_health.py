#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhaleCloud Model Health Checker
从 OpenClaw 配置文件读取 WhaleCloud 模型，逐个测试 API 可用性
"""

import json
import os
import sys
import io
import time
from pathlib import Path

# Windows 下强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests


def load_config(config_path=None):
    """加载 OpenClaw 配置文件"""
    if config_path is None:
        # 默认路径
        home = Path.home()
        config_path = home / ".openclaw" / "openclaw.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_whalecloud_config(oc_config):
    """从配置中提取 WhaleCloud 提供商设置"""
    models_config = oc_config.get('models', {})
    providers = models_config.get('providers', {})
    whalecloud = providers.get('whalecloud')
    
    if not whalecloud:
        print("❌ 配置中未找到 WhaleCloud 提供商")
        sys.exit(1)
    
    base_url = whalecloud.get('baseUrl', '')
    api_key = whalecloud.get('apiKey', '')
    models = whalecloud.get('models', [])
    
    if not api_key:
        print("❌ WhaleCloud API Key 未配置")
        sys.exit(1)
    
    return base_url, api_key, models


def test_model(base_url, api_key, model, timeout=30, max_tokens=10):
    """测试单个模型的可用性
    
    使用 Anthropic Messages API 格式发送测试请求
    """
    # 构建完整的 API URL
    url = f"{base_url}/v1/messages"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model['id'],
        "messages": [
            {"role": "user", "content": "Hi"}
        ],
        "max_tokens": max_tokens
    }
    
    # 如果模型不支持 reasoning，移除 related 参数
    if not model.get('reasoning', False):
        payload.pop('thinking', None)
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return {
                'status': '✅ 可用',
                'response_time': f"{elapsed:.2f}s",
                'error': None
            }
        else:
            return {
                'status': '❌ 不可用',
                'response_time': f"{elapsed:.2f}s",
                'error': f"HTTP {response.status_code}: {response.text[:100]}"
            }
    except requests.exceptions.Timeout:
        return {
            'status': '⏰ 超时',
            'response_time': f">{timeout}s",
            'error': f"请求超时（{timeout}秒）"
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': '🔌 连接失败',
            'response_time': "N/A",
            'error': "无法连接到 API 服务器"
        }
    except Exception as e:
        return {
            'status': '❌ 错误',
            'response_time': "N/A",
            'error': str(e)
        }


def print_report(results):
    """打印健康状态报告"""
    # 标准输出：模型名称 | 状态 | 响应时间 | 错误信息
    print("\n" + "=" * 80)
    print("🔍 WhaleCloud 模型健康状态报告")
    print("=" * 80)
    print(f"{'模型名称':<25} {'状态':<12} {'响应时间':<12} {'错误信息'}")
    print("-" * 80)
    
    available = 0
    total = len(results)
    
    for result in results:
        model_name = result['name'][:24]
        status = result['status']
        response_time = result['response_time']
        error = result.get('error') or '-'
        
        if status.startswith('✅'):
            available += 1
        
        # 截断错误信息以适应输出
        if len(error) > 40:
            error = error[:37] + '...'
        
        print(f"{model_name:<25} {status:<12} {response_time:<12} {error}")
    
    print("=" * 80)
    print(f"📊 总结: {available}/{total} 个模型可用")
    print("=" * 80 + "\n")


def main():
    """主函数"""
    # 加载配置
    print("📖 正在加载配置文件...")
    oc_config = load_config()
    
    # 提取 WhaleCloud 配置
    base_url, api_key, models = extract_whalecloud_config(oc_config)
    
    print(f"🔗 API 地址: {base_url}")
    print(f"📦 发现 {len(models)} 个模型")
    
    # 测试每个模型
    results = []
    for i, model in enumerate(models, 1):
        print(f"\n[{i}/{len(models)}] 正在测试: {model.get('name', model['id'])}...")
        result = test_model(base_url, api_key, model)
        result['name'] = model.get('name', model['id'])
        result['id'] = model['id']
        results.append(result)
        
        # 避免请求过于频繁
        if i < len(models):
            time.sleep(1)
    
    # 打印报告
    print_report(results)
    
    # 返回摘要
    available_count = sum(1 for r in results if r['status'].startswith('✅'))
    return available_count, len(results)


if __name__ == "__main__":
    available, total = main()
    sys.exit(0 if available == total else 1)
