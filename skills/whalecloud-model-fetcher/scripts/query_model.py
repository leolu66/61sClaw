#!/usr/bin/env python3
"""
WhaleCloud 模型详情查询器
实时爬取单个模型详情，支持与本地数据比对更新
"""

import asyncio
import json
import os
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Page

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="
MODEL_INFO_URL = "https://lab.iwhalecloud.com/gpt-proxy/console/model-info"
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
DATA_FILE = OUTPUT_DIR / "models_data_full.json"


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except:
        print(f"[{timestamp}] [{level}] {message.encode('ascii', 'ignore').decode()}")


def load_local_data() -> Optional[List[Dict]]:
    """加载本地 JSON 数据"""
    if not DATA_FILE.exists():
        return None
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"加载本地数据失败: {e}", "WARN")
        return None


def find_model_in_local(data: List[Dict], query: str) -> Optional[Dict]:
    """在本地数据中查找模型（支持模糊匹配）"""
    query_lower = query.lower()
    matches = []
    
    for group in data:
        for model in group.get('models', []):
            name = model.get('name', '')
            model_name = model.get('modelName', '')
            model_id = model.get('modelId', '')
            
            # 精确匹配
            if query_lower == name.lower() or query_lower == model_name.lower():
                return model  # 直接返回精确匹配
            
            # 模糊匹配
            if (query_lower in name.lower() or 
                query_lower in model_name.lower() or 
                query_lower in model_id.lower()):
                matches.append(model)
    
    # 如果只有一个模糊匹配，返回它
    if len(matches) == 1:
        return matches[0]
    
    # 多个匹配，返回匹配列表
    if len(matches) > 1:
        return {"_multiple_matches": matches}
    
    return None


