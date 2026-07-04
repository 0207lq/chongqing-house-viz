import pandas as pd
import sqlite3

db = "data/house_data_cleaned.db"
conn = sqlite3.connect(db)

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables: {tables}")

for tname in tables:
    cursor.execute(f"PRAGMA table_info({tname})")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"\nTable '{tname}' columns: {cols}")

    df = pd.read_sql_query(f"SELECT * FROM {tname} LIMIT 3", conn)
    print(f"\nSample rows:")
    for c in df.columns:
        print(f"  {c}: {df[c].tolist()}")

    # Check numeric columns stats
    print(f"\nNumeric stats:")
    # Find price/area related columns
    for col in cols:
        if any(kw in col.lower() for kw in ['price', 'price', 'area', 'price', 'total', '总价', '均价', '面积']):
            try:
                vals = pd.read_sql_query(f"SELECT {col} FROM {tname} WHERE {col} IS NOT NULL AND {col} != '' LIMIT 20", conn)
                print(f"  {col} samples: {vals[col].tolist()[:10]}")
            except:
                pass

conn.close()
