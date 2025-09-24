import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables in database:', tables)

# Check customer table structure if it exists
if ('customer',) in tables:
    cursor.execute("PRAGMA table_info(customer)")
    columns = cursor.fetchall()
    print('Customer table columns:')
    for col in columns:
        print(f"  {col[1]} - {col[2]}")

conn.close()