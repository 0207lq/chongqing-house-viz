"""
analysis.py - 数据分析算法模块

包含统计分析、多特征预测、聚类、相关系数分析等
"""

import pandas as pd
import numpy as np
import re
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


# ==================== 数据解析函数 ====================

def parse_price(price_str):
    """解析价格字符串为数值"""
    if not price_str or price_str == 'N/A' or pd.isna(price_str):
        return None
    cleaned = str(price_str).replace(',', '').replace(' ', '')
    if '元/㎡' in cleaned:
        cleaned = cleaned.replace('元/㎡', '')
        try: return float(cleaned)
        except: return None
    if '万' in cleaned:
        cleaned = cleaned.replace('万', '')
        try: return float(cleaned)
        except: return None
    try: return float(cleaned)
    except: return None


def parse_area(area_str):
    """解析面积字符串"""
    if not area_str or area_str == 'N/A' or pd.isna(area_str):
        return None
    match = re.search(r'(\d+\.?\d*)', str(area_str))
    if match:
        try: return float(match.group(1))
        except: return None
    return None


def parse_build_year(year_text):
    """解析建造年份"""
    if not year_text or year_text == 'N/A' or pd.isna(year_text):
        return None
    match = re.search(r'(\d{4})', str(year_text))
    if match:
        try: return int(match.group(1))
        except: return None
    return None


def parse_decoration(title):
    """从标题提取装修情况"""
    if not title or pd.isna(title):
        return "未知"
    title = str(title)
    if '豪装' in title: return '豪装'
    if '精装' in title: return '精装'
    if '简装' in title: return '简装'
    if '毛坯' in title: return '毛坯'
    return '未知'


def parse_floor_level(floor_str):
    """提取楼层类别（低层/中层/高层）"""
    if not floor_str or floor_str == 'N/A' or pd.isna(floor_str):
        return "未知"
    if '低层' in str(floor_str): return '低层'
    if '中层' in str(floor_str): return '中层'
    if '高层' in str(floor_str): return '高层'
    return "未知"


def parse_huxing_category(huxing):
    """将户型简化为类别：1室/2室/3室/4室+"""
    if not huxing or pd.isna(huxing):
        return "未知"
    match = re.search(r'(\d+)\s*室', str(huxing))
    if match:
        rooms = int(match.group(1))
        if rooms >= 4: return '4室+'
        return f'{rooms}室'
    return "未知"


def parse_huxing_rooms(huxing):
    """提取室数（纯数字）"""
    if not huxing or pd.isna(huxing):
        return None
    match = re.search(r'(\d+)\s*室', str(huxing))
    if match:
        try: return int(match.group(1))
        except: return None
    return None


def prepare_dataframe(df):
    """统一的数据预处理：解析所有数值字段，添加分类特征"""
    df = df.copy()

    # 解析数值
    if '均价_数值' not in df.columns:
        df['均价_数值'] = df['均价'].apply(parse_price)
    if '总价_数值' not in df.columns:
        df['总价_数值'] = df['总价'].apply(parse_price)
    if '面积_数值' not in df.columns:
        df['面积_数值'] = df['面积'].apply(parse_area)

    # 建造年份 -> 房龄
    if '房龄_计算' not in df.columns and '建造年份' in df.columns:
        df['建造年份_数值'] = df['建造年份'].apply(parse_build_year)
        df['房龄_计算'] = 2026 - df['建造年份_数值']
    elif '建造年份' in df.columns:
        df['建造年份_数值'] = df['建造年份'].apply(parse_build_year)

    # 分类特征
    if '装修情况' not in df.columns and '标题' in df.columns:
        df['装修情况'] = df['标题'].apply(parse_decoration)
    if '楼层类别' not in df.columns and '楼层' in df.columns:
        df['楼层类别'] = df['楼层'].apply(parse_floor_level)
    if '户型分类' not in df.columns and '户型' in df.columns:
        df['户型分类'] = df['户型'].apply(parse_huxing_category)
    if '户型室数' not in df.columns and '户型' in df.columns:
        df['户型室数'] = df['户型'].apply(parse_huxing_rooms)

    return df


# ==================== KPI 统计 ====================

