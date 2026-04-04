#!/usr/bin/env python3
"""
WhaleCloud 模型信息获取器
爬取 WhaleCloud Lab 平台上的所有模型信息
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

# API Key
API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

# 常量
MODEL_INFO_URL = "https://lab.iwhalecloud.com/gpt-proxy/console/model-info"
CHROME_DEBUG_PORT = 9222
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")

# 输出目录
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"


def log(message: str, level: str = "INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except:
        print(f"[{timestamp}] [{level}] {message.encode('ascii', 'ignore').decode()}")


def is_port_open(port: int, host: str = '127.0.0.1', timeout: int = 1) -> bool:
    """检测端口是否开放"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


async def check_if_logged_in(page: Page) -> bool:
    """检查是否已登录"""
    try:
        text = await page.evaluate('() => document.body.innerText')
        
        # 已登录标志 - 页面显示模型数量大于0
        if '共' in text and '个模型' in text:
            model_count_match = re.search(r'共\s*(\d+)\s*个模型', text)
            if model_count_match:
                count = int(model_count_match.group(1))
                if count > 0:
                    return True
        
        # 未登录标志
        if '需要登录' in text or '前往登录' in text:
            return False
        
        if 'API Key' in text and ('请输入' in text or '登录' in text):
            return False
        
        return False
    except Exception as e:
        log(f"检查登录状态失败: {e}", "WARN")
        return False


async def click_login_button(page: Page) -> bool:
    """点击前往登录按钮"""
    try:
        log("点击前往登录按钮...")
        
        login_btn = await page.query_selector('button:has-text("前往登录"), a:has-text("前往登录")')
        if login_btn:
            await login_btn.click()
            log("已点击前往登录")
            await asyncio.sleep(2)
            return True
        
        return False
    except Exception as e:
        log(f"点击登录按钮失败: {e}", "ERROR")
        return False


async def auto_login(page: Page) -> bool:
    """自动登录"""
    try:
        log("检测到未登录，开始自动登录...")
        
        # 等待密码输入框
        await page.wait_for_selector('input[type="password"]', state='visible', timeout=10000)
        await asyncio.sleep(0.5)
        
        # 填写 API Key
        await page.fill('input[type="password"]', '')
        await page.fill('input[type="password"]', API_KEY)
        log("API Key 已填写")
        
        # 点击登录按钮
        login_button = await page.query_selector('button[type="submit"]')
        if not login_button:
            login_button = await page.query_selector('button:has-text("登录")')
        
        if login_button:
            await login_button.click()
            log("已点击登录按钮")
        else:
            log("未找到登录按钮", "WARN")
            return False
        
        # 等待登录完成
        await asyncio.sleep(3)
        
        # 验证登录
        text = await page.evaluate('() => document.body.innerText')
        
        if 'API Key' in text and ('请输入' in text or 'placeholder' in text.lower()):
            log("登录失败 - 仍在登录页面", "ERROR")
            return False
        
        if '今日使用' in text or '仪表板' in text or 'Dashboard' in text.lower():
            log("登录成功 - 已跳转到仪表板")
            return True
        
        if '错误' in text or '失败' in text or 'error' in text.lower():
            log("登录失败 - 页面显示错误", "ERROR")
            return False
        
        log("登录成功")
        return True
            
    except Exception as e:
        log(f"自动登录失败: {e}", "ERROR")
        return False


