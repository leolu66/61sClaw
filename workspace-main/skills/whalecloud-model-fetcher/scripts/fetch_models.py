#!/usr/bin/env python3
"""
WhaleCloud 模型信息获取器 - 完整版
逐个进入模型详情页提取完整信息
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
    log("WhaleCloud 模型信息获取器（弹窗适配版）")
    log("=" * 60)
    
    async with async_playwright() as p:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        # 启动本地Chrome浏览器（Windows桌面环境支持图形界面）
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
        
        log("开始提取模型数据...")
        
        # 等待卡片加载
        await page.wait_for_selector('.card-hover', timeout=30000)
        await asyncio.sleep(2)
        
        # 获取所有模型卡片数量
        card_count = await page.evaluate('() => document.querySelectorAll(".card-hover").length')
        log(f"找到 {card_count} 个模型卡片，将逐个进入详情页提取完整信息...")
        
        models_data = []
        
        # 全量提取所有模型信息
        for i in range(card_count):
            try:
                # 重新获取卡片元素（避免DOM过期）
                cards = await page.query_selector_all('.card-hover')
                if i >= len(cards):
                    break
                    
                card = cards[i]
                
                # 先提取卡片上的基础信息（增加容错）
                # 打印卡片完整文本，调试用
                card_text = await card.evaluate('el => el.textContent')
                log(f"卡片完整文本: {card_text[:200]}...")
                
                try:
                    # 提取完整模型名（匹配DeepSeek-R1这种格式）
                    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                    if len(lines) >= 2:
                        # 第一行是品牌，第二行是完整模型名
                        modelName = lines[1].strip()
                    else:
                        modelName = f"模型{i+1}"
                except:
                    modelName = f"模型{i+1}"
                fullName = modelName
                try:
                    # 提取模型简介，匹配"对应模型【..."开头的文本
                    desc_match = re.search(r'对应模型【.*', card_text, re.S)
                    if desc_match:
                        description = desc_match.group().split('\n')[0].strip()
                    else:
                        description = ''
                except:
                    description = ''
                
                # 提取卡片标签
                try:
                    tags = await card.eval_on_selector_all('.rounded-xl', 'els => els.map(el => el.innerText.trim()).filter(t => t && t.length < 20 && t != "复制模型名")', default=[])
                except:
                    tags = []
                
                log(f"[{i+1}/{card_count}] 正在处理: {fullName}")
                
                # 点击卡片弹出右侧抽屉
                await card.click()
                await asyncio.sleep(3)
                
                # 抽屉内容已加载，直接提取
                
                # 提取抽屉内完整信息
                detail_info = await page.evaluate("""
                    () => {
                        // 直接拿整个页面文本，价格信息肯定在里面
                        const drawerText = document.body.innerText;
                        console.log('抽屉文本前500字符:', drawerText.slice(0, 500)); // 调试用
                        const info = {
                            modelCode: '',
                            inputPrice: '',
                            outputPrice: '',
                            cachePrice: '',
                            contextLength: '',
                            maxOutput: '',
                            releaseTime: '',
                            supportFunctionCall: false,
                            detailTags: []
                        };
                        
                        // 提取模型ID/编码
                        const idMatch = drawerText.match(/模型ID[：:]?\\s*`?([a-zA-Z0-9-_.]+)`?/i);
                        if (idMatch) info.modelId = idMatch[1].trim();
                        const codeMatch = drawerText.match(/(模型编码|调用编码|model code)[：:]?\\s*`?([a-zA-Z0-9-_.]+)`?/i);
                        if (codeMatch) info.modelCode = codeMatch[2].trim();
                        
                        // 提取计费方式
                        const billingMatch = drawerText.match(/(计费方式)[：:]?\\s*([\\u4e00-\u9fa5]+)/i);
                        if (billingMatch) info.billingType = billingMatch[2].trim();
                        
                        // 直接通过DOM选择器提取价格，100%准确
                        const inputEl = document.querySelector('div.bg-gradient-to-br.from-blue-50.to-blue-100 .text-3xl.font-bold.text-blue-600');
                        const outputEl = document.querySelector('div.bg-gradient-to-br.from-emerald-50.to-emerald-100 .text-3xl.font-bold.text-emerald-600');
                        const cacheEl = document.querySelector('div.bg-gradient-to-br.from-purple-50.to-purple-100 .text-3xl.font-bold.text-purple-600');
                        
                        if (inputEl) info.inputPrice = inputEl.textContent.trim() + ' 元/M tokens';
                        if (outputEl) info.outputPrice = outputEl.textContent.trim() + ' 元/M tokens';
                        if (cacheEl) info.cachePrice = cacheEl.textContent.trim() + ' 元/M tokens';
                        
                        // 提取上下文长度（优先匹配128K、256K等更大的数值）
                        const contextMatches = [...drawerText.matchAll(/(上下文长度|最大上下文|上下文窗口)[：:]?\\s*(\\d+)\\s*[Kk]/gi)];
                        if (contextMatches.length > 0) {
                            // 取最大的上下文长度值
                            const maxContext = Math.max(...contextMatches.map(m => parseInt(m[2])));
                            info.contextLength = maxContext + 'K';
                        }
                        
                        // 提取最大输出长度
                        const outputMatch = drawerText.match(/(最大输出|输出长度|最大生成长度)[：:]?\\s*(\\d+)\\s*[Kk]?/i);
                        if (outputMatch) info.maxOutput = outputMatch[2] + 'K';
                        
                        // 提取上架时间
                        const timeMatch = drawerText.match(/(上架时间|发布时间|上线时间)[：:]?\\s*(\\d{4}[-/]\\d{2}[-/]\\d{2})/i);
                        if (timeMatch) info.releaseTime = timeMatch[2].trim();
                        
                        // 提取是否支持Function Call
                        info.supportFunctionCall = /Function Calling|函数调用|支持工具调用|工具调用/i.test(drawerText);
                        
                        // 白名单精准匹配能力标签，只保留指定的标签，避免多余内容
                        const validTags = ['深度思考', '文本生成', '工具调用', '结构化输出', 'Cache缓存', '长上下文'];
                        info.detailTags = validTags.filter(tag => drawerText.includes(tag));
                        
                        return info;
                    }
                """)
                
                # 关闭抽屉（ESC键即可关闭）
                try:
                    await page.keyboard.press('Escape')
                    await asyncio.sleep(1)
                except Exception as e:
                    log(f"关闭抽屉异常: {str(e)}", level="WARN")
                # 点击左侧空白区域确保关闭
                await page.mouse.click(50, 300)
                await asyncio.sleep(0.5)
                
                # 合并标签（卡片标签 + 详情页标签）
                all_tags = list(set(tags + detail_info.get('detailTags', [])))
                # 移除没用的"复制模型名"标签
                all_tags = [t for t in all_tags if t != '复制模型名']
                
                # 合并信息
                model_info = {
                    "index": i,
                    "name": fullName,
                    "modelName": modelName,
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
                
                models_data.append(model_info)
                await asyncio.sleep(1)
                
            except Exception as e:
                log(f"处理第 {i+1} 个模型失败: {str(e)}", level="ERROR")
                # 出错时尝试返回列表页继续
                try:
                    await page.go_back()
                    await asyncio.sleep(2)
                except:
                    pass
                continue
        
        log(f"成功提取 {len(models_data)} 个模型的完整信息")
        
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
        "# WhaleCloud Lab 模型列表报告（完整版）",
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
            
            if model.get('modelId'):
                lines.append(f"**模型ID**: `{model['modelId']}`")
                lines.append("")
            if model.get('modelCode'):
                lines.append(f"**编码**: `{model['modelCode']}`")
                lines.append("")
            
            if model.get('description'):
                lines.append(f"**简介**: {model['description']}")
                lines.append("")
            
            # 价格部分（强制显示，调试用）
            lines.append(f"**价格**: ")
            lines.append(f"- 输入价格：{model.get('inputPrice', '未提取到')}")
            lines.append(f"- 输出价格：{model.get('outputPrice', '未提取到')}")
            lines.append(f"- 缓存价格：{model.get('cachePrice', '未提取到')}")
            lines.append("")
            
            if model.get('contextLength'):
                lines.append(f"**上下文长度**: {model['contextLength']}")
                lines.append("")
            
            if model.get('maxOutput'):
                lines.append(f"**最大输出长度**: {model['maxOutput']}")
                lines.append("")
            
            if model.get('releaseTime'):
                lines.append(f"**上架时间**: {model['releaseTime']}")
                lines.append("")
            

            
            if model.get('tags'):
                lines.append(f"**能力标签**: {', '.join(model['tags'])}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    md_path = OUTPUT_DIR / "models_report_full.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    # 保存JSON数据
    json_path = OUTPUT_DIR / "models_data_full.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
    
    log(f"完整报告已保存: {md_path}")
    log(f"JSON数据已保存: {json_path}")


async def main():
    groups = await fetch_models()
    generate_report(groups)
    log("\n任务完成!")


if __name__ == "__main__":
    asyncio.run(main())
