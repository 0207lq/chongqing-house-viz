import pandas as pd
import sqlite3

db = "data/house_data_cleaned.db"
conn = sqlite3.connect(db)

df = pd.read_sql_query("SELECT * FROM houses_cleaned", conn)
conn.close()

print(f"Total rows: {len(df)}")
print(f"\n--- 均价_数值 stats ---")
print(df["均价_数值"].describe())
print(f"\n--- 总价_数值 stats ---")
print(df["总价_数值"].describe())
print(f"\n--- 面积_数值 stats ---")
print(df["面积_数值"].describe())

print(f"\n--- 所属城区 value counts ---")
print(df["所属城区"].value_counts().head(20))

print(f"\n--- Top 10 最高均价 ---")
top = df.nlargest(10, "均价_数值")
for _, r in top.iterrows():
    print(f"  {r['所属城区']} | {r['所属小区'][:20]} | {r['均价_数值']}元/㎡")

print(f"\n--- District average prices ---")
avg = df.groupby("所属城区")["均价_数值"].agg(["mean", "count", "min", "max"]).sort_values("mean", ascending=False)
print(avg.to_string())
