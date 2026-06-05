#!/usr/bin/env python3
"""
模型服务健康检查脚本
读取 OpenClaw 配置，对所有配置的模型 API 进行健康检查
"""

import json
import sys
import time
import os
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Run: pip install requests")
    sys.exit(1)

# 强制 UTF-8 输出（Windows 兼容）
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


def load_config():
    """加载 OpenClaw 配置文件"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_api_key(provider_name, provider_config, auth_profiles):
    """获取 provider 的 API key"""
    # 1. 直接从配置中获取
    if 'apiKey' in provider_config:
        return provider_config['apiKey']
    
    # 2. 从 auth profiles 获取
    profile_key = f"{provider_name}:default"
    if profile_key in auth_profiles:
        # 尝试从环境变量获取
        env_var = f"{provider_name.upper()}_API_KEY"
        api_key = os.environ.get(env_var)
        if api_key:
            return api_key
    
    return None


def check_anthropic_api(base_url, api_key, model_id):
    """检查 Anthropic 格式的 API（流式模式测量 TTFT）"""
    # WhaleCloud proxy 需要在 baseUrl 后加 /v1/messages
    clean_base = base_url.rstrip('/')
    if clean_base.endswith('/v1'):
        url = clean_base + '/messages'
    else:
        url = clean_base + '/v1/messages'
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }
    
    # 使用流式请求测量 TTFT
    payload = {
        'model': model_id,
        'max_tokens': 10,
        'stream': True,
        'messages': [
            {'role': 'user', 'content': 'say hello'}
        ]
    }
    
    start_time = time.time()
    ttft = None
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, stream=True)
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            elapsed = time.time() - start_time
            return {
                'status': 'error',
                'status_code': response.status_code,
                'elapsed_ms': round(elapsed * 1000),
                'ttft_ms': None,
                'error': response.text
            }
        
        # 流式读取，测量 TTFT
        for line in response.iter_lines():
            if not line:
                continue
            
            line_str = line.decode('utf-8')
            
            # Anthropic SSE 格式: "event: ..." 和 "data: ..."
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                if data_str == '[DONE]':
                    break
                
                try:
                    data = json.loads(data_str)
                    event_type = data.get('type')
                    
                    # message_start 或 content_block_start 表示首 token
                    if event_type in ('message_start', 'content_block_start', 'content_block_delta'):
                        if ttft is None:
                            ttft = time.time() - start_time
                        
                        # 如果是 content_block_delta 且有 text，说明已开始生成
                        if event_type == 'content_block_delta' and data.get('delta', {}).get('type') == 'text_delta':
                            break
                except json.JSONDecodeError:
                    continue
        
        elapsed = time.time() - start_time
        
        return {
            'status': 'ok',
            'status_code': 200,
            'elapsed_ms': round(elapsed * 1000),
            'ttft_ms': round(ttft * 1000) if ttft else round(elapsed * 1000),
            'error': None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'status': 'error',
            'status_code': None,
            'elapsed_ms': round(elapsed * 1000),
            'ttft_ms': None,
            'error': str(e)
        }


def check_openai_api(base_url, api_key, model_id):
    """检查 OpenAI 格式的 API（流式模式测量 TTFT）"""
    # 构建 URL
    url = urljoin(base_url.rstrip('/') + '/', 'chat/completions')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 使用流式请求测量 TTFT
    payload = {
        'model': model_id,
        'max_tokens': 10,
        'stream': True,
        'messages': [
            {'role': 'user', 'content': 'say hello'}
        ]
    }
    
    start_time = time.time()
    ttft = None
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, stream=True)
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            elapsed = time.time() - start_time
            return {
                'status': 'error',
                'status_code': response.status_code,
                'elapsed_ms': round(elapsed * 1000),
                'ttft_ms': None,
                'error': response.text
            }
        
        # 流式读取，测量 TTFT
        for line in response.iter_lines():
            if not line:
                continue
            
            line_str = line.decode('utf-8')
            
            # OpenAI SSE 格式: "data: ..."
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                if data_str == '[DONE]':
                    break
                
                try:
                    data = json.loads(data_str)
                    choices = data.get('choices', [])
                    
                    if choices:
                        choice = choices[0]
                        delta = choice.get('delta', {})
                        
                        # 如果 delta 中有 content，说明首 token 已到达
                        if 'content' in delta and delta['content']:
                            if ttft is None:
                                ttft = time.time() - start_time
                            break
                except json.JSONDecodeError:
                    continue
        
        elapsed = time.time() - start_time
        
        return {
            'status': 'ok',
            'status_code': 200,
            'elapsed_ms': round(elapsed * 1000),
            'ttft_ms': round(ttft * 1000) if ttft else round(elapsed * 1000),
            'error': None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'status': 'error',
            'status_code': None,
            'elapsed_ms': round(elapsed * 1000),
            'ttft_ms': None,
            'error': str(e)
        }


def main():
    print("=== 模型服务健康检查 (WhaleCloud) ===\n")
    
    # 加载配置
    config = load_config()
    models_config = config.get('models', {})
    providers = models_config.get('providers', {})
    auth_profiles = config.get('auth', {}).get('profiles', {})
    
    if not providers:
        print("ERROR: No providers configured")
        sys.exit(1)
    
    # 只检测 whalecloud provider
    target_providers = {'whalecloud'}
    
    results = []
    
    for provider_name, provider_config in providers.items():
        if provider_name not in target_providers:
            continue
        
        base_url = provider_config.get('baseUrl', '')
        api_format = provider_config.get('api', 'openai-completions')
        models = provider_config.get('models', [])
        
        # 获取 API key
        api_key = get_api_key(provider_name, provider_config, auth_profiles)
        
        if not api_key:
            print(f"⚠️  {provider_name}: API key not found, skipping {len(models)} models")
            for model in models:
                results.append({
                    'provider': provider_name,
                    'model': model['id'],
                    'status': 'skipped',
                    'error': 'API key not found'
                })
            continue
        
        print(f"🔍 Checking {provider_name} ({api_format}) - {len(models)} models...")
        
        for model in models:
            model_id = model['id']
            model_name = model.get('name', model_id)
            
            # 检查模型是否有独立的 baseUrl 覆盖
            model_base_url = model.get('baseUrl', base_url)
            
            # 根据 API 格式选择检查方法
            if api_format == 'anthropic-messages':
                result = check_anthropic_api(model_base_url, api_key, model_id)
            else:
                result = check_openai_api(model_base_url, api_key, model_id)
            
            # 添加 provider 和 model 信息
            result['provider'] = provider_name
            result['model'] = model_id
            result['model_name'] = model_name
            
            results.append(result)
            
            # 输出实时状态
            status_icon = '✅' if result['status'] == 'ok' else '❌'
            elapsed = result['elapsed_ms']
            ttft = result.get('ttft_ms')
            
            if ttft:
                print(f"   {status_icon} {model_name}: {result['status']} | TTFT={ttft}ms, Total={elapsed}ms")
            else:
                print(f"   {status_icon} {model_name}: {result['status']} ({elapsed}ms)")
    
    print("\n=== 检查完成 ===\n")
    
    # 输出 JSON 结果
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # 统计
    total = len(results)
    ok_count = sum(1 for r in results if r['status'] == 'ok')
    error_count = sum(1 for r in results if r['status'] == 'error')
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"\n📊 统计: 总计 {total} 个模型")
    print(f"   ✅ 正常: {ok_count}")
    print(f"   ❌ 异常: {error_count}")
    print(f"   ⚠️  跳过: {skipped_count}")


if __name__ == '__main__':
    main()
