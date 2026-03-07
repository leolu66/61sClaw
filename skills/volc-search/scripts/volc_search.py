#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
火山融合信息搜索API 搜索工具
支持网页搜索、搜索总结、图片搜索
"""
import requests
import json
import sys
import os
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
BASE_URL = 'https://open.feedcoopapi.com/search_api/web_search'

def get_api_key():
    """从密码箱获取 API Key"""
    try:
        # 尝试调用 vault 脚本获取
        vault_script = os.path.join(os.path.dirname(__file__), '..', '..', 'vault', 'scripts', 'vault.py')
        if os.path.exists(vault_script):
            # 直接读取凭据文件
            cred_file = os.path.join(os.path.expanduser('~'), '.openclaw', 'vault', 'credentials.json')
            if os.path.exists(cred_file):
                with open(cred_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    creds = data.get('credentials', {})
                    volc_cred = creds.get('volcsearch', {})
                    for field in volc_cred.get('fields', []):
                        if field.get('key') == 'api_key':
                            return field.get('value', '')
    except Exception as e:
        pass
    
    # 降级：从环境变量读取
    return os.environ.get('VOLCSEARCH_API_KEY', '')

def search(query, count=5, search_type='web', need_summary=False, time_range=None):
    """执行火山融合搜索"""
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] 请先在密码箱中添加 volcsearch 凭据：api_key", file=sys.stderr)
        print("[ERROR] 使用命令：查 volcsearch 的 api_key 获取API Key", file=sys.stderr)
        return None
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'Query': query,
        'SearchType': search_type,
        'Count': min(count, 50) if search_type == 'web' else min(count, 5)
    }
    
    # 添加可选参数
    if search_type in ['web', 'web_summary']:
        # web_summary 类型必须设置 NeedSummary 为 true
        if search_type == 'web_summary':
            payload['NeedSummary'] = True
        elif need_summary:
            payload['NeedSummary'] = True
    
    if time_range:
        payload['TimeRange'] = time_range
    
    try:
        r = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        # 检查错误
        if 'ResponseMetadata' in data and 'Error' in data['ResponseMetadata']:
            error = data['ResponseMetadata']['Error']
            print(f"[ERROR] {error.get('CodeN', '')}: {error.get('Message', 'Unknown error')}", file=sys.stderr)
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 请求错误: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析错误: {e}", file=sys.stderr)
        print(f"[ERROR] 响应内容: {r.text[:500]}", file=sys.stderr)
        return None

def format_web_results(data):
    """格式化网页搜索结果"""
    result = data.get('Result', {})
    web_results = result.get('WebResults', [])
    
    if not web_results:
        return "未找到结果"
    
    output = []
    for i, r in enumerate(web_results, 1):
        title = r.get('Title', 'N/A')
        url = r.get('Url', 'N/A')
        snippet = r.get('Snippet', '')
        
        output.append(f"{i}. {title}")
        output.append(f"   {url}")
        if snippet:
            # 截断过长的摘要
            if len(snippet) > 150:
                snippet = snippet[:150] + "..."
            output.append(f"   {snippet}")
        output.append("")
    
    return "\n".join(output)

def format_summary_results(data):
    """格式化搜索总结结果"""
    result = data.get('Result', {})
    web_results = result.get('WebResults', [])
    
    output = []
    
    # 先显示搜索结果
    if web_results:
        output.append("📋 搜索结果：")
        output.append("")
        for i, r in enumerate(web_results[:3], 1):  # 只显示前3条
            title = r.get('Title', 'N/A')
            url = r.get('Url', 'N/A')
            output.append(f"{i}. {title}")
            output.append(f"   {url}")
            output.append("")
    
    # 再显示总结
    choices = result.get('Choices', [])
    if choices:
        output.append("📝 总结：")
        output.append("")
        for choice in choices:
            # 非流式响应
            if 'Message' in choice:
                content = choice['Message'].get('Content', '')
                if content:
                    output.append(content)
            # 流式响应
            elif 'Delta' in choice:
                content = choice['Delta'].get('Content', '')
                if content:
                    output.append(content)
    
    if not output:
        return "未找到结果"
    
    return "\n".join(output)

def format_image_results(data):
    """格式化图片搜索结果"""
    result = data.get('Result', {})
    image_results = result.get('ImageResults', [])
    
    if not image_results:
        return "未找到图片结果"
    
    output = []
    for i, r in enumerate(image_results, 1):
        title = r.get('Title', 'N/A')
        image_info = r.get('Image', {})
        image_url = image_info.get('Url', 'N/A') if image_info else 'N/A'
        
        output.append(f"{i}. {title}")
        output.append(f"   🖼️ {image_url}")
        output.append("")
    
    return "\n".join(output)

def main():
    # 解析参数
    args = sys.argv[1:]
    
    if not args or args[0] in ['-h', '--help', 'help']:
        print("火山融合信息搜索工具")
        print("")
        print("用法: python volc_search.py <关键词> [数量] [类型]")
        print("")
        print("参数:")
        print("  关键词    搜索内容 (必填)")
        print("  数量      返回结果数量，默认 5")
        print("  类型      搜索类型: web(网页) / summary(总结) / image(图片)，默认 web")
        print("")
        print("示例:")
        print('  python volc_search.py "人工智能"')
        print('  python volc_search.py "AI news" 10 web')
        print('  python volc_search.py "北京旅游攻略" 5 summary')
        print('  python volc_search.py "猫咪" 5 image')
        return
    
    query = args[0]
    count = int(args[1]) if len(args) > 1 else 5
    
    # 解析搜索类型
    search_type = 'web'
    need_summary = False
    if len(args) > 2:
        t = args[2].lower()
        if t in ['summary', 'sum', '总结']:
            search_type = 'web_summary'
            need_summary = True
        elif t in ['image', 'img', '图片']:
            search_type = 'image'
        else:
            search_type = 'web'
    
    # 执行搜索
    print(f"🔍 搜索: {query} (类型: {search_type})")
    print("")
    
    data = search(query, count, search_type, need_summary)
    
    if data is None:
        sys.exit(1)
    
    # 格式化输出
    if search_type == 'image':
        print(format_image_results(data))
    elif search_type == 'web_summary':
        print(format_summary_results(data))
    else:
        print(format_web_results(data))

if __name__ == '__main__':
    main()
