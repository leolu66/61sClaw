#!/usr/bin/env python3
"""
WhaleCloud 模型信息获取器 - 详情版
逐个点击模型卡片获取详情

使用方法:
  python fetch_models_with_details.py [数量]
  
  例如:
  python fetch_models_with_details.py 10    # 提取前10个模型的详情
  python fetch_models_with_details.py       # 提取所有181个模型的详情（需要约15-20分钟）
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright, Page

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="
MODEL_INFO_URL = "https://lab.iwhalecloud.com/gpt-proxy/console/model-info"
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}", flush=True)
    except:
        pass


async def extract_detail_from_drawer(page: Page) -> Dict:
    """从详情抽屉提取信息"""
    try:
        await asyncio.sleep(1.5)  # 等待动画
        
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
                
                const drawer = document.querySelector('.fixed.inset-0') || document.body;
                const text = drawer.innerText || '';
                
                // 模型名称
                const titleEl = drawer.querySelector('h2, .text-2xl, .text-3xl');
                if (titleEl) data.name = titleEl.innerText.trim();
                
                // 模型编码
                const codeMatch = text.match(/模型编码[：:]\\s*(.+?)(?:\\n|$)/);
                if (codeMatch) data.model_code = codeMatch[1].trim();
                
                // 能力标签
                drawer.querySelectorAll('.rounded-full, .bg-emerald-100, .bg-blue-100, .bg-purple-100').forEach(tag => {
                    const t = tag.innerText?.trim();
                    if (t && t.length < 30 && !t.includes('\\n')) {
                        data.capability_tags.push(t);
                    }
                });
                
                // 模型能力
                drawer.querySelectorAll('li, .space-y-2 li, .space-y-3 li').forEach(item => {
                    const t = item.innerText?.trim();
                    if (t && t.length > 5 && t.length < 200) {
                        data.capabilities.push(t);
                    }
                });
                
                // 上下文
                const contextMatch = text.match(/上下文[：:]\\s*(\\d+[kK]?)/);
                if (contextMatch) data.context_info = contextMatch[1];
                
                // 价格
                const priceSection = text.match(/模型价格[\\s\\S]*?(?=模型特性|支持的 API|$)/);
                if (priceSection) {
                    const pt = priceSection[0];
                    const im = pt.match(/输入[：:]\\s*([\\d.]+\\s*元?\\/\\s*[kK]?\\s*tokens?)/);
                    if (im) data.pricing.input = im[1].trim();
                    const om = pt.match(/输出[：:]\\s*([\\d.]+\\s*元?\\/\\s*[kK]?\\s*tokens?)/);
                    if (om) data.pricing.output = om[1].trim();
                }
                
                // API格式
                const apiMatch = text.match(/支持的 API 格式[\\s\\S]*?(?=调用样例|$)/);
                if (apiMatch) {
                    const fmts = apiMatch[0].match(/[\\w-]+/g);
                    if (fmts) {
                        data.api_formats = fmts.filter(f => 
                            f.length > 2 && !['API','格式','支持的','调用','样例'].includes(f)
                        );
                    }
                }
                
                // 特性
                const featSection = text.match(/模型特性[\\s\\S]*?(?=模型价格|支持的 API|$)/);
                if (featSection) {
                    data.features = featSection[0].split('\\n')
                        .filter(l => l.trim().length > 5 && l.trim().length < 150)
                        .slice(1, 6);
                }
                
                return data;
            }
        """)
        
        return detail
    except Exception as e:
        log(f"提取详情失败: {e}", "WARN")
        return {}


async def close_drawer(page: Page):
    """关闭详情抽屉"""
    try:
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.5)
        
        # 点击遮罩层
        overlay = await page.query_selector('.fixed.inset-0 .bg-slate-900, .fixed.inset-0 .bg-black, .fixed.inset-0 .bg-opacity-50')
        if overlay:
            await overlay.click()
            await asyncio.sleep(0.5)
    except:
        pass


