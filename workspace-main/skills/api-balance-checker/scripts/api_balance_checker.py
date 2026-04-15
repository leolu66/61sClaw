"""
API Balance Checker - 查询 WhaleCloud API 余额
使用 Playwright 连接 Chrome 浏览器获取数据
支持自动登录：检测到未登录时自动使用 API Key 登录
"""

import asyncio
import socket
import subprocess
import os
import sys
import time
from typing import Dict, Optional
from playwright.async_api import async_playwright

# API Key（从环境变量或配置文件读取更安全）
API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="


# 设置 stdout 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def is_port_open(port, host='127.0.0.1', timeout=1):
    """检测端口是否开放"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def wait_for_port(port, timeout=30):
    """等待端口就绪"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(port):
            return True
        time.sleep(0.5)
    return False


def launch_chrome_if_needed():
    """启动 Chrome 在调试模式（如果未运行）"""
    
    # 先检查 Chrome 是否已经在调试模式运行
    if is_port_open(9222):
        print("[检测] Chrome 已在调试模式运行，直接连接")
        return True
    
    print("[启动] Chrome 未在调试模式运行，启动 Chrome...")
    
    # Chrome 路径
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if not os.path.exists(chrome_path):
        print("[错误] 找不到 Chrome 安装路径")
        return False

    # 使用固定的用户数据目录
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    # 直接打开 Dashboard URL，避免空白页面
    dashboard_url = "https://lab.iwhalecloud.com/gpt-proxy/console/dashboard"
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={user_data_dir}",
        dashboard_url
    ]

    # 启动 Chrome
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launched_pid = process.pid
    print(f"[启动] Chrome 已启动，PID: {launched_pid}")
    
    # 等待端口就绪
    if wait_for_port(9222, timeout=30):
        print("[完成] Chrome 调试端口已就绪")
        return True
    else:
        print("[警告] Chrome 启动超时")
        return False


async def check_if_logged_in(page) -> bool:
    """检查是否已登录"""
    try:
        text = await page.evaluate('() => document.body.innerText')
        
        # 已登录标志：页面包含特定关键词
        logged_in_keywords = ['余额', '已用', '请求', '模型', 'Model', '定价', '价格', '上下文', 'tokens']
        # 未登录标志：包含登录相关文字
        login_keywords = ['请输入 API Key', 'API Key 登录', '请登录', '登录']
        
        has_logged_in_marker = any(kw in text for kw in logged_in_keywords)
        has_login_form = any(kw in text for kw in login_keywords)
        
        # 如果有登录表单关键词，且没有已登录标志，则视为未登录
        if has_login_form and not has_logged_in_marker:
            return False
        
        # 如果有已登录标志，视为已登录
        if has_logged_in_marker:
            return True
        
        return False
        
    except Exception as e:
        print(f"[警告] 检查登录状态失败：{e}")
        return False