async def extract_all_models_from_page(page: Page) -> List[Dict]:
    """从页面提取所有模型基本信息（不点击详情）"""
    log("正在提取模型列表...")
    
    try:
        # 等待页面加载
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)
        
        # 提取所有模型卡片信息
        models = await page.evaluate("""
            () => {
                const models = [];
                const cards = document.querySelectorAll('.card-hover');
                
                cards.forEach((card, index) => {
                    try {
                        // 提取提供商（品牌）
                        const brandEl = card.querySelector('span.text-xl, span.font-semibold');
                        const brand = brandEl ? brandEl.innerText.trim() : '';
                        
                        // 提取模型名称（h3 元素）
                        const nameEl = card.querySelector('h3');
                        const modelName = nameEl ? nameEl.innerText.trim() : '';
                        
                        // 组合成完整名称：品牌 + 模型名
                        let fullName = modelName;
                        if (brand && modelName && !modelName.startsWith(brand)) {
                            fullName = brand + ' / ' + modelName;
                        }
                        
                        // 提取描述
                        const descEl = card.querySelector('p.line-clamp-2-custom');
                        const description = descEl ? descEl.innerText.trim() : '';
                        
                        // 提取标签
                        const tags = [];
                        const tagEls = card.querySelectorAll('.rounded-xl');
                        tagEls.forEach(tag => {
                            const text = tag.innerText?.trim();
                            if (text && text.length < 20 && !text.includes('\\n')) {
                                tags.push(text);
                            }
                        });
                        
                        if (fullName && fullName.length > 0 && fullName.length < 200) {
                            models.push({
                                index: index,
                                name: fullName,
                                brand: brand,
                                modelName: modelName,
                                description: description,
                                tags: tags
                            });
                        }
                    } catch (e) {
                        console.error('Error:', e);
                    }
                });
                
                return models;
            }
        """)
        
        log(f"找到 {len(models)} 个模型卡片")
        return models
        
    except Exception as e:
        log(f"提取模型列表失败: {e}", "ERROR")
        return []