def summarize_data(df, price_col="均价_数值", area_col="面积_数值", total_col="总价_数值"):
    """数据概览"""
    if df.empty:
        return {"total": 0, "avg_price": 0, "avg_area": 0, "avg_total": 0,
                "max_price": 0, "min_price": 0, "max_total": 0, "min_total": 0, "districts_count": 0}

    data = df[price_col].dropna()
    data_total = df[total_col].dropna()
    return {
        "total": len(df),
        "avg_price": round(data.mean(), 0),
        "median_price": round(data.median(), 0),
        "avg_area": round(df[area_col].dropna().mean(), 1),
        "avg_total": round(data_total.mean(), 1),
        "max_price": round(data.max(), 0),
        "min_price": round(data.min(), 0),
        "max_total": round(data_total.max(), 1),
        "min_total": round(data_total.min(), 1),
        "districts_count": df["所属城区"].nunique(),
        "price_std": round(data.std(), 0),
    }


def calc_district_stats(df, price_col="均价_数值", area_col="面积_数值"):
    """各区域统计"""
    if df.empty:
        return pd.DataFrame()
    stats = df.groupby("所属城区").agg(
        房源数量=("标题", "count"),
        均价均值=("均价_数值", "mean"),
        均价中位数=("均价_数值", "median"),
        均价最高=("均价_数值", "max"),
        均价最低=("均价_数值", "min"),
        均价标准差=("均价_数值", "std"),
        平均面积=("面积_数值", "mean"),
        总价均值=("总价_数值", "mean"),
    ).reset_index()
    int_cols = ["均价均值", "均价中位数", "均价最高", "均价最低", "均价标准差"]
    for col in int_cols:
        stats[col] = stats[col].fillna(0).round(0).astype(int)
    stats["平均面积"] = stats["平均面积"].fillna(0).round(1)
    stats["总价均值"] = stats["总价均值"].fillna(0).round(1)
    stats = stats.sort_values("均价均值", ascending=False)
    stats = stats.rename(columns={"所属城区": "区域"})
    return stats


# ==================== 相关性分析 ====================

def calc_correlation(df, col1, col2, label1="变量1", label2="变量2"):
    """计算两个数值列的皮尔逊相关系数"""
    if df.empty:
        return {"correlation": 0, "strength": "无数据", "description": "数据集为空"}
    data = df[[col1, col2]].dropna()
    if len(data) < 3:
        return {"correlation": 0, "strength": "数据不足", "description": f"有效数据少于3条"}
    corr = data[col1].corr(data[col2])
    corr = round(corr, 4)
    abs_corr = abs(corr)
    if abs_corr < 0.1:
        strength = "极弱相关"
    elif abs_corr < 0.3:
        strength = "弱相关"
    elif abs_corr < 0.5:
        strength = "中等相关"
    elif abs_corr < 0.7:
        strength = "强相关"
    else:
        strength = "极强相关"
    direction = "正相关" if corr > 0 else "负相关"
    desc = f"{label1}与{label2}之间存在{strength}（{direction}，r={corr:.4f}）"
    return {"correlation": corr, "strength": strength, "description": desc, "sample_size": len(data)}


def calc_price_area_correlation(df):
    return calc_correlation(df, "均价_数值", "面积_数值", "均价", "面积")


# ==================== 排行榜 ====================

def get_community_rankings(df, top_n=10):
    """
    小区排行榜

    Returns:
        dict: {"most_expensive": DataFrame, "cheapest": DataFrame}
    """
    if df.empty:
        return {"most_expensive": pd.DataFrame(), "cheapest": pd.DataFrame()}

    community_stats = df.groupby("所属小区").agg(
        区域=("所属城区", "first"),
        均价=("均价_数值", "mean"),
        房源数量=("标题", "count"),
    ).reset_index()

    community_stats = community_stats.dropna(subset=["均价"])
    community_stats["均价"] = community_stats["均价"].round(0).astype(int)

    # 过滤掉房源数太少的（至少3条）
    community_stats = community_stats[community_stats["房源数量"] >= 3]

    most_expensive = community_stats.sort_values("均价", ascending=False).head(top_n)
    cheapest = community_stats.sort_values("均价", ascending=True).head(top_n)

    most_expensive = most_expensive.rename(columns={
        "所属小区": "小区名称", "区域": "区域", "均价": "均价(元/㎡)", "房源数量": "房源数"
    })
    cheapest = cheapest.rename(columns={
        "所属小区": "小区名称", "区域": "区域", "均价": "均价(元/㎡)", "房源数量": "房源数"
    })

    return {"most_expensive": most_expensive, "cheapest": cheapest}


