# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime
import sys
import io

# 设置UTF-8输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def calculate_time_diff(prev_time_str, curr_time_str):
    """计算两个时间字符串之间的差值"""
    try:
        prev_dt = datetime.strptime(prev_time_str, '%Y-%m-%d %H:%M:%S')
        curr_dt = datetime.strptime(curr_time_str, '%Y-%m-%d %H:%M:%S')
        diff = curr_dt - prev_dt
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        if diff.days > 0:
            hours = diff.days * 24 + hours
        return f'{hours}小时{minutes}分钟'
    except:
        return '-'

def get_today_last_record(cursor, platform_name, package_name):
    """获取当天指定平台和资源包的最后一条记录"""
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
    SELECT balance, record_time 
    FROM resource_packages 
    WHERE platform_name = ? 
      AND package_name = ?
      AND date(record_time) = date(?)
    ORDER BY record_time DESC
    LIMIT 1
    ''', (platform_name, package_name, today))
    result = cursor.fetchone()
    if result:
        return {'balance': result[0], 'time': result[1]}
    return None

def get_last_record(cursor, platform_name, package_name):
    """获取指定平台和资源包的最后一条记录（不限日期）"""
    cursor.execute('''
    SELECT balance, record_time 
    FROM resource_packages 
    WHERE platform_name = ? 
      AND package_name = ?
    ORDER BY record_time DESC
    LIMIT 1
    ''', (platform_name, package_name))
    result = cursor.fetchone()
    if result:
        return {'balance': result[0], 'time': result[1]}
    return None

def check_balance():
    db_path = r'C:\Users\luzhe\.openclaw\workspace-main\datas\zhipu_balance.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 当前数据 - 使用最新的浩鲸Lab数据
    current_data = {
        '浩鲸Lab': {
            'used': '18.32',
            'remaining': '81.68',
            'requests': '422'
        },
        '月之暗面': {
            'balance': '25.29633',
            'total_consumption': '139.70367',
            'total_recharge': '50.00000',
            'gift_amount': '164.00000'
        },
        '智谱AI': [
            ('800万GLM-4.1V-FlashX', '8,000,000', 'tokens'),
            ('1000万GLM-4.5-AIR', '10,000,000', 'tokens'),
            ('1000万GLM-4.7', '8,802,880', 'tokens'),
            ('20次图片/视频生成', '20', '次'),
            ('100次搜索', '99', '次'),
            ('600万GLM-4.6V', '6,000,000', 'tokens'),
            ('1200万GLM-4.5-Air', '12,000,000', 'tokens'),
        ]
    }
    
    # ========== 输出 ==========
    print(f'📅 当前查询时间: {current_time}')
    print()
    
    # 浩鲸Lab - 只跟当天最后一条记录对比
    print('### 【浩鲸Lab】')
    today_record = get_today_last_record(cursor, '浩鲸Lab', '已使用费用')
    last_record = get_last_record(cursor, '浩鲸Lab', '已使用费用')
    
    used_val = float(current_data["浩鲸Lab"]["used"])
    requests_val = int(current_data["浩鲸Lab"]["requests"])
    
    if today_record:
        used_diff = used_val - float(today_record['balance'])
        prev_requests_record = get_today_last_record(cursor, '浩鲸Lab', '请求次数')
        requests_diff = 0
        if prev_requests_record:
            requests_diff = requests_val - int(prev_requests_record['balance'])
        
        prev_time = today_record['time']
        time_diff = calculate_time_diff(prev_time, current_time)
        
        print(f'  📊 已使用 ¥{used_val}')
        if used_diff != 0:
            print(f'     较今天上次 (+¥{used_diff:.2f})')
        print(f'  💰 剩余 ¥{current_data["浩鲸Lab"]["remaining"]}')
        print(f'  🔄 请求 {requests_val}次')
        if requests_diff != 0:
            print(f'     较今天上次 (+{requests_diff})')
        print(f'  ⏰ 今天上次记录: {prev_time} ({time_diff}前)')
    elif last_record:
        prev_time = last_record['time']
        time_diff = calculate_time_diff(prev_time, current_time)
        print(f'  📊 已使用 ¥{used_val}')
        print(f'  💰 剩余 ¥{current_data["浩鲸Lab"]["remaining"]}')
        print(f'  🔄 请求 {requests_val}次')
        print(f'  ⏰ 历史记录: {prev_time} ({time_diff}前)')
        print(f'  ℹ️  今天首次记录（浩鲸Lab每日重置）')
    else:
        print(f'  📊 已使用 ¥{used_val}')
        print(f'  💰 剩余 ¥{current_data["浩鲸Lab"]["remaining"]}')
        print(f'  🔄 请求 {requests_val}次')
        print(f'  ℹ️  首次记录')
    print()
    print('---')
    print()
    
    # 月之暗面
    print('### 【月之暗面】')
    today_balance = get_today_last_record(cursor, '月之暗面', '余额')
    last_balance = get_last_record(cursor, '月之暗面', '余额')
    
    balance_val = float(current_data["月之暗面"]["balance"])
    consumption_val = float(current_data["月之暗面"]["total_consumption"])
    
    if today_balance:
        balance_diff = balance_val - float(today_balance['balance'])
        print(f'  余额 {balance_val}￥  *({balance_diff:+.4f}￥)*')
        print(f'  总消费 {consumption_val}￥')
        print(f'  累计充值 {current_data["月之暗面"]["total_recharge"]}￥')
        print(f'  赠送 {current_data["月之暗面"]["gift_amount"]}￥')
    elif last_balance:
        print(f'  余额 {balance_val}￥')
        print(f'  总消费 {consumption_val}￥')
        print(f'  累计充值 {current_data["月之暗面"]["total_recharge"]}￥')
        print(f'  赠送 {current_data["月之暗面"]["gift_amount"]}￥')
        print(f'  ⏰ 上次记录: {last_balance["time"]}')
    else:
        print(f'  余额 {balance_val}￥')
        print(f'  总消费 {consumption_val}￥')
        print(f'  累计充值 {current_data["月之暗面"]["total_recharge"]}￥')
        print(f'  赠送 {current_data["月之暗面"]["gift_amount"]}￥')
    print()
    print('---')
    print()
    
    # 智谱AI 表格
    print('### 【智谱AI】')
    print('资源包 | 当前 | 上次 | 使用')
    print('-|------|------|----')
    for pkg in current_data['智谱AI']:
        today_pkg = get_today_last_record(cursor, '智谱AI', pkg[0])
        last_pkg = get_last_record(cursor, '智谱AI', pkg[0])
        
        prev_balance = '-'
        if today_pkg:
            prev_balance = today_pkg['balance']
        elif last_pkg:
            prev_balance = last_pkg['balance']
        
        # 计算使用量
        usage_str = '-'
        if prev_balance != '-' and prev_balance != pkg[1]:
            try:
                curr_num = int(pkg[1].replace(',', ''))
                prev_num = int(prev_balance.replace(',', ''))
                usage = prev_num - curr_num
                if usage > 0:
                    usage_str = f'-{usage:,}'
            except:
                pass
        
        print(f'{pkg[0]} | {pkg[1]} {pkg[2]} | {prev_balance} | {usage_str}')
    
    # ========== 写入数据库 ==========
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('浩鲸Lab', '已使用费用', current_data['浩鲸Lab']['used'], '元', ''))
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('浩鲸Lab', '剩余额度', current_data['浩鲸Lab']['remaining'], '元', ''))
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('浩鲸Lab', '请求次数', current_data['浩鲸Lab']['requests'], '次', ''))
    
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('月之暗面', '余额', current_data['月之暗面']['balance'], '元', ''))
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('月之暗面', '总消费', current_data['月之暗面']['total_consumption'], '元', ''))
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('月之暗面', '累计充值', current_data['月之暗面']['total_recharge'], '元', ''))
    cursor.execute('''
    INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
    VALUES (?, ?, ?, ?, ?)
    ''', ('月之暗面', '赠送金额', current_data['月之暗面']['gift_amount'], '元', ''))
    
    for pkg in current_data['智谱AI']:
        cursor.execute('''
        INSERT INTO resource_packages (platform_name, package_name, balance, unit, status) 
        VALUES (?, ?, ?, ?, ?)
        ''', ('智谱AI', pkg[0], pkg[1], pkg[2], '生效中'))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    check_balance()
