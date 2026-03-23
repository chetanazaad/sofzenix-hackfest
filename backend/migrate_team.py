"""
Migration: Create team_members table if it doesn't exist.
"""
import pymysql

conn = pymysql.connect(
    host='localhost', port=3306,
    user='root', password='',
    database='sofzenix_hackfest'
)
cur = conn.cursor()

cur.execute("SHOW TABLES LIKE 'team_members'")
if not cur.fetchone():
    cur.execute("""
        CREATE TABLE team_members (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            leader_id  INT NOT NULL,
            name       VARCHAR(255) NOT NULL,
            email      VARCHAR(255) NOT NULL,
            phone      VARCHAR(15)  NOT NULL,
            added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (leader_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("[+] Created table: team_members")
else:
    print("[=] Table already exists: team_members")

conn.commit()
conn.close()
print("\n[✓] Migration complete!")