# ==================== 多特征房价预测 ====================

def train_multifeature_model(df):
    """
    多特征线性回归房价预测模型

    特征: 面积, 户型室数, 房龄, 楼层类别, 装修情况, 区域

    Returns:
        dict: 模型信息
    """
    if df.empty:
        return {"error": "数据集为空"}

    # 准备数据
    model_df = prepare_dataframe(df)

    # 选取有效特征
    feature_cols = []

    # 面积
    if "面积_数值" in model_df.columns:
        model_df["特征_面积"] = model_df["面积_数值"]
        feature_cols.append("特征_面积")

    # 室数
    if "户型室数" in model_df.columns:
        model_df["特征_室数"] = model_df["户型室数"].fillna(3)
        feature_cols.append("特征_室数")

    # 房龄
    if "房龄_计算" in model_df.columns:
        model_df["特征_房龄"] = model_df["房龄_计算"].fillna(5)
        feature_cols.append("特征_房龄")

    # 楼层类别 one-hot
    if "楼层类别" in model_df.columns:
        floor_dummies = pd.get_dummies(model_df["楼层类别"], prefix="楼层")
        for col in floor_dummies.columns:
            model_df[col] = floor_dummies[col].astype(int)
            if col != "楼层_未知":
                feature_cols.append(col)

    # 区域 one-hot (取Top 20区域)
    if "所属城区" in model_df.columns:
        top_districts = model_df["所属城区"].value_counts().head(20).index
        model_df["区域_编码"] = model_df["所属城区"].apply(lambda x: x if x in top_districts else "其他")
        district_dummies = pd.get_dummies(model_df["区域_编码"], prefix="区")
        for col in district_dummies.columns:
            model_df[col] = district_dummies[col].astype(int)
            if col != "区_其他":
                feature_cols.append(col)

    # 装修情况 one-hot
    if "装修情况" in model_df.columns:
        dec_dummies = pd.get_dummies(model_df["装修情况"], prefix="装修")
        for col in dec_dummies.columns:
            model_df[col] = dec_dummies[col].astype(int)
            if col not in ["装修_未知"]:
                feature_cols.append(col)

    # 目标变量：总价
    target = "总价_数值"
    if target not in model_df.columns:
        return {"error": "缺少总价字段"}

    model_df = model_df.dropna(subset=feature_cols + [target])
    if len(model_df) < 100:
        return {"error": f"有效数据不足（{len(model_df)}条），至少需要100条"}

    X = model_df[feature_cols].values
    y = model_df[target].values

    # 划分
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 训练
    model = LinearRegression()
    model.fit(X_train, y_train)

    # 评估
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

    return {
        "model": model,
        "feature_cols": feature_cols,
        "train_r2": round(train_r2, 4),
        "test_r2": round(test_r2, 4),
        "train_rmse": round(train_rmse, 1),
        "test_rmse": round(test_rmse, 1),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "feature_importance": dict(zip(feature_cols, model.coef_)),
    }


def predict_multifeature(model_info, features_dict):
    """
    使用多特征模型预测房价

    Args:
        model_info: train_multifeature_model 返回的字典
        features_dict: 特征值字典 {特征名: 值}

    Returns:
        float: 预测总价（万元）
    """
    if "error" in model_info or model_info.get("model") is None:
        return None
    model = model_info["model"]
    feature_cols = model_info["feature_cols"]

    # 构建特征向量
    X_vec = []
    for col in feature_cols:
        val = features_dict.get(col, 0)
        if val is None:
            val = 0
        X_vec.append(val)

    if len(X_vec) != len(feature_cols):
        return None

    pred = model.predict([X_vec])[0]
    return round(pred, 1)


# ==================== KMeans 聚类 ====================

