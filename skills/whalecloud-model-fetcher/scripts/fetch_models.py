#!/usr/bin/env python3
"""
WhaleCloud 模型信息获取器 - 简化版
直接从页面提取模型和分组信息
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


async def fetch_models():
    log("=" * 60)
    log("WhaleCloud 模型信息获取器")
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
        
        log("开始提取模型数据...")
        
        # 等待卡片加载
        await page.wait_for_selector('.card-hover', timeout=30000)
        await asyncio.sleep(2)
        
        # 提取所有模型卡片
        models_data = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.card-hover');
                const models = [];
                
                cards.forEach((card, index) => {
                    try {
                        // 提取品牌
                        const brandEl = card.querySelector('span.text-xl, span.font-semibold');
                        const brand = brandEl ? brandEl.innerText.trim() : '';
                        
                        // 提取模型名
                        const nameEl = card.querySelector('h3');
                        const modelName = nameEl ? nameEl.innerText.trim() : '';
                        
                        // 组合名称
                        let fullName = modelName;
                        if (brand && modelName && !modelName.startsWith(brand)) {
                            fullName = brand + ' / ' + modelName;
                        }
                        
                        // 提取描述
                        const descEl = card.querySelector('p.line-clamp-2-custom');
                        const description = descEl ? descEl.innerText.trim() : '';
                        
                        // 提取标签
                        const tags = [];
                        card.querySelectorAll('.rounded-xl').forEach(tag => {
                            const t = tag.innerText?.trim();
                            if (t && t.length < 20) tags.push(t);
                        });
                        
                        // 获取卡片在页面中的位置（用于判断分组）
                        const rect = card.getBoundingClientRect();
                        
                        models.push({
                            index: index,
                            name: fullName,
                            brand: brand,
                            modelName: modelName,
                            description: description,
                            tags: tags,
                            y: rect.y
                        });
                    } catch (e) {
                        console.error('Error:', e);
                    }
                });
                
                return models;
            }
        """)
        
        log(f"找到 {len(models_data)} 个模型卡片")
        
        # 从页面文本提取分组信息
        page_text = await page.evaluate('() => document.body.innerText')
        
        # 查找所有 "分组名 XX 个模型" 的模式
        group_pattern = r'([\u4e00-\u9fa5\w\s-]+?)\s*(\d+)\s*个模型'
        group_matches = re.findall(group_pattern, page_text)
        
        log(f"找到 {len(group_matches)} 个分组标题")
        for name, count in group_matches[:20]:
            log(f"  - {name.strip()}: {count} 个模型")
        
        # 手动定义分组（根据页面实际顺序）
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
        
        # 按顺序分配模型到分组
        groups = []
        model_idx = 0
        
        for group_name, expected_count in group_definitions:
            group_models = []
            
            # 为这个分组取 expected_count 个模型
            for i in range(expected_count):
                if model_idx < len(models_data):
                    group_models.append(models_data[model_idx])
                    model_idx += 1
                else:
                    break
            
            if group_models:
                groups.append({
                    "name": group_name,
                    "expected_count": expected_count,
                    "models": group_models
                })
        
        # 处理剩余的模型（归入其他）
        remaining = models_data[model_idx:]
        if remaining:
            groups.append({
                "name": "其他模型",
                "expected_count": len(remaining),
                "models": remaining
            })
        
        log(f"\n分组结果:")
        total = 0
        for g in groups:
            log(f"  - {g['name']}: {len(g['models'])} 个模型")
            total += len(g['models'])
        log(f"  总计: {total} 个模型")
        
        await context.close()
        
        return groups


def generate_report(groups):
    """生成 Markdown 报告"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = sum(len(g['models']) for g in groups)
    
    lines = [
        "# WhaleCloud Lab 模型列表报告",
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
            
            if model.get('description'):
                lines.append(f"**简介**: {model['description']}")
                lines.append("")
            
            if model.get('tags'):
                lines.append(f"**标签**: {', '.join(model['tags'])}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    md_path = OUTPUT_DIR / "models_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    log(f"报告已保存: {md_path}")


async def main():
    groups = await fetch_models()
    generate_report(groups)
    log("\n任务完成!")


if __name__ == "__main__":
    asyncio.run(main())
