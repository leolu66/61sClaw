#!/usr/bin/env python3
"""
WhaleCloud 模型信息获取器 - 完整版（含详情）
爬取 WhaleCloud Lab 平台上的所有模型信息，包括详情
"""

import asyncio
import json
import os
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright, Page

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="
MODEL_INFO_URL = "https://lab.iwhalecloud.com/gpt-proxy/console/model-info"
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except:
        print(f"[{timestamp}] [{level}] {message.encode('ascii', 'ignore').decode()}")


def is_port_open(port: int) -> bool:
    try:
        import socket
        with socket.create_connection(('127.0.0.1', port), timeout=1):
            return True
    except:
        return False


async def check_login(page: Page) -> bool:
    text = await page.evaluate('() => document.body.innerText')
    return '共' in text and '个模型' in text


async def do_login(page: Page):
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


async def close_drawer(page: Page):
    """关闭详情抽屉"""
    try:
        # 按 ESC 键关闭
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.5)
        
        # 点击遮罩层
        overlay = await page.query_selector('.fixed.inset-0 .bg-slate-900, .fixed.inset-0 .bg-black')
        if overlay:
            await overlay.click()
            await asyncio.sleep(0.5)
    except:
        pass


async def extract_detail(page: Page) -> Dict:
    """从详情弹窗提取信息"""
    try:
        await asyncio.sleep(1.5)  # 等待弹窗动画
        
        detail = await page.evaluate("""
            () => {
                const data = {
                    name: '',
                    model_code: '',
                    capability_tags: [],
                    capabilities: [],
                    context_info: '',
                    pricing: {},
                    features: [],
                    api_formats: []
                };
                
                // 查找详情弹窗
                const drawer = document.querySelector('.fixed.inset-0') || document.body;
                const text = drawer.innerText;
                
                // 提取模型名称（弹窗标题）
                const titleEl = drawer.querySelector('h2, .text-2xl, .text-3xl');
                if (titleEl) {
                    data.name = titleEl.innerText.trim();
                }
                
                // 提取模型编码
                const codeMatch = text.match(/模型编码[：:]\s*(.+?)(?:\n|$)/);
                if (codeMatch) {
                    data.model_code = codeMatch[1].trim();
                }
                
                // 提取能力标签
                const tagEls = drawer.querySelectorAll('.rounded-full, .bg-emerald-100, .bg-blue-100');
                tagEls.forEach(tag => {
                    const t = tag.innerText?.trim();
                    if (t && t.length < 30 && !t.includes('\n')) {
                        data.capability_tags.push(t);
                    }
                });
                
                // 提取模型能力（列表项）
                const listItems = drawer.querySelectorAll('li, .space-y-2 li');
                listItems.forEach(item => {
                    const t = item.innerText?.trim();
                    if (t && t.length > 5 && t.length < 200) {
                        data.capabilities.push(t);
                    }
                });
                
                // 提取上下文信息
                const contextMatch = text.match(/上下文[：:]\s*(\d+[kK]?)/);
                if (contextMatch) {
                    data.context_info = contextMatch[1];
                }
                
                // 提取价格信息
                const priceSection = text.match(/模型价格[\s\S]*?(?=模型特性|支持的 API|$)/);
                if (priceSection) {
                    const priceText = priceSection[0];
                    
                    const inputMatch = priceText.match(/输入[：:]\s*([\d.]+\s*元?\/\s*[kK]?\s*tokens?)/);
                    if (inputMatch) data.pricing.input = inputMatch[1].trim();
                    
                    const outputMatch = priceText.match(/输出[：:]\s*([\d.]+\s*元?\/\s*[kK]?\s*tokens?)/);
                    if (outputMatch) data.pricing.output = outputMatch[1].trim();
                }
                
                // 提取API格式
                const apiMatch = text.match(/支持的 API 格式[\s\S]*?(?=调用样例|$)/);
                if (apiMatch) {
                    const apiText = apiMatch[0];
                    const formats = apiText.match(/[\w-]+/g);
                    if (formats) {
                        data.api_formats = formats.filter(f => 
                            f.length > 2 && 
                            !['API', '格式', '支持的', '调用', '样例'].includes(f)
                        );
                    }
                }
                
                // 提取模型特性
                const featureSection = text.match(/模型特性[\s\S]*?(?=模型价格|支持的 API|$)/);
                if (featureSection) {
                    const lines = featureSection[0].split('\n').filter(l => 
                        l.trim().length > 5 && l.trim().length < 150
                    );
                    data.features = lines.slice(1, 6);
                }
                
                return data;
            }
        """)
        
        return detail
    except Exception as e:
        log(f"提取详情失败: {e}", "WARN")
        return {}


