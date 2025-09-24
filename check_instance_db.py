import sqlite3
import os

# Check instance/data.db
db_path = os.path.join('instance', 'data.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables in instance/data.db:', tables)

    if ('customer',) in tables:
        cursor.execute("PRAGMA table_info(customer)")
        columns = cursor.fetchall()
        print('Customer table columns:')
        for col in columns:
            print(f"  {col[1]} - {col[2]}")

    conn.close()
else:
    print("instance/data.db not found")