async def auto_login(page) -> bool:
    """自动登录"""
    try:
        print("[登录] 检测到未登录，开始自动登录...")
        
        # 等待页面加载完成
        await asyncio.sleep(2)
        
        # 尝试多种方式找到输入框
        input_selectors = [
            'input[type="password"]',
            'input[placeholder*="API"]',
            'input[name="password"]',
            'input[name="apiKey"]',
            'input'
        ]
        
        password_input = None
        for selector in input_selectors:
            try:
                password_input = await page.wait_for_selector(selector, state='visible', timeout=5000)
                if password_input:
                    input_type = await password_input.get_attribute('type')
                    placeholder = await password_input.get_attribute('placeholder') or ''
                    if input_type == 'password' or 'API' in placeholder or 'key' in placeholder.lower():
                        break
            except:
                continue
        
        if not password_input:
            print("[错误] 未找到密码输入框")
            return False
        
        # 填写 API Key
        await password_input.fill('')
        await password_input.fill(API_KEY)
        print("[登录] API Key 已填写")
        
        # 点击登录按钮（尝试多种方式）
        login_button = await page.query_selector('button:has-text("登录"), button[type="submit"], .login-btn, [class*="login"]')
        if login_button:
            await login_button.click()
            print("[登录] 已点击登录按钮")
        else:
            # 尝试按回车键
            await password_input.press('Enter')
            print("[登录] 已按回车键登录")
        
        # 等待登录完成
        await asyncio.sleep(5)
        
        # 验证登录是否成功
        is_logged_in = await check_if_logged_in(page)
        if is_logged_in:
            print("[登录] 登录成功")
            return True
        else:
            print("[登录] 登录失败")
            return False
            
    except Exception as e:
        print(f"[错误] 自动登录失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def get_whalecloud_models() -> list:
    """获取 WhaleCloud 模型列表（含价格和上架时间）"""
    models = []
    
    browser = None
    context = None
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    try:
        async with async_playwright() as p:
            # 启动独立的 Chrome 实例（非调试模式连接）
            print("[启动] 正在启动 Chrome 浏览器...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,  # 显示浏览器窗口，方便用户手动登录
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-extensions",
                    "--disable-dev-shm-usage"
                ]
            )
            
            page = context.pages[0] if context.pages else await context.new_page()
            
            # 访问模型列表页面
            url = "https://lab.iwhalecloud.com/gpt-proxy/console/models"
            print(f"[访问] 正在访问 {url}...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
            
            # 检查登录状态
            is_logged_in = await check_if_logged_in(page)
            if not is_logged_in:
                print("[提示] 请在打开的浏览器窗口中手动登录，登录完成后按回车继续...")
                input()  # 等待用户手动登录后按回车
                await page.reload(wait_until="networkidle")
                await asyncio.sleep(3)
            
            print("[提取] 正在提取模型数据...")
            
            # 提取模型数据 - 使用更智能的提取逻辑
            models = await page.evaluate(r"""
                () => {
                    const models = [];
                    const pageText = document.body.innerText;
                    
                    // 方法1: 尝试从表格中提取
                    const tables = document.querySelectorAll('table');
                    tables.forEach(table => {
                        const rows = table.querySelectorAll('tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td, th');
                            if (cells.length >= 3) {
                                const model = {};
                                cells.forEach((cell, idx) => {
                                    const text = cell.innerText.trim();
                                    if (idx === 0) model.name = text;
                                    else if (text.match(/[\w-]+-\d+/)) model.code = text;
                                    else if (text.includes('¥') || text.includes('元')) model.price = text;
                                    else if (text.match(/\d{4}[-/]/)) model.release_time = text;
                                });
                                if (model.name || model.code) {
                                    models.push(model);
                                }
                            }
                        });
                    });
                    
                    // 方法2: 从卡片/列表项中提取
                    if (models.length === 0) {
                        const items = document.querySelectorAll('.model-item, .model-card, [class*="model"], .ant-list-item, .MuiListItem-root');
                        items.forEach(item => {
                            const model = {};
                            const text = item.innerText;
                            
                            // 提取名称（通常是第一个标题）
                            const title = item.querySelector('h1, h2, h3, h4, .title, [class*="title"], [class*="name"]');
                            if (title) model.name = title.innerText.trim();
                            
                            // 提取编码（通常包含数字和连字符）
                            const codeMatch = text.match(/([a-zA-Z0-9]+-[a-zA-Z0-9.-]+)/);
                            if (codeMatch) model.code = codeMatch[1];
                            
                            // 提取价格
                            const priceMatch = text.match(/([¥￥]\s*[\d.]+\s*\/?\s*(?:千|1K|k|K)?\s*(?:tokens?|token)?)/i);
                            if (priceMatch) model.price = priceMatch[1].trim();
                            
                            // 提取上下文长度
                            const contextMatch = text.match(/(\d+)\s*[Kk]\s*(?:上下文|context)/i);
                            if (contextMatch) model.context = contextMatch[1] + 'K';
                            
                            // 提取上架时间
                            const timeMatch = text.match(/(\d{4}[-/]\d{2}[-/]\d{2})/);
                            if (timeMatch) model.release_time = timeMatch[1];
                            
                            // 提取能力标签
                            const tags = [];
                            const tagMatches = text.match(/(Function Calling|深度思考|长上下文|结构化输出|视觉理解|多模态|推理模型|极速推理)/g);
                            if (tagMatches) tags.push(...tagMatches);
                            model.tags = tags;
                            
                            if (model.name || model.code) {
                                models.push(model);
                            }
                        });
                    }
                    
                    // 方法3: 如果以上都失败，返回页面结构供调试
                    if (models.length === 0) {
                        return [{
                            debug: "No models found",
                            page_sample: pageText.substring(0, 3000),
                            html_sample: document.body.innerHTML.substring(0, 2000)
                        }];
                    }
                    
                    return models;
                }
            """)
            
            await page.close()
            print(f"[完成] 成功提取 {len(models)} 个模型信息")
            
    except Exception as e:
        print(f"[错误] 获取模型列表失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        if context:
            try:
                await context.close()
            except:
                pass
    
    return models


async def get_whalecloud_balance() -> Dict:
    """查询 WhaleCloud API 余额"""
    result = {
        "platform": "WhaleCloud Lab (鲸云实验室)",
        "platform_key": "whalecloud",
        "url": "https://lab.iwhalecloud.com/gpt-proxy/console/dashboard",
        "used": "未知",
        "remaining": "未知",
        "requests": "未知",
        "status": "error",
        "error_message": None
    }

    browser = None
    context = None
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    try:
        async with async_playwright() as p:
            # 先尝试连接已运行的 Chrome
            print("[检测] 检查 Chrome 是否已运行...")
            if is_port_open(9222):
                try:
                    print("[连接] 连接到已运行的 Chrome (端口 9222)...")
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=5000)
                    # 连接成功，创建新页面
                    page = await browser.new_page()
                except Exception as e:
                    print(f"[连接失败] {e}，将启动新 Chrome")
                    browser = None
            else:
                print("[未运行] Chrome 未在调试模式运行")
            
            # 如果没有成功连接，启动新的 Chrome
            if not browser:
                print("[启动] 启动 Chrome (调试模式)...")
                # 使用 persistent_context 保持登录状态
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    args=["--remote-debugging-port=9222"]
                )
                page = context.pages[0] if context.pages else await context.new_page()
                print("[启动] Chrome 已启动")
                
                # 导航到 Dashboard
                print("[访问] 正在访问 WhaleCloud Dashboard...")
                await page.goto(result["url"], wait_until="domcontentloaded", timeout=30000)
            else:
                # 访问 Dashboard
                print("[访问] 正在访问 WhaleCloud Dashboard...")
                await page.goto(result["url"], wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面初始加载
            print("[等待] 等待页面加载...")
            await asyncio.sleep(2)
            
            # 检查登录状态
            is_logged_in = await check_if_logged_in(page)
            
            if not is_logged_in:
                # 未登录，尝试自动登录
                login_success = await auto_login(page)
                if not login_success:
                    result["error_message"] = "自动登录失败，请检查 API Key 是否正确"
                    await page.close()
                    return result
                
                # 登录后再等待一下
                await asyncio.sleep(2)
            else:
                print("[状态] 已登录")
            
            # 提取余额数据（尝试 2 次）
            print("[提取] 正在提取余额数据...")
            data = await extract_balance_data(page)
            
            if data:
                print("[成功] 数据提取成功")
                result.update(data)
                result["status"] = "success"
            else:
                # 第 2 次尝试
                print("[重试] 第 1 次失败，等待 2 秒后重试...")
                await asyncio.sleep(2)
                
                data = await extract_balance_data(page)
                
                if data:
                    print("[成功] 第 2 次尝试成功")
                    result.update(data)
                    result["status"] = "success"
                else:
                    print("[失败] 两次尝试都失败")
                    result["error_message"] = "无法提取余额数据"
            
            await page.close()
            
    except Exception as e:
        result["error_message"] = f"查询过程出错：{str(e)}"
        print(f"[错误] 查询错误：{e}")
        
    finally:
        # 关闭浏览器/上下文
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
        print("[提示] Chrome 窗口保持打开，如需关闭请手动操作")
    
    return result


async def extract_balance_data(page) -> Optional[Dict]:
    """从页面提取余额数据"""
    try:
        # 等待包含余额信息的元素出现
        try:
            await page.wait_for_function(
                '() => document.body.innerText.includes("余额") || document.body.innerText.includes("已用")',
                timeout=5000
            )
        except:
            pass  # 超时也继续尝试提取
        
        # 提取数据
        data = await page.evaluate("""
            () => {
                const data = {};
                const pageText = document.body.innerText;
                
                // 提取剩余额度（优先匹配"剩余额度"）
                const remainingPatterns = [
                    /剩余额度[\\s\\n]*¥([\\d.]+)/,
                    /剩余[\\s:：]*[￥¥$]?([\\d.]+)/,
                    /余额[\\s:：]*[￥¥$]?([\\d.]+)/,
                    /balance[\\s:：]*[￥¥$]?([\\d.]+)/i
                ];
                for (const pattern of remainingPatterns) {
                    const match = pageText.match(pattern);
                    if (match) {
                        data.remaining = `￥${match[1]}`;
                        break;
                    }
                }
                
                // 提取已使用费用（优先匹配"已使用费用"）
                const usedPatterns = [
                    /已使用费用[\\s\\n]*¥([\\d.]+)/,
                    /已用[\\s:：]*[￥¥$]?([\\d.]+)/,
                    /消耗[\\s:：]*[￥¥$]?([\\d.]+)/,
                    /used[\\s:：]*[￥¥$]?([\\d.]+)/i
                ];
                for (const pattern of usedPatterns) {
                    const match = pageText.match(pattern);
                    if (match) {
                        data.used = `￥${match[1]}`;
                        break;
                    }
                }
                
                // 提取请求次数
                const requestsPatterns = [
                    /请求次数[\\s\\n]*"?(\\d+)"?/,
                    /请求[\\s:：]*"?(\\d+)"?/,
                    /次数[\\s:：]*(\\d+)/,
                    /requests[\\s:：]*(\\d+)/i
                ];
                for (const pattern of requestsPatterns) {
                    const match = pageText.match(pattern);
                    if (match) {
                        data.requests = match[1];
                        break;
                    }
                }
                
                return data;
            }
        """)
        
        # 验证数据有效性
        if data.get("remaining") or data.get("used"):
            return data
        
        return None
        
    except Exception as e:
        print(f"[警告] 提取数据失败：{e}")
        return None


def format_result(r: Dict) -> str:
    """格式化输出结果"""
    if r["status"] == "success":
        return "\n".join([
            "=" * 60,
            "[成功] 余额查询成功",
            "=" * 60,
            f"   剩余余额：{r['remaining']}",
            f"   已用金额：{r['used']}",
            f"   请求次数：{r['requests']}",
            "=" * 60
        ])
    else:
        return "\n".join([
            "=" * 60,
            "[失败] 余额查询失败",
            "=" * 60,
            f"   原因：{r['error_message']}",
            "",
            "[建议]",
            "   1. 检查 Chrome 是否在调试模式运行（端口 9222）",
            "   2. 检查 API Key 是否正确",
            "   3. 手动访问以下链接验证：",
            f"      {r['url']}",
            "=" * 60
        ])


async def main():
    """主函数"""
    import sys
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "models":
        # 获取模型列表
        print("[开始] 正在获取 WhaleCloud 模型列表...\n")
        models = await get_whalecloud_models()
        print(f"[完成] 获取到 {len(models)} 个模型\n")
        
        # 输出 JSON 格式
        import json
        print(json.dumps(models, ensure_ascii=False, indent=2))
        return {"models": models, "status": "success"}
    else:
        # 查询余额
        print("[开始] 正在查询 WhaleCloud 余额...\n")
        result = await get_whalecloud_balance()
        print("\n" + format_result(result))
        return result


if __name__ == "__main__":
    asyncio.run(main())
