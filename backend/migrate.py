"""
One-time database migration:
Adds payer_name and payment_date columns to the users table.
"""
import pymysql

conn = pymysql.connect(
    host='localhost', port=3306,
    user='root', password='',
    database='sofzenix_hackfest'
)
cur = conn.cursor()

# Add payer_name if missing
cur.execute("SHOW COLUMNS FROM users LIKE 'payer_name'")
if not cur.fetchone():
    cur.execute("ALTER TABLE users ADD COLUMN payer_name VARCHAR(255) NULL")
    print("[+] Added column: payer_name")
else:
    print("[=] Column already exists: payer_name")

# Add payment_date if missing
cur.execute("SHOW COLUMNS FROM users LIKE 'payment_date'")
if not cur.fetchone():
    cur.execute("ALTER TABLE users ADD COLUMN payment_date VARCHAR(20) NULL")
    print("[+] Added column: payment_date")
else:
    print("[=] Column already exists: payment_date")

conn.commit()
conn.close()
print("\n[✓] Migration complete! Restart app.py now.")