async def fetch_models_with_details():
    log("=" * 60)
    log("WhaleCloud 模型信息获取器（含详情）")
    log("=" * 60)
    
    async with async_playwright() as p:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        # 启动浏览器
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=["--remote-debugging-port=9222"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 访问页面
        log(f"访问 {MODEL_INFO_URL}")
        await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        # 登录
        if not await check_login(page):
            await do_login(page)
        
        log("已登录，开始提取模型数据...")
        
        # 等待卡片加载
        await page.wait_for_selector('.card-hover', timeout=30000)
        await asyncio.sleep(2)
        
        # 获取所有卡片
        cards = await page.query_selector_all('.card-hover')
        log(f"找到 {len(cards)} 个模型卡片")
        
        # 限制处理的模型数量（避免时间过长）
        max_models = min(len(cards), 50)  # 先处理前50个
        
        models_with_details = []
        
        for i in range(max_models):
            try:
                log(f"\n[{i+1}/{max_models}] 处理第 {i+1} 个模型...")
                
                # 重新获取卡片（因为页面可能刷新）
                cards = await page.query_selector_all('.card-hover')
                if i >= len(cards):
                    break
                
                card = cards[i]
                
                # 获取卡片基本信息
                card_info = await card.evaluate("""
                    (card) => {
                        const brandEl = card.querySelector('span.text-xl, span.font-semibold');
                        const brand = brandEl ? brandEl.innerText.trim() : '';
                        
                        const nameEl = card.querySelector('h3');
                        const modelName = nameEl ? nameEl.innerText.trim() : '';
                        
                        let fullName = modelName;
                        if (brand && modelName && !modelName.startsWith(brand)) {
                            fullName = brand + ' / ' + modelName;
                        }
                        
                        const descEl = card.querySelector('p.line-clamp-2-custom');
                        const description = descEl ? descEl.innerText.trim() : '';
                        
                        return { name: fullName, brand, modelName, description };
                    }
                """)
                
                log(f"  模型: {card_info['name']}")
                
                # 点击卡片打开详情
                await card.click()
                log("  已点击卡片")
                
                # 提取详情
                detail = await extract_detail(page)
                
                # 合并信息
                model_data = {
                    "name": detail.get('name') or card_info['name'],
                    "brand": card_info['brand'],
                    "modelName": card_info['modelName'],
                    "model_code": detail.get('model_code', ''),
                    "description": card_info['description'] or detail.get('description', ''),
                    "capability_tags": detail.get('capability_tags', []),
                    "capabilities": detail.get('capabilities', []),
                    "context_info": detail.get('context_info', ''),
                    "pricing": detail.get('pricing', {}),
                    "features": detail.get('features', []),
                    "api_formats": detail.get('api_formats', [])
                }
                
                models_with_details.append(model_data)
                log(f"  ✓ 已提取详情")
                
                # 关闭详情弹窗
                await close_drawer(page)
                await asyncio.sleep(0.5)
                
            except Exception as e:
                log(f"  ✗ 处理失败: {e}", "ERROR")
                await close_drawer(page)
                continue
        
        log(f"\n成功获取 {len(models_with_details)} 个模型的详情")
        
        await context.close()
        
        return models_with_details


def organize_by_group(models: List[Dict]) -> List[Dict]:
    """按页面分组组织模型"""
    group_definitions = [
        ("国产商用模型", 46),
        ("国外商用模型", 34),
        ("多模态大模型", 7),
        ("本地部署模型", 6),
        ("开源语言模型", 28),
        ("文生图大模型", 3),
        ("语音识别模型", 1),
        ("Embedding模型", 11),
        ("Rerank模型", 8),
        ("极速响应模型", 1),
        ("第三方搜索服务", 2),
        ("浩鲸内部问答", 34),
    ]
    
    groups = []
    model_idx = 0
    
    for group_name, expected_count in group_definitions:
        group_models = []
        
        for i in range(expected_count):
            if model_idx < len(models):
                group_models.append(models[model_idx])
                model_idx += 1
            else:
                break
        
        if group_models:
            groups.append({
                "name": group_name,
                "expected_count": expected_count,
                "models": group_models
            })
    
    # 剩余模型
    remaining = models[model_idx:]
    if remaining:
        groups.append({
            "name": "其他模型",
            "expected_count": len(remaining),
            "models": remaining
        })
    
    return groups


def save_report(groups: List[Dict]):
    """生成 Markdown 报告"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = sum(len(g['models']) for g in groups)
    
    lines = [
        "# WhaleCloud Lab 模型列表报告（含详情）",
        "",
        f"**生成时间**: {datetime.now().isoformat()}",
        f"**平台**: WhaleCloud Lab",
        f"**模型总数**: {total}",
        "",
        "---",
        ""
    ]
    
    for group in groups:
        expected = group.get('expected_count', 0)
        actual = len(group['models'])
        lines.append(f"## {group['name']} ({actual} 个模型 / 页面显示: {expected})")
        lines.append("")
        
        for model in group['models']:
            lines.append(f"### {model['name']}")
            lines.append("")
            
            if model.get('model_code'):
                lines.append(f"**模型编码**: `{model['model_code']}`")
                lines.append("")
            
            if model.get('description'):
                lines.append(f"**简介**: {model['description']}")
                lines.append("")
            
            if model.get('capability_tags'):
                lines.append(f"**能力标签**: {', '.join(model['capability_tags'])}")
                lines.append("")
            
            if model.get('capabilities'):
                lines.append("**模型能力**:")
                for cap in model['capabilities'][:5]:
                    lines.append(f"- {cap}")
                lines.append("")
            
            if model.get('context_info'):
                lines.append(f"**上下文**: {model['context_info']}")
                lines.append("")
            
            if model.get('pricing'):
                pricing = model['pricing']
                lines.append("**价格**:")
                if pricing.get('input'):
                    lines.append(f"- 输入: {pricing['input']}")
                if pricing.get('output'):
                    lines.append(f"- 输出: {pricing['output']}")
                lines.append("")
            
            if model.get('api_formats'):
                lines.append(f"**API 格式**: {', '.join(model['api_formats'])}")
                lines.append("")
            
            if model.get('features'):
                lines.append("**特性**:")
                for feat in model['features'][:3]:
                    lines.append(f"- {feat}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    md_path = OUTPUT_DIR / "models_report_detailed.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    log(f"\n详细报告已保存: {md_path}")


async def main():
    models = await fetch_models_with_details()
    
    if models:
        groups = organize_by_group(models)
        save_report(groups)
        
        log("\n" + "=" * 60)
        log("任务完成!")
        log(f"  - 共获取 {len(models)} 个模型详情")
        log(f"  - 分为 {len(groups)} 个分组")
        log("=" * 60)
    else:
        log("\n任务失败: 未获取到模型数据", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
