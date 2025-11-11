import os, time
import pandas as pd
import seaborn as sns
from sqlalchemy import create_engine, text

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "1234")
DB_NAME = os.getenv("DB_NAME", "tipsdb")
URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def wait_db():
    for i in range(60):
        try:
            eng = create_engine(URL)
            with eng.connect() as c:
                c.execute(text("SELECT 1"))
            print("[loader] DB OK")
            return
        except Exception as e:
            print(f"[loader] wait DB... {i+1}/60 {e}")
            time.sleep(2)
    raise RuntimeError("DB not reachable")

def main():
    wait_db()
    eng = create_engine(URL)
    with eng.begin() as conn:
        cnt = conn.execute(text("SELECT COUNT(*) FROM tips")).scalar()
        if cnt and cnt > 0:
            print(f"[loader] already loaded: {cnt} rows")
            return

        print("[loader] loading seaborn.tips...")
        df = sns.load_dataset("tips")  # total_bill, tip, sex, smoker, day, time, size
        df["total_bill"] = df["total_bill"].astype(float)
        df["tip"]        = df["tip"].astype(float)
        df["size"]       = df["size"].astype(int)
        df["source"]     = "initial"
        df.to_sql("tips", con=eng, if_exists="append", index=False)

        # 감사 로그 입력
        inserted = conn.execute(text("SELECT id FROM tips WHERE source='initial'")).fetchall()
        if inserted:
            conn.execute(
                text("INSERT INTO tips_audit (tips_id, source) VALUES " +
                     ",".join([f"({row[0]}, 'initial')" for row in inserted]))
            )
        print(f"[loader] loaded {len(df)} rows")

if __name__ == "__main__":
    main()
