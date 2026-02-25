import sqlite3

db_path = r'C:\Users\luzhe\.openclaw\workspace-main\datas\zhipu_balance.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建平台表
cursor.execute('''
CREATE TABLE IF NOT EXISTS platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL UNIQUE
)
''')

# 插入平台
cursor.execute('INSERT OR IGNORE INTO platforms (platform_name) VALUES (?)', ('智谱AI',))
cursor.execute('INSERT OR IGNORE INTO platforms (platform_name) VALUES (?)', ('月之暗面',))
cursor.execute('INSERT OR IGNORE INTO platforms (platform_name) VALUES (?)', ('WhaleCloud',))

conn.commit()

# 查看表结构
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', cursor.fetchall())

conn.close()
print('平台表已创建')
