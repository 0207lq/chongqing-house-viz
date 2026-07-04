import pandas as pd
import sqlite3

db = "data/house_data_cleaned.db"
conn = sqlite3.connect(db)
df = pd.read_sql_query("SELECT * FROM houses_cleaned", conn)
conn.close()

# 1. 看看异常数据：1514元/㎡ 和 64365元/㎡ 各有多少
for extreme in [1514, 64365]:
    subset = df[df["均价_数值"] == extreme]
    print(f"\n=== 均价={extreme}元/㎡ 共 {len(subset)} 条 ===")
    print(subset[["所属城区", "所属小区", "面积", "总价", "均价"]].head(10).to_string())

# 2. 用中位数代替均值，看看效果
print("\n\n=== 各区均价中位数 vs 均值对比 ===")
stats = df.groupby("所属城区")["均价_数值"].agg(["mean", "median", "count"])
stats["diff"] = stats["mean"] - stats["median"]
stats = stats.sort_values("median", ascending=False)
print(stats.to_string())

# 3. 看看江北的明细
print("\n\n=== 江北区数据样本 ===")
jiangbei = df[df["所属城区"] == "江北"].head(10)
print(jiangbei[["所属小区", "面积", "总价", "均价"]].to_string())

# 4. 检查"香港置地壹号半岛" - 它在很多区出现
print("\n\n=== 香港置地壹号半岛 分布 ===")
hkg = df[df["所属小区"].str.contains("壹号半岛", na=False)]
print(hkg.groupby("所属城区")["均价_数值"].agg(["count", "mean", "min", "max"]).to_string())

# 5. 看看各个价格区间的房源数量
print("\n\n=== 价格区间分布 ===")
bins = [0, 5000, 8000, 10000, 12000, 14000, 16000, 20000, 30000, 999999]
labels = ["<5000", "5000-8000", "8000-10000", "10000-12000", "12000-14000", "14000-16000", "16000-20000", "20000-30000", ">30000"]
df["价格区间"] = pd.cut(df["均价_数值"], bins=bins, labels=labels)
print(df["价格区间"].value_counts().sort_index())

# 6. 按中位数排名（排除数量太少的区县）
print("\n\n=== 各区中位数排名（房源数>=100） ===")
stats2 = df.groupby("所属城区")["均价_数值"].agg(["median", "mean", "count"])
stats2 = stats2[stats2["count"] >= 100].sort_values("median", ascending=False)
print(stats2.to_string())
