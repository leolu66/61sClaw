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
        content = await page.content()
        text = await page.evaluate('() => document.body.innerText')
        
        # 已登录标志：页面包含"余额"或"已用"
        if '余额' in text or '已用' in text or '请求' in text:
            # 但不包含"请输入 API Key"
            if '请输入 API Key' not in text:
                return True
        
        # 未登录标志：包含登录相关文字
        if 'API Key' in text and ('请输入' in text or '登录' in text):
            return False
        
        return False
        
    except Exception as e:
        print(f"[警告] 检查登录状态失败：{e}")
        return False


async def auto_login(page) -> bool:
    """自动登录"""
    try:
        print("[登录] 检测到未登录，开始自动登录...")
        
        # 等待密码输入框出现
        await page.wait_for_selector('input[type="password"]', state='visible', timeout=5000)
        await asyncio.sleep(0.5)
        
        # 填写 API Key
        await page.fill('input[type="password"]', '')
        await page.fill('input[type="password"]', API_KEY)
        print("[登录] API Key 已填写")
        
        # 点击登录按钮
        login_button = await page.query_selector('button:has-text("登录")')
        if login_button:
            await login_button.click()
            print("[登录] 已点击登录按钮")
        else:
            print("[警告] 未找到登录按钮")
            return False
        
        # 等待登录完成（等待页面跳转或内容变化）
        await asyncio.sleep(3)
        
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
        return False


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
    print("[开始] 正在查询 WhaleCloud 余额...\n")
    result = await get_whalecloud_balance()
    print("\n" + format_result(result))
    return result


if __name__ == "__main__":
    asyncio.run(main())
