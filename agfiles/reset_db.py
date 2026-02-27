import sqlite3
import os
from datetime import datetime

# 删除旧数据库
db_path = r'C:\Users\luzhe\.openclaw\workspace-main\datas\zhipu_balance.db'
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建新的余额记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS resource_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL,
    package_name TEXT,
    balance TEXT NOT NULL,
    unit TEXT NOT NULL,
    status TEXT,
    record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print('数据库已重建')
