import sqlite3

conn = sqlite3.connect(r'C:\Users\luzhe\.api_balance_history.db')
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('表:', tables)

# 查看表结构
print('\n--- balance_history 表结构 ---')
cursor.execute('PRAGMA table_info(balance_history)')
for row in cursor.fetchall():
    print(row)

# 查看各平台的最近记录
print('\n--- 各平台最近1条记录 ---')
for platform in ['whalecloud', 'moonshot', 'zhipu']:
    cursor.execute("SELECT * FROM balance_history WHERE platform=? ORDER BY query_time DESC LIMIT 1", (platform,))
    row = cursor.fetchone()
    print(f'\n{platform}:')
    print(row)

conn.close()
