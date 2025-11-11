import os
import time
import pymysql

DB_HOST = os.environ.get("DB_HOST", "db1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "1234")
DB_NAME = os.environ.get("DB_NAME", "testdb")

def wait_for_mysql():
    for i in range(30):
        try:
            conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME, connect_timeout=2)
            conn.close()
            print("[OK] MySQL reachable")
            return
        except Exception as e:
            print(f"[WAIT] MySQL not ready yet... ({i+1}/30) {e}")
            time.sleep(2)
    raise RuntimeError("MySQL not reachable within timeout")

def main():
    wait_for_mysql()
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME, autocommit=True)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS demo (id INT PRIMARY KEY AUTO_INCREMENT, msg VARCHAR(100))")
    cur.execute("INSERT INTO demo (msg) VALUES ('hello from python'), ('docker + mysql + volume + network')")
    cur.execute("SELECT id, msg FROM demo ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    print("=== SELECT result ===")
    for r in rows:
        print(r)
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

