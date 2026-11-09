import sqlite3
import os

db_path = 'cr.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('[OK] Tabelas:', tables)
for t in tables:
    cur.execute('SELECT COUNT(*) FROM ' + t)
    print('  -', t + ':', cur.fetchone()[0], 'registros')
conn.close()
