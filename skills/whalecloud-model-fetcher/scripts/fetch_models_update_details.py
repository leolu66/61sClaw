#!/usr/bin/env python3
"""
WhaleCloud 模型信息获取器 - 增量更新详情
逐个点击模型卡片获取详情，并更新到现有报告
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
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}", flush=True)
    except:
        pass


async def extract_detail_from_drawer(page: Page) -> Dict:
    """从详情抽屉提取结构化信息"""
    try:
        await asyncio.sleep(1.5)
        
        # 使用 Python 处理页面文本
        drawer_text = await page.evaluate("""
            () => {
                const drawer = document.querySelector('.fixed.inset-0') || document.body;
                return drawer.innerText || '';
            }
        """)
        
        text = drawer_text
        data = {
            "model_code": "",
            "description": "",
            "capability_tags": [],
            "capabilities": [],
            "context_info": {},
            "pricing": {},
            "features": [],
            "api_formats": []
        }
        
        # 1. 提取模型编码和描述
        desc_match = re.search(r'对应模型【(.+?)】，(.+?)(?:\n|$)', text)
        if desc_match:
            data["model_code"] = desc_match.group(1).strip()
            data["description"] = desc_match.group(2).strip()
        
        # 2. 提取上下文信息
        context_section = re.search(r'上下文信息([\s\S]*?)(?=模型价格|$)', text)
        if context_section:
            ctx_text = context_section.group(1)
            
            len_match = re.search(r'上下文长度\s*[:：]?\s*(\d+[kK]?)', ctx_text)
            if len_match:
                data["context_info"]["context_length"] = len_match.group(1)
            
            max_match = re.search(r'最大输出长度\s*[:：]?\s*(\d+[kK]?)', ctx_text)
            if max_match:
                data["context_info"]["max_output"] = max_match.group(1)
            
            time_match = re.search(r'上架时间\s*[:：]?\s*(\d{4}-\d{2}-\d{2})', ctx_text)
            if time_match:
                data["context_info"]["release_date"] = time_match.group(1)
        
        # 3. 提取模型价格
        price_section = re.search(r'模型价格([\s\S]*?)(?=模型特性|支持的 API|计费方式|$)', text)
        if price_section:
            pt = price_section.group(1)
            
            # 输入价格
            input_match = re.search(r'[¥￥]([\d.]+)\s*/\s*输入价格', pt)
            if input_match:
                data["pricing"]["input"] = f"¥{input_match.group(1)}/M tokens"
            
            # 输出价格
            output_match = re.search(r'[¥￥]([\d.]+)\s*/\s*输出价格', pt)
            if output_match:
                data["pricing"]["output"] = f"¥{output_match.group(1)}/M tokens"
            
            # 缓存价格
            cache_match = re.search(r'[¥￥]([\d.]+)\s*/\s*缓存价格', pt)
            if cache_match:
                data["pricing"]["cache"] = f"¥{cache_match.group(1)}/M tokens"
        
        # 4. 提取API格式
        api_match = re.search(r'支持的 API 格式([\s\S]*?)(?=调用样例|$)', text)
        if api_match:
            formats = re.findall(r'[\w-]+', api_match.group(1))
            valid_formats = ['cURL', 'Python', 'JavaScript', 'Go', 'Java', 'PHP', 'Ruby', 'C#']
            data["api_formats"] = list(set([f for f in formats if f in valid_formats]))
        
        # 5. 提取能力标签（从文本中提取常见标签）
        common_tags = ['深度思考', '文本生成', '工具调用', '结构化输出', '文本对话', 
                       'Function Calling', '推理模型', '极速推理', '长上下文', 'Cache 缓存']
        for tag in common_tags:
            if tag in text:
                data["capability_tags"].append(tag)
        
        # 6. 提取模型能力（从列表项）
        capability_lines = re.findall(r'[•·]\s*(.+?)(?=\n|$)', text)
        data["capabilities"] = [line.strip() for line in capability_lines if len(line.strip()) > 2 and len(line.strip()) < 50][:8]
        
        return data
    except Exception as e:
        log(f"提取详情失败: {e}", "WARN")
        return {}


async def close_drawer(page: Page):
    """关闭详情抽屉"""
    try:
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.5)
        
        overlay = await page.query_selector('.fixed.inset-0 .bg-slate-900, .fixed.inset-0 .bg-black, .fixed.inset-0 .bg-opacity-50')
        if overlay:
            await overlay.click()
            await asyncio.sleep(0.5)
    except:
        pass


def format_model_detail(model: Dict) -> str:
    """格式化模型详情为 Markdown"""
    lines = []
    
    # 模型编码和描述
    if model.get('model_code'):
        lines.append(f"**模型编码**: `{model['model_code']}`")
        lines.append("")
    
    if model.get('description'):
        lines.append(f"**简介**: {model['description']}")
        lines.append("")
    
    # 能力标签
    if model.get('capability_tags'):
        lines.append(f"**能力标签**: {', '.join(model['capability_tags'])}")
        lines.append("")
    
    # 模型能力
    if model.get('capabilities'):
        lines.append("**模型能力**:")
        for cap in model['capabilities']:
            lines.append(f"- {cap}")
        lines.append("")
    
    # 上下文信息
    if model.get('context_info'):
        ctx = model['context_info']
        lines.append("**上下文信息**:")
        if ctx.get('context_length'):
            lines.append(f"- 上下文长度: {ctx['context_length']}")
        if ctx.get('max_output'):
            lines.append(f"- 最大输出长度: {ctx['max_output']}")
        if ctx.get('release_date'):
            lines.append(f"- 上架时间: {ctx['release_date']}")
        lines.append("")
    
    # 模型价格
    if model.get('pricing'):
        pricing = model['pricing']
        lines.append("**模型价格**:")
        if pricing.get('input'):
            lines.append(f"- 输入价格: {pricing['input']}")
        if pricing.get('output'):
            lines.append(f"- 输出价格: {pricing['output']}")
        if pricing.get('cache'):
            lines.append(f"- 缓存价格: {pricing['cache']}")
        lines.append("")
    
    # API 格式
    if model.get('api_formats'):
        lines.append(f"**支持的 API 格式**: {', '.join(model['api_formats'])}")
        lines.append("")
    
    return '\n'.join(lines)


async def update_report_with_details(max_models: int = None):
    log("=" * 60)
    log("WhaleCloud 模型信息增量更新（添加详情）")
    log("=" * 60)
    
    # 读取现有报告
    report_path = OUTPUT_DIR / "models_report.md"
    if not report_path.exists():
        log(f"错误: 找不到报告文件 {report_path}", "ERROR")
        return
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    log(f"已加载现有报告")
    
    async with async_playwright() as p:
        log("启动 Chrome...")
        
        user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
        os.makedirs(user_data_dir, exist_ok=True)
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--remote-debugging-port=9222"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        log(f"访问 {MODEL_INFO_URL}")
        await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        # 登录
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
        
        log("开始提取模型详情...")
        
        await page.wait_for_selector('.card-hover', timeout=30000)
        await asyncio.sleep(2)
        
        cards = await page.query_selector_all('.card-hover')
        total_cards = len(cards)
        log(f"找到 {total_cards} 个模型卡片")
        
        if max_models is None or max_models > total_cards:
            max_models = total_cards
        
        log(f"将更新前 {max_models} 个模型的详情")
        
        updated_count = 0
        
        for i in range(max_models):
            try:
                cards = await page.query_selector_all('.card-hover')
                if i >= len(cards):
                    break
                
                card = cards[i]
                
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
                        return { name: fullName, brand, modelName };
                    }
                """)
                
                model_name = card_info['name']
                log(f"[{i+1}/{max_models}] {model_name}")
                
                # 检查是否已有详情
                model_pattern = rf'### {re.escape(model_name)}\n\n(.+?)(?=---|\Z)'
                existing_match = re.search(model_pattern, report_content, re.DOTALL)
                
                if existing_match and '模型编码' in existing_match.group(1):
                    log(f"  跳过（已有详情）")
                    continue
                
                # 点击卡片获取详情
                await card.click()
                detail = await extract_detail_from_drawer(page)
                
                if detail:
                    model_data = {
                        "name": model_name,
                        "model_code": detail.get('model_code', ''),
                        "description": detail.get('description', ''),
                        "capability_tags": detail.get('capability_tags', []),
                        "capabilities": detail.get('capabilities', []),
                        "context_info": detail.get('context_info', {}),
                        "pricing": detail.get('pricing', {}),
                        "api_formats": detail.get('api_formats', [])
                    }
                    
                    detail_text = format_model_detail(model_data)
                    
                    if existing_match:
                        old_content = existing_match.group(1)
                        report_content = report_content.replace(
                            f'### {model_name}\n\n{old_content}',
                            f'### {model_name}\n\n{detail_text}'
                        )
                    else:
                        report_content = report_content.replace(
                            f'### {model_name}\n\n---',
                            f'### {model_name}\n\n{detail_text}---'
                        )
                    
                    updated_count += 1
                    log(f"  ✓ 已更新详情")
                
                await close_drawer(page)
                await asyncio.sleep(0.3)
                
            except Exception as e:
                log(f"  错误: {e}", "ERROR")
                await close_drawer(page)
                continue
        
        log(f"\n成功更新 {updated_count} 个模型的详情")
        
        await context.close()
        
        # 保存更新后的报告
        report_content = re.sub(
            r'\*\*生成时间\*\*: .+',
            f'**生成时间**: {datetime.now().isoformat()} (含详情)',
            report_content
        )
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        log(f"报告已更新: {report_path}")


async def main():
    max_models = None
    if len(sys.argv) > 1:
        try:
            max_models = int(sys.argv[1])
        except:
            pass
    
    await update_report_with_details(max_models)
    
    log("\n" + "=" * 60)
    log("任务完成!")
    log("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