async def query_model_detail(page: Page, query: str) -> Optional[Dict]:
    """在页面上查询模型详情"""
    
    # 等待卡片加载
    await page.wait_for_selector('.card-hover', timeout=30000)
    await asyncio.sleep(2)
    
    # 获取所有模型卡片
    cards = await page.query_selector_all('.card-hover')
    log(f"找到 {len(cards)} 个模型卡片")
    
    query_lower = query.lower()
    target_card = None
    target_index = -1
    
    # 查找匹配的卡片
    for i, card in enumerate(cards):
        card_text = await card.evaluate('el => el.textContent')
        lines = [line.strip() for line in card_text.split('\n') if line.strip()]
        
        if len(lines) >= 2:
            model_name = lines[1].strip()
        else:
            continue
        
        # 精确匹配
        if query_lower == model_name.lower():
            target_card = card
            target_index = i
            log(f"精确匹配到模型: {model_name}")
            break
        
        # 模糊匹配（记录第一个匹配的）
        if target_card is None and query_lower in model_name.lower():
            target_card = card
            target_index = i
            log(f"模糊匹配到模型: {model_name}")
    
    if not target_card:
        return None
    
    # 提取卡片基础信息
    card_text = await target_card.evaluate('el => el.textContent')
    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
    
    if len(lines) >= 2:
        full_name = lines[1].strip()
    else:
        full_name = f"模型{target_index+1}"
    
    # 提取简介
    desc_match = re.search(r'对应模型【.*', card_text, re.S)
    description = desc_match.group().split('\n')[0].strip() if desc_match else ''
    
    # 提取卡片标签
    try:
        tags = await target_card.eval_on_selector_all(
            '.rounded-xl', 
            'els => els.map(el => el.innerText.trim()).filter(t => t && t.length < 20 && t != "复制模型名")',
            default=[]
        )
    except:
        tags = []
    
    log(f"正在获取详情: {full_name}")
    
    # 点击卡片打开详情抽屉
    await target_card.click()
    await asyncio.sleep(3)
    
    # 提取详情信息
    detail_info = await page.evaluate("""
        () => {
            const drawerText = document.body.innerText;
            const info = {
                modelCode: '',
                modelId: '',
                inputPrice: '',
                outputPrice: '',
                cachePrice: '',
                contextLength: '',
                maxOutput: '',
                releaseTime: '',
                billingType: '',
                supportFunctionCall: false,
                detailTags: []
            };
            
            // 提取模型ID
            const idMatch = drawerText.match(/模型ID[：:]?\\s*`?([a-zA-Z0-9-_.]+)`?/i);
            if (idMatch) info.modelId = idMatch[1].trim();
            
            // 提取模型编码
            const codeMatch = drawerText.match(/(模型编码|调用编码|model code)[：:]?\\s*`?([a-zA-Z0-9-_.]+)`?/i);
            if (codeMatch) info.modelCode = codeMatch[2].trim();
            
            // 提取计费方式
            const billingMatch = drawerText.match(/(计费方式)[：:]?\\s*([\\u4e00-\\u9fa5]+)/i);
            if (billingMatch) info.billingType = billingMatch[2].trim();
            
            // 提取价格
            const inputEl = document.querySelector('div.bg-gradient-to-br.from-blue-50.to-blue-100 .text-3xl.font-bold.text-blue-600');
            const outputEl = document.querySelector('div.bg-gradient-to-br.from-emerald-50.to-emerald-100 .text-3xl.font-bold.text-emerald-600');
            const cacheEl = document.querySelector('div.bg-gradient-to-br.from-purple-50.to-purple-100 .text-3xl.font-bold.text-purple-600');
            
            if (inputEl) info.inputPrice = inputEl.textContent.trim() + ' 元/M tokens';
            if (outputEl) info.outputPrice = outputEl.textContent.trim() + ' 元/M tokens';
            if (cacheEl) info.cachePrice = cacheEl.textContent.trim() + ' 元/M tokens';
            
            // 提取上下文长度
            const contextMatches = [...drawerText.matchAll(/(上下文长度|最大上下文|上下文窗口)[：:]?\\s*(\\d+)\\s*[Kk]/gi)];
            if (contextMatches.length > 0) {
                const maxContext = Math.max(...contextMatches.map(m => parseInt(m[2])));
                info.contextLength = maxContext + 'K';
            }
            
            // 提取最大输出长度
            const outputMatch = drawerText.match(/(最大输出|输出长度|最大生成长度)[：:]?\\s*(\\d+)\\s*[Kk]?/i);
            if (outputMatch) info.maxOutput = outputMatch[2] + 'K';
            
            // 提取上架时间
            const timeMatch = drawerText.match(/(上架时间|发布时间|上线时间)[：:]?\\s*(\\d{4}[-/]\\d{2}[-/]\\d{2})/i);
            if (timeMatch) info.releaseTime = timeMatch[2].trim();
            
            // 检查是否支持 Function Call
            info.supportFunctionCall = /Function Calling|函数调用|支持工具调用|工具调用/i.test(drawerText);
            
            // 提取能力标签 - 从抽屉内的 rounded-full bg-emerald-100 元素获取
            const tagElements = document.querySelectorAll('.rounded-full.bg-emerald-100');
            const extractedTags = [];
            tagElements.forEach(el => {
                const tagText = el.textContent.trim();
                if (tagText && tagText.length < 20) {
                    extractedTags.push(tagText);
                }
            });
            info.detailTags = extractedTags;
            
            return info;
        }
    """)
    
    # 关闭抽屉
    try:
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.5)
        await page.mouse.click(50, 300)
        await asyncio.sleep(0.5)
    except:
        pass
    
    # 使用抽屉内提取的标签（不再合并卡片标签，因为抽屉内的更准确）
    all_tags = detail_info.get('detailTags', [])
    
    return {
        "index": target_index,
        "name": full_name,
        "modelName": full_name,
        "modelCode": detail_info.get('modelCode', ''),
        "modelId": detail_info.get('modelId', ''),
        "description": description,
        "inputPrice": detail_info.get('inputPrice', ''),
        "outputPrice": detail_info.get('outputPrice', ''),
        "cachePrice": detail_info.get('cachePrice', ''),
        "contextLength": detail_info.get('contextLength', ''),
        "maxOutput": detail_info.get('maxOutput', ''),
        "releaseTime": detail_info.get('releaseTime', ''),
        "billingType": detail_info.get('billingType', ''),
        "supportFunctionCall": detail_info.get('supportFunctionCall', False),
        "tags": all_tags
    }


def format_model_info(model: Dict) -> str:
    """格式化模型信息为可读文本"""
    lines = [f"[模型详情] {model.get('name', 'Unknown')}", ""]
    
    # 基本信息
    lines.append("[基本信息]")
    if model.get('modelId'):
        lines.append(f"  模型ID: {model['modelId']}")
    if model.get('modelCode'):
        lines.append(f"  编码: {model['modelCode']}")
    if model.get('description'):
        lines.append(f"  简介: {model['description']}")
    lines.append("")
    
    # 价格信息
    lines.append("[价格信息]")
    lines.append(f"  输入: {model.get('inputPrice', 'N/A')}")
    lines.append(f"  输出: {model.get('outputPrice', 'N/A')}")
    lines.append(f"  缓存: {model.get('cachePrice', 'N/A')}")
    if model.get('billingType'):
        lines.append(f"  计费方式: {model['billingType']}")
    lines.append("")
    
    # 技术规格
    lines.append("[技术规格]")
    if model.get('contextLength'):
        lines.append(f"  上下文长度: {model['contextLength']}")
    if model.get('maxOutput'):
        lines.append(f"  最大输出: {model['maxOutput']}")
    if model.get('releaseTime'):
        lines.append(f"  上架时间: {model['releaseTime']}")
    lines.append("")
    
    # 能力标签
    if model.get('tags'):
        lines.append(f"[能力标签] {', '.join(model['tags'])}")
    
    return '\n'.join(lines)


