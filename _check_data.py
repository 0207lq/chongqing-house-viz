"""检查数据结构"""
import sqlite3
db = r'D:\my-project\Anjuke-WebCrawler-Visualization-BigDataAnalysis-main\case\project\data\Database\house_data.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# 标题样例
print("=== 标题样例 ===")
c.execute('SELECT 标题 FROM houses LIMIT 15')
for r in c.fetchall():
    print(f'  {r[0]}')

# 装修信息统计
print("\n=== 装修信息 ===")
keywords = {'精装': 0, '毛坯': 0, '简装': 0, '豪装': 0}
for kw in keywords:
    c.execute(f"SELECT COUNT(*) FROM houses WHERE 标题 LIKE '%{kw}%'")
    keywords[kw] = c.fetchone()[0]
for k, v in keywords.items():
    print(f'  {k}: {v}')
c.execute("SELECT COUNT(*) FROM houses WHERE 标题 NOT LIKE '%精装%' AND 标题 NOT LIKE '%毛坯%' AND 标题 NOT LIKE '%简装%' AND 标题 NOT LIKE '%豪装%'")
print(f'  无标注: {c.fetchone()[0]}')

# 楼层样例
print("\n=== 楼层样例 ===")
c.execute('SELECT DISTINCT 楼层 FROM houses LIMIT 20')
for r in c.fetchall():
    print(f'  {r[0]}')

# 户型样例
print("\n=== 户型样例 ===")
c.execute('SELECT DISTINCT 户型 FROM houses LIMIT 20')
for r in c.fetchall():
    print(f'  {r[0]}')

# 小区数量
c.execute('SELECT COUNT(DISTINCT 所属小区) FROM houses')
print(f"\n=== 小区总数: {c.fetchone()[0]} ===")

# 区县总数
c.execute('SELECT COUNT(DISTINCT 所属城区) FROM houses')
print(f"=== 区县总数: {c.fetchone()[0]} ===")

conn.close()
