"""
database.py - 真实数据库连接模块

用于从 A 同学的 SQLite 数据库中读取房源数据
"""

import sqlite3
import pandas as pd
import os
import re
from config import REAL_DB_PATH, CLEAN_DB_PATH, LOCAL_DB_PATH


def load_data_from_db(db_path=None, use_cleaned=True):
    """
    从 SQLite 数据库加载清洗后的房源数据

    Args:
        db_path: 数据库路径，None 则使用默认路径
        use_cleaned: 是否使用清洗后的数据库（含数值字段）

    Returns:
        pd.DataFrame: 房源数据，包含解析后的数值字段
    """
    if db_path is None:
        # 优先使用清洗后的数据库
        if use_cleaned and os.path.exists(CLEAN_DB_PATH):
            db_path = CLEAN_DB_PATH
            table = "houses_cleaned"
        elif os.path.exists(LOCAL_DB_PATH):
            db_path = LOCAL_DB_PATH
            table = "houses_cleaned"
        elif os.path.exists(REAL_DB_PATH):
            db_path = REAL_DB_PATH
            table = "houses"
        else:
            raise FileNotFoundError(f"数据库文件不存在")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    # 确定表名
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    if "houses_cleaned" in tables:
        table = "houses_cleaned"
    elif "houses" in tables:
        table = "houses"
    else:
        conn.close()
        raise ValueError(f"数据库中找不到 houses 或 houses_cleaned 表，现有表: {tables}")

    # 读取数据
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()

    if df.empty:
        return df

    # 如果读取的是原始数据库，需要解析数值字段
    if table == "houses":
        df = _parse_raw_data(df)

    return df


def _parse_raw_data(df):
    """
    解析原始数据的字符串字段为数值

    原始数据中：均价="12173元/㎡"，总价="120 万"，面积="98.58㎡"
    """
    df = df.copy()

    # 解析均价
    if "均价" in df.columns and "均价_数值" not in df.columns:
        df["均价_数值"] = df["均价"].apply(_parse_price)

    # 解析总价
    if "总价" in df.columns and "总价_数值" not in df.columns:
        df["总价_数值"] = df["总价"].apply(_parse_price)

    # 解析面积
    if "面积" in df.columns and "面积_数值" not in df.columns:
        df["面积_数值"] = df["面积"].apply(_parse_area)

    # 计算房龄
    if "建造年份" in df.columns and "房龄_计算" not in df.columns:
        df["房龄_计算"] = df["建造年份"].apply(_calc_age)

    return df


def _parse_price(price_str):
    """
    解析价格字符串为数值

    例："12173元/㎡" -> 12173.0
        "120 万" -> 120.0
    """
    if not price_str or price_str == "N/A" or pd.isna(price_str):
        return None

    cleaned = str(price_str).replace(",", "").replace(" ", "")

    if "元/㎡" in cleaned:
        cleaned = cleaned.replace("元/㎡", "")
        try:
            return float(cleaned)
        except:
            return None

    if "万" in cleaned:
        cleaned = cleaned.replace("万", "")
        try:
            return float(cleaned)
        except:
            return None

    try:
        return float(cleaned)
    except:
        return None


def _parse_area(area_str):
    """解析面积字符串，如 '98.58㎡' -> 98.58"""
    if not area_str or area_str == "N/A" or pd.isna(area_str):
        return None

    match = re.search(r"(\d+\.?\d*)", str(area_str))
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


def _calc_age(year_text):
    """计算房龄"""
    if not year_text or year_text == "N/A" or pd.isna(year_text):
        return None

    match = re.search(r"(\d{4})", str(year_text))
    if match:
        try:
            return 2026 - int(match.group(1))
        except:
            return None
    return None


def get_db_info():
    """
    获取数据库信息

    Returns:
        dict: 数据库路径、大小、数据量等
    """
    info = {}

    for label, path in [("原始数据库", REAL_DB_PATH), ("清洗后数据库", CLEAN_DB_PATH)]:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                table_info = {}
                for t in tables:
                    tname = t[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {tname}")
                    count = cursor.fetchone()[0]
                    cursor.execute(f"PRAGMA table_info({tname})")
                    cols = len(cursor.fetchall())
                    table_info[tname] = {"rows": count, "columns": cols}
                conn.close()
                info[label] = {
                    "path": path,
                    "size_mb": round(size_mb, 2),
                    "tables": table_info,
                }
            except Exception as e:
                info[label] = {"path": path, "error": str(e)}
        else:
            info[label] = {"path": path, "exists": False}

    return info


if __name__ == "__main__":
    # 测试数据库连接
    try:
        df = load_data_from_db()
        print(f"成功读取 {len(df)} 条数据")
        print(f"字段: {df.columns.tolist()}")
        print(df[["所属城区", "均价_数值", "面积_数值"]].head())
    except Exception as e:
        print(f"读取失败: {e}")

    print("\n数据库信息:")
    info = get_db_info()
    for k, v in info.items():
        print(f"{k}: {v}")
