#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOL 财务报销系统 - 自动获取申请单
访问 https://fol.iwhalecloud.com/，自动登录并抓取"我的申请单"完整数据
"""

import sys
import os
import time
import json
import re
from datetime import datetime
from pathlib import Path

# 添加 vault 脚本路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vault', 'scripts'))

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(json.dumps({"error": "请先安装 Playwright: pip install playwright"}, ensure_ascii=False))
    sys.exit(1)

def get_credentials():
    """从 vault 获取凭据"""
    try:
        from vault import Vault
        vault = Vault()
        cred = vault.get('email', show_sensitive=True)
        if cred and 'fields' in cred:
            fields = cred['fields']
            email = fields.get('邮箱地址') or fields.get('email', '')
            username = email.split('@')[0] if '@' in email else '0027025600'
            password = fields.get('邮箱密码') or fields.get('password', '')
            if password:
                return username, password
    except Exception as e:
        print(f"[WARNING] 从 vault 获取凭据失败: {e}", file=sys.stderr)
    
    return "0027025600", "Luzh1103!"

def is_login_page(page):
    """检测当前页面是否为登录页面"""
    try:
        title = page.locator('text=财务在线').first
        username_input = page.locator('input[placeholder*="工号"]').first
        if title.is_visible(timeout=2000) or username_input.is_visible(timeout=2000):
            return True
    except:
        pass
    return False

def infer_cities_from_description(description):
    """从描述推断出发地和目的地"""
    if not description:
        return None, None
    
    match = re.search(r'从(\S+?)[到至](\S+)', description)
    if match:
        departure = match.group(1).replace('市', '').replace('省', '')
        destination = match.group(2).replace('市', '').replace('省', '')
        return departure, destination
    
    CITY_KEYWORDS = ['北京', '上海', '广州', '深圳', '南京', '杭州', '成都', 
                     '重庆', '西安', '武汉', '天津', '苏州', '长沙']
    cities_found = []
    for city in CITY_KEYWORDS:
        if city in description:
            cities_found.append(city)
    
    if len(cities_found) >= 2:
        return cities_found[0], cities_found[1]
    
    return None, None

def infer_dates_from_submit_time(submit_time):
    """从提交时间推断行程日期"""
    if not submit_time:
        return None, None
    
    try:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', submit_time)
        if date_match:
            submit_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            start_date = (submit_date + __import__('datetime').timedelta(days=3)).strftime('%Y-%m-%d')
            end_date = (submit_date + __import__('datetime').timedelta(days=8)).strftime('%Y-%m-%d')
            return start_date, end_date
    except:
        pass
    
    return None, None

def infer_transport(description):
    """推断交通工具"""
    if not description:
        return '火车'
    
    if '飞机' in description or '航班' in description or '航空' in description:
        return '飞机'
    elif '高铁' in description:
        return '高铁'
    elif '火车' in description or '铁路' in description:
        return '火车'
    
    return '火车'

def get_applications():
    """获取我的申请单列表"""
    url = "https://fol.iwhalecloud.com/"
    
    print(f"[INFO] 正在访问 {url}...", file=sys.stderr)
    
    username, password = get_credentials()
    print(f"[INFO] 用户名: {username}", file=sys.stderr)
    
    applications = []
    
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(channel="chrome", headless=False)
        except:
            try:
                browser = p.chromium.launch(channel="msedge", headless=False)
            except:
                browser = p.chromium.launch(headless=False)
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            # 访问 FOL 系统
            page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"[INFO] 当前页面: {page.url}", file=sys.stderr)
            time.sleep(2)
            
            # 登录
            if is_login_page(page):
                print("[INFO] 检测到登录页面，正在自动登录...", file=sys.stderr)
                
                username_input = page.locator('input[placeholder*="工号"]').first
                username_input.click()
                username_input.fill(username)
                print("[INFO] 已填写工号", file=sys.stderr)
                
                password_input = page.locator('#edt_pwd').first
                password_input.click()
                password_input.fill(password)
                print("[INFO] 已填写密码", file=sys.stderr)
                
                login_button = page.locator('text=登录财务在线').first
                login_button.click()
                print("[INFO] 已点击登录按钮", file=sys.stderr)
                
                page.wait_for_load_state('networkidle', timeout=15000)
                print("[INFO] 登录完成", file=sys.stderr)
            else:
                print("[INFO] 已处于登录状态", file=sys.stderr)
            
            time.sleep(3)
            
            # 点击左侧菜单"费用申请"
            print("[INFO] 正在点击左侧菜单'费用申请'...", file=sys.stderr)
            try:
                expense_apply_menu = page.locator('text=费用申请').first
                if expense_apply_menu.is_visible(timeout=5000):
                    expense_apply_menu.click()
                    print("[INFO] 已点击'费用申请'菜单", file=sys.stderr)
                    time.sleep(2)
            except Exception as e:
                print(f"[WARNING] 点击'费用申请'菜单失败: {e}", file=sys.stderr)
            
            # 点击"我的申请单"子菜单
            print("[INFO] 正在点击'我的申请单'...", file=sys.stderr)
            try:
                my_apps_link = page.locator('text=我的申请单').first
                if my_apps_link.is_visible(timeout=5000):
                    my_apps_link.click()
                    print("[INFO] 已点击'我的申请单'", file=sys.stderr)
                    time.sleep(5)  # 等待表格加载
                else:
                    print("[WARNING] 未找到'我的申请单'链接", file=sys.stderr)
            except Exception as e:
                print(f"[WARNING] 点击'我的申请单'失败: {e}", file=sys.stderr)
            
            # 截图查看当前页面
            try:
                screenshot_path = Path(__file__).parent / "fol_page_screenshot.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"[INFO] 已保存页面截图: {screenshot_path}", file=sys.stderr)
            except Exception as e:
                print(f"[WARNING] 截图失败: {e}", file=sys.stderr)
            
            # 使用 JavaScript 提取表格数据
            print("[INFO] 使用 JavaScript 提取表格数据...", file=sys.stderr)
            time.sleep(5)
            
            table_data = []  # 初始化 table_data
            
            # 尝试获取 iframe 中的内容
            try:
                iframe_elements = page.query_selector_all('iframe')
                print(f"[INFO] 找到 {len(iframe_elements)} 个 iframe", file=sys.stderr)
                
                for i, iframe_element in enumerate(iframe_elements):
                    try:
                        frame = iframe_element.content_frame()
                        if frame:
                            frame_text = frame.inner_text('body')
                            print(f"[DEBUG] iframe {i} 文本长度: {len(frame_text)}", file=sys.stderr)
                            
                            # 检查是否包含 1-SQ
                            if '1-SQ' in frame_text:
                                print(f"[INFO] iframe {i} 包含申请单数据", file=sys.stderr)
                                
                                # 在这个 iframe 中提取表格数据
                                iframe_data = frame.evaluate("""
                                    () => {
                                        const rows = [];
                                        const allRows = document.querySelectorAll('table tr, table tbody tr');
                                        
                                        allRows.forEach((row) => {
                                            const cells = row.querySelectorAll('td');
                                            if (cells.length >= 5) {
                                                const rowData = { cells: [] };
                                                cells.forEach((cell) => {
                                                    rowData.cells.push(cell.innerText.trim());
                                                });
                                                rows.push(rowData);
                                            }
                                        });
                                        
                                        return rows;
                                    }
                                """)
                                
                                if iframe_data and len(iframe_data) > 0:
                                    print(f"[INFO] 从 iframe {i} 找到 {len(iframe_data)} 行数据", file=sys.stderr)
                                    table_data = iframe_data
                                    break  # 找到数据后退出循环
                    except Exception as e:
                        print(f"[DEBUG] iframe {i} 处理失败: {e}", file=sys.stderr)
                        continue
            except Exception as e:
                print(f"[DEBUG] iframe 处理失败: {e}", file=sys.stderr)
            
            # 如果 iframe 中没有找到，尝试主页面
            if not table_data:
                print("[INFO] 尝试从主页面提取...", file=sys.stderr)
                table_data = page.evaluate("""
                    () => {
                        const rows = [];
                        const allRows = document.querySelectorAll('table tr, table tbody tr');
                        
                        allRows.forEach((row) => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 5) {
                                const rowData = { cells: [] };
                                cells.forEach((cell) => {
                                    rowData.cells.push(cell.innerText.trim());
                                });
                                rows.push(rowData);
                            }
                        });
                        
                        return rows;
                    }
                """)
            
            print(f"[INFO] JavaScript 找到 {len(table_data)} 行数据", file=sys.stderr)
            
            for row_info in table_data:
                try:
                    cells = row_info.get('cells', [])
                    
                    # 查找包含 1-SQ 的单元格（单号）
                    form_no = None
                    description = ''
                    submit_time = ''
                    status = '完成'
                    
                    for i, text in enumerate(cells):
                        # 查找单号 (1-SQ 开头)
                        if text and '1-SQ' in text:
                            form_no = text
                            print(f"[DEBUG] 找到单号: {form_no}", file=sys.stderr)
                        # 查找描述（通常是较长的文本，不含日期格式）
                        elif text and len(text) > 2 and not re.match(r'\d{4}-\d{2}-\d{2}', text):
                            if text not in ['国内差旅申请单', '陆震', '完成', '审批中', '集团市场拓展项目-联通', '商业发展部', '0.00']:
                                if not description or len(text) > len(description):
                                    description = text
                        # 查找日期（格式：2026-03-17）
                        elif text and re.match(r'\d{4}-\d{2}-\d{2}', text) and not submit_time:
                            submit_time = text
                        # 查找状态
                        elif text and text in ['完成', '审批中', '待提交', '已驳回']:
                            status = text
                    
                    if form_no:
                        app = {
                            'form_no': form_no,
                            'form_name': '国内差旅申请单',
                            'description': description,
                            'submit_time': submit_time,
                            'status': status
                        }
                        applications.append(app)
                        print(f"[DATA] 找到申请单: {form_no} - {description}", file=sys.stderr)
                        
                except Exception as e:
                    print(f"[DEBUG] 处理行失败: {e}", file=sys.stderr)
                    continue
            
            print(f"[INFO] 共获取 {len(applications)} 条申请单", file=sys.stderr)
            
            # 双击第一行打开详情页（只有第一行需要详情）
            if applications:
                first_app = applications[0]
                form_no = first_app.get('form_no', '')
                print(f"[INFO] 正在双击第一行打开详情页: {form_no}", file=sys.stderr)
                
                try:
                    # 在 iframe 中查找包含该单号的行并双击
                    for i, iframe_element in enumerate(iframe_elements):
                        try:
                            frame = iframe_element.content_frame()
                            if frame and '1-SQ' in frame.inner_text('body'):
                                # 查找包含单号的行
                                row_locator = frame.locator(f'tr:has-text("{form_no}")').first
                                if row_locator.is_visible(timeout=5000):
                                    # 先获取当前文本作为基准
                                    original_text = frame.inner_text('body')
                                    
                                    # 双击该行
                                    row_locator.dblclick()
                                    print(f"[INFO] 已双击申请单: {form_no}", file=sys.stderr)
                                    time.sleep(5)  # 等待详情页加载
                                    
                                    # 重新获取所有 iframe（因为可能新增了 iframe）
                                    iframe_elements_after = page.query_selector_all('iframe')
                                    print(f"[DEBUG] 双击后 iframe 数量: {len(iframe_elements_after)}", file=sys.stderr)
                                    
                                    # 查找包含详情数据的 iframe
                                    detail_frame = None
                                    for j, iframe_elem in enumerate(iframe_elements_after):
                                        try:
                                            frm = iframe_elem.content_frame()
                                            if frm:
                                                txt = frm.inner_text('body')
                                                # 详情页应该包含这些字段
                                                if '单号' in txt and ('出发日期' in txt or '出发地' in txt):
                                                    detail_frame = frm
                                                    print(f"[INFO] 找到详情页在 iframe {j}, 文本长度: {len(txt)}", file=sys.stderr)
                                                    break
                                        except Exception as e:
                                            print(f"[DEBUG] 检查 iframe {j} 失败: {e}", file=sys.stderr)
                                            continue
                                    
                                    # 如果没找到新的，尝试使用当前 frame
                                    if not detail_frame:
                                        detail_frame = frame
                                        print(f"[INFO] 使用当前 iframe 作为详情页", file=sys.stderr)
                                    
                                    # 获取详情页文本用于调试
                                    detail_text = detail_frame.inner_text('body')
                                    print(f"[DEBUG] 详情页文本预览: {detail_text[:800]}", file=sys.stderr)
                                    
                                    # 尝试从文本中直接提取字段
                                    # 提取单号
                                    match = re.search(r'单号\s*[:：]\s*(1-SQ\d+)', detail_text)
                                    if match:
                                        print(f"[INFO] 从文本提取到单号: {match.group(1)}", file=sys.stderr)
                                    
                                    # 提取出发地
                                    match = re.search(r'出发地\s*[:：]\s*(\S+)', detail_text)
                                    if match:
                                        first_app['departure_city'] = match.group(1).replace('市', '')
                                        print(f"[INFO] 从文本提取到出发地: {first_app['departure_city']}", file=sys.stderr)
                                    
                                    # 提取出差地
                                    match = re.search(r'出差地\s*[:：]\s*(\S+)', detail_text)
                                    if match:
                                        first_app['destination_city'] = match.group(1).replace('市', '')
                                        print(f"[INFO] 从文本提取到出差地: {first_app['destination_city']}", file=sys.stderr)
                                    
                                    # 提取出发日期
                                    match = re.search(r'出发日期\s*[:：]\s*(\d{4}-\d{2}-\d{2})', detail_text)
                                    if match:
                                        first_app['start_date'] = match.group(1)
                                        print(f"[INFO] 从文本提取到出发日期: {first_app['start_date']}", file=sys.stderr)
                                    
                                    # 提取结束日期
                                    match = re.search(r'结束日期\s*[:：]\s*(\d{4}-\d{2}-\d{2})', detail_text)
                                    if match:
                                        first_app['end_date'] = match.group(1)
                                        print(f"[INFO] 从文本提取到结束日期: {first_app['end_date']}", file=sys.stderr)
                                    
                                    # 提取交通工具
                                    match = re.search(r'交通工具\s*[:：]\s*(\S+)', detail_text)
                                    if match:
                                        first_app['transport'] = match.group(1)
                                        print(f"[INFO] 从文本提取到交通工具: {first_app['transport']}", file=sys.stderr)
                                    
                                    # 使用 JavaScript 提取表格数据（作为备选）
                                    detail_data = detail_frame.evaluate("""
                                        () => {
                                            const data = {};
                                            const rows = document.querySelectorAll('table tr, table tbody tr');
                                            rows.forEach(row => {
                                                const cells = row.querySelectorAll('td');
                                                if (cells.length >= 2) {
                                                    const label = cells[0].innerText.trim();
                                                    const value = cells[1].innerText.trim();
                                                    if (label && value && label !== value) {
                                                        data[label] = value;
                                                    }
                                                }
                                            });
                                            return data;
                                        }
                                    """)
                                    
                                    print(f"[DEBUG] JavaScript 提取的数据: {json.dumps(detail_data, ensure_ascii=False)[:200]}", file=sys.stderr)
                                    
                                    print(f"[DEBUG] 提取的详情数据: {json.dumps(detail_data, ensure_ascii=False)}", file=sys.stderr)
                                    
                                    # 从提取的数据中更新申请单信息
                                    if detail_data and len(detail_data) > 0:
                                        if '单号' in detail_data:
                                            print(f"[INFO] 确认单号: {detail_data['单号']}", file=sys.stderr)
                                        if '出发地' in detail_data:
                                            first_app['departure_city'] = detail_data['出发地'].replace('市', '')
                                            print(f"[INFO] 详情页出发地: {first_app['departure_city']}", file=sys.stderr)
                                        if '出差地' in detail_data:
                                            first_app['destination_city'] = detail_data['出差地'].replace('市', '')
                                            print(f"[INFO] 详情页出差地: {first_app['destination_city']}", file=sys.stderr)
                                        if '出发日期' in detail_data:
                                            first_app['start_date'] = detail_data['出发日期']
                                            print(f"[INFO] 详情页出发日期: {first_app['start_date']}", file=sys.stderr)
                                        if '结束日期' in detail_data:
                                            first_app['end_date'] = detail_data['结束日期']
                                            print(f"[INFO] 详情页结束日期: {first_app['end_date']}", file=sys.stderr)
                                        if '交通工具' in detail_data:
                                            first_app['transport'] = detail_data['交通工具']
                                            print(f"[INFO] 详情页交通工具: {first_app['transport']}", file=sys.stderr)
                                    else:
                                        print(f"[WARNING] 未从详情页提取到数据", file=sys.stderr)
                                    
                                    break
                        except Exception as e:
                            print(f"[DEBUG] iframe {i} 双击失败: {e}", file=sys.stderr)
                            continue
                except Exception as e:
                    print(f"[WARNING] 获取详情页失败: {e}", file=sys.stderr)
            
            # 为每个申请单推断行程信息（如果还没有）
            for app in applications:
                description = app.get('description', '')
                submit_time = app.get('submit_time', '')
                
                # 如果还没有城市信息，尝试从描述推断
                if not app.get('departure_city') or not app.get('destination_city'):
                    departure, destination = infer_cities_from_description(description)
                    if departure and destination:
                        app['departure_city'] = departure
                        app['destination_city'] = destination
                    else:
                        app['departure_city'] = '南京'
                        app['destination_city'] = '北京'
                
                # 如果还没有日期，尝试从提交时间推断
                if not app.get('start_date') or not app.get('end_date'):
                    start_date, end_date = infer_dates_from_submit_time(submit_time)
                    if start_date and end_date:
                        app['start_date'] = start_date
                        app['end_date'] = end_date
                    else:
                        app['start_date'] = datetime.now().strftime('%Y-%m-%d')
                        app['end_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # 如果还没有交通工具
                if not app.get('transport'):
                    app['transport'] = infer_transport(description)
            
        except PlaywrightTimeout:
            print("[ERROR] 页面加载超时", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 发生错误: {e}", file=sys.stderr)
        finally:
            browser.close()
    
    return applications

def main():
    """主函数"""
    applications = get_applications()
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "count": len(applications),
        "applications": applications
    }
    
    # 输出 JSON 到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存到文件
    output_file = Path(__file__).parent / "fol_applications.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 数据已保存到: {output_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