def compare_models(local: Dict, remote: Dict) -> List[Dict]:
    """比对本地和远程数据，返回差异列表"""
    differences = []
    
    fields = [
        ('modelId', '模型ID'),
        ('modelCode', '编码'),
        ('description', '简介'),
        ('inputPrice', '输入价格'),
        ('outputPrice', '输出价格'),
        ('cachePrice', '缓存价格'),
        ('contextLength', '上下文长度'),
        ('maxOutput', '最大输出'),
        ('releaseTime', '上架时间'),
        ('billingType', '计费方式'),
    ]
    
    for field, label in fields:
        local_val = local.get(field, '')
        remote_val = remote.get(field, '')
        if local_val != remote_val and (local_val or remote_val):
            differences.append({
                'field': field,
                'label': label,
                'local': local_val or 'N/A',
                'remote': remote_val or 'N/A'
            })
    
    # 比对标签
    local_tags = set(local.get('tags', []))
    remote_tags = set(remote.get('tags', []))
    if local_tags != remote_tags:
        differences.append({
            'field': 'tags',
            'label': '能力标签',
            'local': ', '.join(local_tags) or 'N/A',
            'remote': ', '.join(remote_tags) or 'N/A'
        })
    
    return differences


def update_local_data(data: List[Dict], updated_model: Dict) -> bool:
    """更新本地数据文件"""
    try:
        for group in data:
            for i, model in enumerate(group.get('models', [])):
                if model.get('name') == updated_model.get('name'):
                    group['models'][i] = updated_model
                    break
        
        # 保存 JSON
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        log(f"更新本地数据失败: {e}", "ERROR")
        return False


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='查询 WhaleCloud 模型详情')
    parser.add_argument('query', help='模型名称或关键词')
    parser.add_argument('--update', action='store_true', help='自动更新本地数据（不询问）')
    args = parser.parse_args()
    
    query = args.query
    log(f"查询模型: {query}")
    
    # 加载本地数据
    local_data = load_local_data()
    local_model = None
    
    if local_data:
        result = find_model_in_local(local_data, query)
        if result:
            if '_multiple_matches' in result:
                matches = result['_multiple_matches']
                log(f"找到 {len(matches)} 个匹配模型:")
                for i, m in enumerate(matches, 1):
                    log(f"  {i}. {m.get('name')}")
                log("请使用更精确的名称查询")
                return
            else:
                local_model = result
                log(f"本地数据中找到: {local_model.get('name')}")
    
    # 实时查询
    log("启动浏览器进行实时查询...")
    
    async with async_playwright() as p:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=["--start-maximized"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 访问页面
        log(f"访问 {MODEL_INFO_URL}")
        await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        # 检查登录
        text = await page.evaluate('() => document.body.innerText')
        if '需要登录' in text:
            log("需要登录")
            login_btn = await page.query_selector('button:has-text("前往登录")')
            if login_btn:
                await login_btn.click()
                await asyncio.sleep(2)
                await page.fill('input[type="password"]', API_KEY)
                await page.click('button[type="submit"]')
                log("已登录")
                await asyncio.sleep(3)
                await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)
        
        # 查询模型详情
        remote_model = await query_model_detail(page, query)
        await context.close()
        
        if not remote_model:
            log(f"未找到模型: {query}", "ERROR")
            return
        
        # 输出查询结果
        output_text = "\n" + "=" * 60 + "\n" + format_model_info(remote_model) + "\n" + "=" * 60 + "\n"
        # 使用 UTF-8 编码输出
        sys.stdout.buffer.write(output_text.encode('utf-8'))
        print()
        
        # 比对数据
        if local_model and local_data:
            differences = compare_models(local_model, remote_model)
            
            if differences:
                log("检测到数据差异:")
                diff_lines = ["\n[字段变更]"]
                diff_lines.append(f"{'字段':<12} {'本地数据':<25} {'最新数据'}")
                diff_lines.append("-" * 70)
                for diff in differences:
                    diff_lines.append(f"{diff['label']:<12} {diff['local']:<25} → {diff['remote']}")
                diff_text = "\n".join(diff_lines) + "\n"
                sys.stdout.buffer.write(diff_text.encode('utf-8'))
                
                if args.update:
                    # 自动更新
                    if update_local_data(local_data, remote_model):
                        log("本地数据已更新")
                    else:
                        log("更新失败", "ERROR")
                else:
                    # 询问用户
                    print("\n是否更新本地数据？输入 '是' 确认更新，其他键跳过")
                    print("[请确认更新: 将上述差异应用到本地数据文件]")
            else:
                log("数据一致，无需更新")
        else:
            log("本地数据不存在，跳过比对")


def safe_print(text: str):
    """安全打印，处理编码问题"""
    try:
        sys.stdout.buffer.write(text.encode('utf-8'))
    except:
        print(text.encode('ascii', 'ignore').decode())


if __name__ == "__main__":
    asyncio.run(main())