def run_kmeans_clustering(df, n_clusters=3):
    """
    KMeans 聚类将房源分类

    Args:
        df: 数据框
        n_clusters: 分类数（默认3类）

    Returns:
        pd.DataFrame: 带"分类"列的 DataFrame
    """
    if df.empty:
        return df

    model_df = prepare_dataframe(df)

    # 特征：面积、总价、均价、房龄、室数
    cluster_features = []
    if "面积_数值" in model_df.columns:
        model_df["聚类_面积"] = model_df["面积_数值"]
        cluster_features.append("聚类_面积")
    if "总价_数值" in model_df.columns:
        model_df["聚类_总价"] = model_df["总价_数值"]
        cluster_features.append("聚类_总价")
    if "均价_数值" in model_df.columns:
        model_df["聚类_均价"] = model_df["均价_数值"]
        cluster_features.append("聚类_均价")
    if "房龄_计算" in model_df.columns:
        model_df["聚类_房龄"] = model_df["房龄_计算"].fillna(5)
        cluster_features.append("聚类_房龄")
    if "户型室数" in model_df.columns:
        model_df["聚类_室数"] = model_df["户型室数"].fillna(3)
        cluster_features.append("聚类_室数")

    model_df = model_df.dropna(subset=cluster_features)
    if len(model_df) < 50:
        model_df["分类"] = "未知"
        return model_df

    # 标准化
    X = model_df[cluster_features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # 分析每个聚类的特征来确定标签
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_info = []
    for i in range(n_clusters):
        center = cluster_centers[i]
        avg_total = center[cluster_features.index("聚类_总价")] if "聚类_总价" in cluster_features else 0
        avg_area = center[cluster_features.index("聚类_面积")] if "聚类_面积" in cluster_features else 0
        avg_age = center[cluster_features.index("聚类_房龄")] if "聚类_房龄" in cluster_features else 0
        cluster_info.append({"id": i, "avg_total": avg_total, "avg_area": avg_area, "avg_age": avg_age})

    # 根据总价和面积排序判断类型
    # 按总价排序，最高的是豪宅，最低的是老破小/刚需
    cluster_info.sort(key=lambda x: x["avg_total"])
    label_map = {}
    for idx, info in enumerate(cluster_info):
        if idx == 0:
            if info["avg_age"] > 10:
                label_map[info["id"]] = "老破小"
            else:
                label_map[info["id"]] = "经济型"
        elif idx == n_clusters - 1:
            label_map[info["id"]] = "豪宅"
        else:
            label_map[info["id"]] = "改善型"

    # 如果只有3类，更明确的命名
    if n_clusters == 3:
        cluster_info.sort(key=lambda x: x["avg_total"])
        label_map[cluster_info[0]["id"]] = "经济型"
        label_map[cluster_info[1]["id"]] = "改善型"
        label_map[cluster_info[2]["id"]] = "豪宅"

    model_df["分类"] = [label_map.get(l, f"类{l}") for l in labels]
    return model_df


# ==================== 房龄趋势分析 ====================

def get_age_price_trend(df):
    """
    房龄与均价趋势分析

    Returns:
        pd.DataFrame: 按房龄分组的价格统计
    """
    if df.empty:
        return pd.DataFrame()
    data = prepare_dataframe(df)
    data = data.dropna(subset=["房龄_计算", "均价_数值"])
    if data.empty:
        return pd.DataFrame()
    trend = data.groupby("房龄_计算").agg(
        房源数=("标题", "count"),
        均价=("均价_数值", "mean"),
        中位数=("均价_数值", "median"),
    ).reset_index()
    trend["均价"] = trend["均价"].round(0).astype(int)
    trend["中位数"] = trend["中位数"].round(0).astype(int)
    return trend.sort_values("房龄_计算")


def get_huxing_distribution(df):
    """户型分布统计"""
    if df.empty:
        return pd.DataFrame()
    data = prepare_dataframe(df)
    dist = data["户型分类"].value_counts().reset_index()
    dist.columns = ["户型", "数量"]
    dist["占比"] = (dist["数量"] / dist["数量"].sum() * 100).round(1)
    return dist


def get_decoration_distribution(df):
    """装修情况分布统计"""
    if df.empty:
        return pd.DataFrame()
    data = prepare_dataframe(df)
    dist = data["装修情况"].value_counts().reset_index()
    dist.columns = ["装修情况", "数量"]
    dist["占比"] = (dist["数量"] / dist["数量"].sum() * 100).round(1)
    return dist


def get_price_summary_by_deco(df):
    """各装修类型的价格统计"""
    if df.empty:
        return pd.DataFrame()
    data = prepare_dataframe(df)
    stats = data.groupby("装修情况").agg(
        房源数=("标题", "count"),
        均价=("均价_数值", "mean"),
        总价均值=("总价_数值", "mean"),
    ).reset_index()
    stats["均价"] = stats["均价"].fillna(0).round(0).astype(int)
    stats["总价均值"] = stats["总价均值"].fillna(0).round(1)
    return stats.sort_values("均价", ascending=False)
