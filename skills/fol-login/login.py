#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOL 财务报销系统自动登录
访问 https://fol.iwhalecloud.com/ 并自动登录
"""

import sys
import os
import time

# 添加 vault 脚本路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vault', 'scripts'))

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("[ERROR] 请先安装 Playwright: pip install playwright")
    print("[INFO] 然后运行: playwright install chromium")
    sys.exit(1)

def get_credentials():
    """从 vault 获取凭据"""
    try:
        from vault import Vault
        vault = Vault()
        # 使用公司邮箱凭据（工号相同，密码不同）
        cred = vault.get('email', show_sensitive=True)
        if cred and 'fields' in cred:
            fields = cred['fields']
            # 从邮箱地址提取工号
            email = fields.get('email', '')
            username = email.split('@')[0] if '@' in email else '0027025600'
            password = fields.get('password', '')
            return username, password
    except Exception as e:
        print(f"[WARNING] 从 vault 获取凭据失败: {e}")
    
    # 默认凭据（fallback）
    return "0027025600", "Luzh1103!"

def is_login_page(page):
    """检测当前页面是否为登录页面"""
    try:
        # FOL 登录页面特征：包含"财务在线"标题和工号输入框
        title = page.locator('text=财务在线').first
        username_input = page.locator('textbox[placeholder*="工号"], input[placeholder*="工号"]').first
        
        if title.is_visible(timeout=2000) or username_input.is_visible(timeout=2000):
            return True
    except:
        pass
    
    # 检查 URL
    url = page.url
    if 'fol.iwhalecloud.com' in url and 'login' not in url.lower():
        # 如果在 FOL 域名但不在登录页，可能是已登录
        return False
    
    return False

def login_fol():
    """主登录流程"""
    url = "https://fol.iwhalecloud.com/"
    
    print(f"[INFO] 正在访问 {url}...")
    
    # 获取凭据
    username, password = get_credentials()
    print(f"[INFO] 用户名: {username}")
    
    with sync_playwright() as p:
        # 启动浏览器（尝试使用已安装的 Chrome/Edge）
        browser = None
        try:
            # 尝试连接已安装的 Chrome
            browser = p.chromium.launch(channel="chrome", headless=False)
        except:
            try:
                # 尝试连接已安装的 Edge
                browser = p.chromium.launch(channel="msedge", headless=False)
            except:
                # 使用默认 chromium
                browser = p.chromium.launch(headless=False)
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        try:
            # 访问 FOL 系统
            page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"[INFO] 当前页面: {page.url}")
            
            # 等待页面加载
            time.sleep(2)
            
            # 检测是否为登录页面
            if is_login_page(page):
                print("[INFO] 检测到登录页面，正在自动登录...")
                
                # 填写工号（使用 placeholder 定位）
                username_input = page.locator('input[placeholder*="工号"]').first
                username_input.click()
                username_input.fill(username)
                print("[INFO] 已填写工号")
                
                # 填写密码（使用 id 定位）
                password_input = page.locator('#edt_pwd').first
                password_input.click()
                password_input.fill(password)
                print("[INFO] 已填写密码")
                
                # 点击登录按钮
                login_button = page.locator('text=登录财务在线').first
                login_button.click()
                print("[INFO] 已点击登录按钮")
                
                # 等待登录完成（等待页面跳转）
                page.wait_for_load_state('networkidle', timeout=10000)
                print("[INFO] 页面加载完成")
                
                # 检查是否登录成功
                if 'login' not in page.url.lower() and 'ssodr' not in page.url.lower():
                    print(f"[SUCCESS] 登录成功！当前页面: {page.url}")
                else:
                    print(f"[INFO] 当前页面: {page.url}")
            else:
                print(f"[INFO] 已处于登录状态，当前页面: {page.url}")
            
            print("[INFO] 浏览器保持打开状态，请手动关闭")
            
            # 保持浏览器打开
            while True:
                time.sleep(1)
                
        except PlaywrightTimeout:
            print("[ERROR] 页面加载超时")
        except Exception as e:
            print(f"[ERROR] 发生错误: {e}")
        finally:
            # 不自动关闭，让用户手动关闭
            pass

if __name__ == "__main__":
    login_fol()
