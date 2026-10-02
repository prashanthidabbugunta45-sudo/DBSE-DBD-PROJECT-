from database import get_connection
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT * FROM notifications WHERE patient_id='P202600011'")
for row in cur.fetchall():
    print(row)
conn.close()