async def fetch_models_with_details(max_models: int = None):
    log("=" * 60)
    log("WhaleCloud 模型信息获取器（含详情）")
    log("=" * 60)
    
    async with async_playwright() as p:
        # 连接到已运行的 Chrome
        log("连接到 Chrome...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()
        
        # 访问页面
        log(f"访问 {MODEL_INFO_URL}")
        await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        # 检查登录
        text = await page.evaluate('() => document.body.innerText')
        if '需要登录' in text:
            log("需要登录")
            await page.click('button:has-text("前往登录")')
            await asyncio.sleep(2)
            await page.fill('input[type="password"]', API_KEY)
            await page.click('button[type="submit"]')
            log("已登录")
            await asyncio.sleep(3)
            await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
        
        log("开始提取模型数据...")
        
        # 等待卡片
        await page.wait_for_selector('.card-hover', timeout=30000)
        await asyncio.sleep(2)
        
        # 获取所有卡片
        cards = await page.query_selector_all('.card-hover')
        total_cards = len(cards)
        log(f"找到 {total_cards} 个模型卡片")
        
        # 确定要处理的模型数量
        if max_models is None or max_models > total_cards:
            max_models = total_cards
        
        log(f"将提取前 {max_models} 个模型的详情")
        
        models_with_details = []
        
        for i in range(max_models):
            try:
                # 重新获取卡片（页面可能变化）
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
                
                log(f"[{i+1}/{max_models}] {card_info['name']}")
                
                # 点击卡片
                await card.click()
                
                # 提取详情
                detail = await extract_detail_from_drawer(page)
                
                # 合并数据
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
                
                # 关闭抽屉
                await close_drawer(page)
                await asyncio.sleep(0.3)
                
            except Exception as e:
                log(f"  错误: {e}", "ERROR")
                await close_drawer(page)
                continue
        
        log(f"\n成功获取 {len(models_with_details)} 个模型详情")
        
        await browser.close()
        
        return models_with_details


def organize_and_save(models: List[Dict]):
    """组织分组并保存报告"""
    # 按页面顺序分组
    group_defs = [
        ("国产商用模型", 46), ("国外商用模型", 34), ("多模态大模型", 7),
        ("本地部署模型", 6), ("开源语言模型", 28), ("文生图大模型", 3),
        ("语音识别模型", 1), ("Embedding模型", 11), ("Rerank模型", 8),
        ("极速响应模型", 1), ("第三方搜索服务", 2), ("浩鲸内部问答", 34),
    ]
    
    groups = []
    idx = 0
    for name, count in group_defs:
        group_models = []
        for _ in range(count):
            if idx < len(models):
                group_models.append(models[idx])
                idx += 1
            else:
                break
        if group_models:
            groups.append({"name": name, "expected_count": count, "models": group_models})
    
    if idx < len(models):
        groups.append({"name": "其他模型", "expected_count": len(models) - idx, "models": models[idx:]})
    
    # 生成报告
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# WhaleCloud Lab 模型列表报告（含详情）",
        "",
        f"**生成时间**: {datetime.now().isoformat()}",
        f"**平台**: WhaleCloud Lab",
        f"**模型总数**: {len(models)}",
        "",
        "---",
        ""
    ]
    
    for group in groups:
        lines.append(f"## {group['name']} ({len(group['models'])} 个模型)")
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
    
    md_path = OUTPUT_DIR / "models_report_with_details.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    # 保存 JSON
    json_path = OUTPUT_DIR / "models_data_with_details.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"groups": groups, "total": len(models)}, f, ensure_ascii=False, indent=2)
    
    log(f"\n报告已保存:")
    log(f"  - Markdown: {md_path}")
    log(f"  - JSON: {json_path}")


async def main():
    # 获取命令行参数
    max_models = None
    if len(sys.argv) > 1:
        try:
            max_models = int(sys.argv[1])
        except:
            pass
    
    models = await fetch_models_with_details(max_models)
    
    if models:
        organize_and_save(models)
        log("\n" + "=" * 60)
        log(f"任务完成! 共获取 {len(models)} 个模型详情")
        log("=" * 60)
    else:
        log("\n任务失败", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