async def fetch_all_models() -> Dict:
    """获取所有模型信息的主函数"""
    log("=" * 60)
    log("WhaleCloud 模型信息获取器")
    log("=" * 60)
    
    result = {
        "platform": "WhaleCloud Lab",
        "url": MODEL_INFO_URL,
        "fetch_time": datetime.now().isoformat(),
        "groups": [],
        "total_models": 0,
        "status": "error",
        "error_message": None
    }
    
    browser = None
    context = None
    
    try:
        async with async_playwright() as p:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            
            # 尝试连接已运行的 Chrome
            if is_port_open(CHROME_DEBUG_PORT):
                try:
                    log("连接到已运行的 Chrome...")
                    browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{CHROME_DEBUG_PORT}", timeout=5000)
                    page = await browser.new_page()
                except Exception as e:
                    log(f"连接失败，将启动新 Chrome: {e}")
                    browser = None
            
            # 启动新的 Chrome
            if not browser:
                log("启动 Chrome...")
                context = await p.chromium.launch_persistent_context(
                    USER_DATA_DIR,
                    headless=False,
                    args=[f"--remote-debugging-port={CHROME_DEBUG_PORT}"]
                )
                page = context.pages[0] if context.pages else await context.new_page()
            
            # 访问模型信息页面
            log(f"访问 {MODEL_INFO_URL}")
            await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)
            
            # 检查登录状态
            if not await check_if_logged_in(page):
                log("未登录，需要登录...")
                
                # 先尝试点击"前往登录"按钮
                if await click_login_button(page):
                    pass
                
                # 执行自动登录
                if not await auto_login(page):
                    result["error_message"] = "登录失败"
                    return result
                
                # 登录后重新导航到模型列表页面
                log("登录成功，重新导航到模型列表页面...")
                await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(5)
            
            # 再次检查登录状态
            if not await check_if_logged_in(page):
                result["error_message"] = "登录后仍无法访问模型列表"
                return result
            
            log("已登录，开始提取模型数据...")
            
            # 提取所有模型卡片
            model_cards = await extract_all_models_from_page(page)
            
            if not model_cards:
                result["error_message"] = "未找到模型卡片"
                return result
            
            log(f"成功提取 {len(model_cards)} 个模型信息")
            
            # 转换为模型数据格式
            all_models = []
            for card in model_cards:
                # 使用模型名称（不是品牌）进行分组
                model_name_for_group = card.get('modelName', card['name'])
                
                model_data = {
                    "name": card['name'],  # 完整名称：品牌 / 模型名
                    "modelName": card.get('modelName', ''),
                    "brand": card.get('brand', ''),
                    "model_code": "",
                    "description": card.get('description', ''),
                    "capability_tags": card.get('tags', []),
                    "capabilities": [],
                    "context_info": "",
                    "pricing": {},
                    "features": [],
                    "api_formats": []
                }
                all_models.append(model_data)
            
            # 组织分组
            groups = organize_models_by_group(all_models)
            
            result["groups"] = groups
            result["total_models"] = len(all_models)
            result["status"] = "success"
            
            log(f"\n[完成] 成功获取 {len(all_models)} 个模型信息")
            
            await page.close()
            
    except Exception as e:
        result["error_message"] = str(e)
        log(f"获取模型信息失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        
    finally:
        if context:
            try:
                await context.close()
            except:
                pass
        elif browser:
            try:
                await browser.close()
            except:
                pass
        log("Chrome 已关闭")
    
    return result


def organize_models_by_group(models: List[Dict]) -> List[Dict]:
    """根据模型名称关键词分组"""
    
    group_definitions = [
        ("国产商用模型", ["deepseek", "doubao", "qwen", "glm", "kimi", "step", "minimax", "通义千问", "豆包", "阿里"]),
        ("国外商用模型", ["gpt", "claude", "gemini", "openai", "anthropic", "google"]),
        ("多模态大模型", ["vl", "vision", "multimodal", "glm-4.5v", "glm-4.6v", "glm-5v"]),
        ("文生图大模型", ["dall", "midjourney", "stable-diffusion", "sd", "flux", "seedream", "qwen-image"]),
        ("语音识别模型", ["whisper", "asr", "tts", "sensevoice"]),
        ("Embedding模型", ["embedding", "embed", "bge-m3", "text-embedding"]),
        ("Rerank模型", ["rerank", "reranker"]),
        ("极速响应模型", ["flash", "turbo", "fast", "haste"]),
        ("开源语言模型", ["llama", "yi", "baichuan", "mistral", "longcat"]),
        ("本地部署模型", ["local"]),
        ("第三方搜索服务", ["search", "bocha"]),
        ("浩鲸内部问答", ["浩鲸", "iwhale", "应标", "差旅", "atom", "cd问答", "codingplus", "docchain", "dpc", "ncell", "oss", "v8", "v9", "yak", "云智能", "产品安全", "割接", "计费", "whalebook", "数字渠道", "门户", "孟加拉", "平台技术", "报表", "研发云", "统一问答", "质量运营", "配置", "镜湖", "需求调研"])
    ]
    
    groups = {name: [] for name, _ in group_definitions}
    groups["其他模型"] = []
    
    for model in models:
        # 优先使用 modelName 进行分组判断
        model_name_for_group = model.get('modelName', model['name'])
        model_name_lower = model_name_for_group.lower()
        
        assigned = False
        
        for group_name, keywords in group_definitions:
            if any(kw.lower() in model_name_lower for kw in keywords):
                groups[group_name].append(model)
                assigned = True
                break
        
        if not assigned:
            groups["其他模型"].append(model)
    
    result = []
    for group_name, models_in_group in groups.items():
        if models_in_group:
            result.append({
                "name": group_name,
                "models": models_in_group
            })
    
    return result


def save_results(data: Dict):
    """保存结果到文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存 JSON
    json_path = OUTPUT_DIR / "models_data.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"JSON 数据已保存: {json_path}")
    
    # 生成 Markdown 报告
    md_path = OUTPUT_DIR / "models_report.md"
    generate_markdown_report(data, md_path)
    log(f"Markdown 报告已保存: {md_path}")


def generate_markdown_report(data: Dict, output_path: Path):
    """生成 Markdown 格式报告"""
    
    lines = [
        "# WhaleCloud Lab 模型列表报告",
        "",
        f"**生成时间**: {data.get('fetch_time', 'N/A')}",
        f"**平台**: {data.get('platform', 'N/A')}",
        f"**模型总数**: {data.get('total_models', 0)}",
        "",
        "---",
        ""
    ]
    
    for group in data.get('groups', []):
        lines.append(f"## {group['name']} ({len(group['models'])} 个模型)")
        lines.append("")
        
        for model in group.get('models', []):
            lines.append(f"### {model['name']}")
            lines.append("")
            
            if model.get('description'):
                lines.append(f"**简介**: {model['description']}")
                lines.append("")
            
            if model.get('capability_tags'):
                lines.append(f"**标签**: {', '.join(model['capability_tags'])}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


async def main():
    """主函数"""
    data = await fetch_all_models()
    
    if data['status'] == 'success':
        save_results(data)
        log("\n" + "=" * 60)
        log("任务完成!")
        log(f"  - 共获取 {data['total_models']} 个模型")
        log(f"  - 分为 {len(data['groups'])} 个分组")
        log(f"  - 输出目录: {OUTPUT_DIR}")
        log("=" * 60)
    else:
        log(f"\n任务失败: {data.get('error_message')}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
