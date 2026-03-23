"""
Diagnostic: Shows ALL columns in the users table.
Run this to confirm what MySQL actually sees.
"""
import pymysql

conn = pymysql.connect(
    host='localhost', port=3306,
    user='root', password='',
    database='sofzenix_hackfest'
)
cur = conn.cursor()
cur.execute("SHOW COLUMNS FROM users")
cols = cur.fetchall()
print(f"\n[✓] Found {len(cols)} columns in 'users' table:\n")
for c in cols:
    print(f"  - {c[0]:30s}  type={c[1]}")

conn.close()
print("\n[Done]")
