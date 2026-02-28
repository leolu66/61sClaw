"""
API Balance Checker - 查询多个API平台的余额和用量
使用Playwright连接已登录的Chrome浏览器获取数据
"""

import asyncio
import json
from typing import Dict, List, Optional
from playwright.async_api import async_playwright


async def get_whalecloud_balance() -> Dict:
    """查询WhaleCloud API余额"""
    result = {
        "platform": "WhaleCloud API",
        "url": "https://lab.iwhalecloud.com/gpt-proxy/console/dashboard",
        "balance": "未知",
        "today_usage": "未知",
        "month_usage": "未知",
        "status": "error",
        "details": []
    }

    try:
        async with async_playwright() as p:
            # 连接已运行的Chrome
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")

            # 创建新页面
            page = await browser.new_page()

            # 访问页面
            print("正在访问 WhaleCloud Dashboard...")
            await page.goto(result["url"], wait_until="domcontentloaded", timeout=30000)

            # 等待页面加载
            await asyncio.sleep(3)

            # 获取页面标题
            print(f"页面标题: {await page.title()}")

            # 提取数据
            data = await page.evaluate("""
                () => {
                    const data = {};
                    const pageText = document.body.innerText;

                    // 提取余额
                    if (pageText.includes('账户余额')) {
                        const match = pageText.match(/账户余额[\\s:：]*([¥$]?\\d+\\.?\\d*)/);
                        if (match) data.balance = match[1];
                    }

                    // 提取今日消耗
                    if (pageText.includes('今日消耗')) {
                        const match = pageText.match(/今日消耗[\\s:：]*([¥$]?\\d+\\.?\\d*)/);
                        if (match) data.todayUsage = match[1];
                    }

                    // 提取本月消耗
                    if (pageText.includes('本月消耗')) {
                        const match = pageText.match(/本月消耗[\\s:：]*([¥$]?\\d+\\.?\\d*)/);
                        if (match) data.monthUsage = match[1];
                    }

                    return data;
                }
            """)

            print(f"提取的数据: {data}")

            if data.get("balance"):
                result["balance"] = f"¥{data.get('balance', '0')}"
            if data.get("todayUsage"):
                result["today_usage"] = f"¥{data.get('todayUsage', '0')}"
            if data.get("monthUsage"):
                result["month_usage"] = f"¥{data.get('monthUsage', '0')}"

            if data:
                result["status"] = "success"
                result["details"].append("数据获取成功")
            else:
                result["details"].append("未能提取到数据，可能需要登录")

            await browser.close()

    except Exception as e:
        result["details"].append(f"获取失败: {str(e)}")
        print(f"WhaleCloud查询错误: {e}")

    return result


def format_result(r: Dict) -> str:
    """格式化输出"""
    output = ["=" * 50]
    output.append(f"【{r['platform']}】")
    output.append(f"  状态: {r['status']}")
    output.append(f"  账户余额: {r['balance']}")
    output.append(f"  今日消耗: {r['today_usage']}")
    output.append(f"  本月消耗: {r['month_usage']}")
    if r['details']:
        output.append(f"  详情: {', '.join(r['details'])}")
    output.append("=" * 50)
    return "\n".join(output)


async def main():
    """主函数"""
    print("正在查询 WhaleCloud API 余额...")

    result = await get_whalecloud_balance()
    print(format_result(result))


if __name__ == "__main__":
    asyncio.run(main())
