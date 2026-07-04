"""
app.py - 重庆二手房数据可视化平台（Streamlit + Pyecharts）
数据源: SQLite 真实数据库（2026年7月更新 - 167,297条）
"""

import streamlit as st
import pandas as pd
import numpy as np
import time, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="重庆二手房数据可视化平台",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================== CSS ====================

def render_css():
    st.markdown("""
    <style>
        .stApp { padding-left: 20px !important; }
        .main .block-container { padding-left: 3rem !important; padding-right: 2rem !important; max-width: 1400px; }
        section[data-testid="stSidebar"] .sidebar-content { padding: 1.5rem 1rem; }
        div[data-testid="column"] { padding: 0 0.5rem !important; }
        [data-testid="stMetric"] { background: #f8f9fa; padding: 1rem 1.2rem; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: box-shadow 0.2s; }
        [data-testid="stMetric"]:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        [data-testid="stMetric"] label { font-size: 0.9rem !important; font-weight: 500 !important; }
        [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; }
        .element-container:has(iframe) { margin-bottom: 1.5rem; }
        h2, h3 { margin-top: 1.5rem !important; margin-bottom: 0.8rem !important; }
        hr { margin: 1.5rem 0 !important; }
        [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
        .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
        .stTabs [data-baseweb="tab"] { padding: 0.5rem 1.2rem; border-radius: 6px 6px 0 0; }
    </style>
    """, unsafe_allow_html=True)


# ==================== 导入 ====================

from config import CHONGQING_DISTRICTS, MAIN_DISTRICTS
from analysis import (
    summarize_data, calc_district_stats, calc_price_area_correlation,
    get_community_rankings, train_multifeature_model, predict_multifeature,
    run_kmeans_clustering, get_age_price_trend, get_huxing_distribution,
    get_decoration_distribution, get_price_summary_by_deco,
    prepare_dataframe, calc_correlation, parse_decoration
)


# ==================== 数据加载 ====================

@st.cache_data(ttl=600)
def load_data():
    from database import load_data_from_db
    from config import CLEAN_DB_PATH
    # 用文件修改时间作缓存键，切换数据源后自动刷新
    _ = os.path.getmtime(CLEAN_DB_PATH) if os.path.exists(CLEAN_DB_PATH) else 0
    df = load_data_from_db()
    if df.empty:
        st.error("数据库为空，请检查数据文件")
    return df


# ==================== 侧边栏筛选 ====================

def render_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/real-estate.png", width=80)
        st.title("🏠 重庆房源分析")
        st.markdown("---")
        st.markdown("### ⚙️ 数据源")
        st.success("✅ 2026年7月新数据已连接")
        st.caption("📦 167,297 条 | 37 个区县 | 5年以上数据")

        st.markdown("---")
        st.markdown("### 🔍 筛选条件")

        # 区域
        selected_districts = st.multiselect(
            "选择区域", options=MAIN_DISTRICTS, default=[],
            placeholder="全部区域（默认全选）")

        # 价格
        price_range = st.slider("总价区间（万元）", 0, 1000, (0, 1000), step=10)

        # 面积
        area_range = st.slider("面积区间（㎡）", 0, 500, (0, 500), step=10)

        # 户型
        hx_options = ["全部", "1室", "2室", "3室", "4室+"]
        selected_hx = st.selectbox("户型选择", options=hx_options, index=0)

        # 装修情况
        deco_options = ["全部", "精装", "毛坯", "简装", "豪装", "未知"]
        selected_deco = st.selectbox("装修情况", options=deco_options, index=0)

        st.markdown("---")
        if st.button("🔄 重置所有筛选", use_container_width=True):
            st.rerun()
        st.caption("📌 v2.0 | 链家/贝壳重庆站")

        return {
            "districts": selected_districts, "price_range": price_range,
            "area_range": area_range, "huxing": selected_hx, "decoration": selected_deco,
        }


# ==================== 筛选逻辑 ====================

def apply_filters(df, filters):
    filtered = df.copy()
    if "均价_数值" not in filtered.columns:
        from analysis import prepare_dataframe
        filtered = prepare_dataframe(filtered)

    if filters["districts"]:
        filtered = filtered[filtered["所属城区"].isin(filters["districts"])]
    pmin, pmax = filters["price_range"]
    if "总价_数值" in filtered.columns:
        if pmin > 0:
            filtered = filtered[filtered["总价_数值"] >= pmin]
        if pmax < 1000:
            filtered = filtered[filtered["总价_数值"] <= pmax]
    amin, amax = filters["area_range"]
    if "面积_数值" in filtered.columns:
        if amin > 0:
            filtered = filtered[filtered["面积_数值"] >= amin]
        if amax < 500:
            filtered = filtered[filtered["面积_数值"] <= amax]
    if filters["huxing"] != "全部":
        hx = filters["huxing"]
        if hx == "4室+":
            filtered = filtered[filtered["户型"].str.match(r'[4-9]\s*室', na=False)]
        else:
            filtered = filtered[filtered["户型"].str.match(fr'^{hx[0]}\s*室', na=False)]
    if filters["decoration"] != "全部":
        filtered["_deco"] = filtered["标题"].apply(parse_decoration)
        filtered = filtered[filtered["_deco"] == filters["decoration"]]
    return filtered


# ==================== KPI 卡片 ====================

def render_kpi_cards(summary):
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("🏘️ 总房源", f"{summary['total']:,}")
    with col2:
        st.metric("💰 均价", f"{summary['median_price']:,.0f}", "元/㎡（中位数）")
    with col3:
        st.metric("📏 平均面积", f"{summary['avg_area']:.1f}", "㎡")
    with col4:
        st.metric("💵 平均总价", f"{summary['avg_total']:.1f}", "万元")
    with col5:
        st.metric("🔺 最高单价", f"{summary['max_price']:,.0f}", "元/㎡")
    with col6:
        st.metric("🔻 最低单价", f"{summary['min_price']:,.0f}", "元/㎡")
    with col7:
        st.metric("📍 覆盖区域", f"{summary['districts_count']}", "个区县")


# ==================== Tab0: 数据总览 ====================

def _safe_chart(chart_func, df, fallback_msg="图表加载失败"):
    """安全渲染图表，出错时显示提示信息而非崩溃"""
    try:
        chart = chart_func(df)
        return chart.render_embed()
    except Exception as e:
        st.warning(f"⚠️ {fallback_msg}：{str(e)[:80]}")
        return None


def render_overview_tab(df):
    st.markdown("## 📊 数据概览")
    summary = summarize_data(df)
    render_kpi_cards(summary)

    # 图表行
    st.markdown("---")
    col1, col2 = st.columns([6, 5])
    with col1:
        with st.spinner("加载重庆房价热力图..."):
            from charts import create_chongqing_heatmap
            html = _safe_chart(create_chongqing_heatmap, df, "热力图")
            if html:
                st.components.v1.html(html, height=640, scrolling=False)
    with col2:
        with st.spinner("加载价格分布..."):
            from charts import create_price_distribution_chart
            html = _safe_chart(create_price_distribution_chart, df, "价格分布图")
            if html:
                st.components.v1.html(html, height=480, scrolling=False)

    col3, col4 = st.columns([5, 6])
    with col3:
        with st.spinner("加载区域均价..."):
            from charts import create_district_avg_price_chart
            html = _safe_chart(create_district_avg_price_chart, df, "区域均价图")
            if html:
                st.components.v1.html(html, height=480, scrolling=False)
    with col4:
        with st.spinner("加载价格热力图..."):
            from charts import create_price_heatmap
            html = _safe_chart(create_price_heatmap, df, "价格热力图")
            if html:
                st.components.v1.html(html, height=520, scrolling=False)

    # ====== 数据分析报告 ======
    st.markdown("---")
    st.markdown("## 📋 数据分析报告")

    # 区域统计表
    st.markdown("### 各区均价统计")
    with st.spinner("计算区域统计..."):
        district_stats = calc_district_stats(df)
    if not district_stats.empty:
        col_config = {"区域": st.column_config.TextColumn("区域"),
                      "房源数量": st.column_config.NumberColumn("房源数", format="%d")}
        skip = {"区域", "房源数量", "平均面积(㎡)"}
        for col in district_stats.columns:
            if col not in skip:
                col_config[col] = st.column_config.NumberColumn(col, format="%.0f")
        st.dataframe(district_stats, use_container_width=True, hide_index=True, column_config=col_config)

    # 相关系数矩阵
    st.markdown("### 相关系数分析")
    col_c1, col_c2, col_c3 = st.columns(3)
    df_prepared = prepare_dataframe(df)

    with col_c1:
        r1 = calc_correlation(df_prepared, "面积_数值", "总价_数值", "面积", "总价")
        st.metric("面积 vs 总价", f"r = {r1['correlation']:.4f}", r1["strength"])
        st.caption(r1["description"][:80])

    with col_c2:
        r2 = calc_correlation(df_prepared, "房龄_计算", "均价_数值", "房龄", "均价")
        st.metric("房龄 vs 均价", f"r = {r2['correlation']:.4f}", r2["strength"])
        st.caption(r2["description"][:80])

    with col_c3:
        if "户型室数" in df_prepared.columns:
            r3 = calc_correlation(df_prepared, "户型室数", "均价_数值", "户型室数", "均价")
        else:
            df_prepared["户型室数"] = df_prepared["户型"].apply(
                lambda x: int(str(x)[0]) if str(x)[0].isdigit() else None)
            r3 = calc_correlation(df_prepared.dropna(subset=["户型室数"]), "户型室数", "均价_数值", "户型室数", "均价")
        st.metric("户型室数 vs 均价", f"r = {r3['correlation']:.4f}", r3["strength"])
        st.caption(r3["description"][:80])

    # 装修情况分布
    st.markdown("### 装修情况分布")
    col_deco1, col_deco2 = st.columns([1, 1])
    with col_deco1:
        deco_stats = get_price_summary_by_deco(df)
        if not deco_stats.empty:
            st.dataframe(deco_stats, use_container_width=True, hide_index=True,
                         column_config={"装修情况": "装修类型", "房源数": st.column_config.NumberColumn("房源数", format="%d"),
                                        "均价": st.column_config.NumberColumn("均价(元/㎡)", format="%.0f"),
                                        "总价均值": st.column_config.NumberColumn("总价均值(万元)", format="%.1f")})

    # 项目简介
    with st.expander("ℹ️ 关于本项目", expanded=False):
        st.markdown("""
        **重庆二手房数据可视化平台**
        - 数据来源：链家/贝壳重庆站二手房数据
        - 技术栈：Python + Streamlit + Pyecharts + scikit-learn
        - 数据量：167,297 条房源（5年），覆盖 37 个区县
        - 功能：数据概览、排行榜、图表分析、房价预测、房源分类
        """)


# ==================== Tab1: 排行榜 ====================

def render_ranking_tab(df):
    st.markdown("## 🏆 小区排行榜")
    st.markdown("---")

    with st.spinner("计算排行榜..."):
        rankings = get_community_rankings(df)

    col_most, col_cheap = st.columns(2)

    with col_most:
        st.markdown("### 💰 最贵小区 Top 10")
        if not rankings["most_expensive"].empty:
            most = rankings["most_expensive"].reset_index(drop=True)
            most.index = most.index + 1
            st.dataframe(most, use_container_width=True,
                         column_config={"小区名称": st.column_config.TextColumn("小区名称", width="large"),
                                        "区域": st.column_config.TextColumn("区域"),
                                        "均价(元/㎡)": st.column_config.NumberColumn("均价(元/㎡)", format="%d"),
                                        "房源数": st.column_config.NumberColumn("房源数", format="%d")})

    with col_cheap:
        st.markdown("### 💸 最便宜小区 Top 10")
        if not rankings["cheapest"].empty:
            cheap = rankings["cheapest"].reset_index(drop=True)
            cheap.index = cheap.index + 1
            st.dataframe(cheap, use_container_width=True,
                         column_config={"小区名称": st.column_config.TextColumn("小区名称", width="large"),
                                        "区域": st.column_config.TextColumn("区域"),
                                        "均价(元/㎡)": st.column_config.NumberColumn("均价(元/㎡)", format="%d"),
                                        "房源数": st.column_config.NumberColumn("房源数", format="%d")})

    # 区域均价统计
    st.markdown("---")
    st.markdown("### 📊 各区均价详情")
    stats = calc_district_stats(df)
    if not stats.empty:
        stats_display = stats.copy()
        stats_display = stats_display.rename(columns={"区域": "区域", "房源数量": "房源数"})
        st.dataframe(stats_display, use_container_width=True, hide_index=True,
                     column_config={
                         "区域": "区域", "房源数": st.column_config.NumberColumn("房源数", format="%d"),
                         "均价均值": st.column_config.NumberColumn("均价均值", format="%.0f"),
                         "均价中位数": st.column_config.NumberColumn("中位数", format="%.0f"),
                         "均价最高": st.column_config.NumberColumn("最高价", format="%.0f"),
                         "均价最低": st.column_config.NumberColumn("最低价", format="%.0f"),
                         "平均面积": st.column_config.NumberColumn("平均面积(㎡)", format="%.1f"),
                         "总价均值": st.column_config.NumberColumn("总价均值(万元)", format="%.1f"),
                     })


# ==================== Tab2: 图表分析 ====================

def render_charts_tab(df):
    st.markdown("## 📈 深度图表分析")
    st.markdown("---")

    tab_a, tab_b, tab_c, tab_d = st.tabs(["面积-总价趋势", "房龄趋势分析", "户型分布", "装修情况"])

    with tab_a:
        with st.spinner("加载图表..."):
            from charts import create_area_total_trend_scatter
            st.components.v1.html(create_area_total_trend_scatter(df).render_embed(), height=500, scrolling=False)

        # 显示趋势公式
        from sklearn.linear_model import LinearRegression
        trend_data = df.dropna(subset=["面积_数值", "总价_数值"])
        if len(trend_data) > 0:
            X = trend_data["面积_数值"].values.reshape(-1, 1)
            y = trend_data["总价_数值"].values
            model = LinearRegression().fit(X, y)
            st.info(f"📐 **趋势公式**: 总价(万元) = {model.coef_[0]:.2f} × 面积(㎡) + {model.intercept_:.2f}")

    with tab_b:
        st.markdown("### 房龄-均价趋势")
        with st.spinner("加载图表..."):
            from charts import create_age_trend_chart
            st.components.v1.html(create_age_trend_chart(df).render_embed(), height=450, scrolling=False)

        trend_df = get_age_price_trend(df)
        if not trend_df.empty:
            st.caption(f"数据范围：房龄 {int(trend_df['房龄_计算'].min())} - {int(trend_df['房龄_计算'].max())} 年")
            young = trend_df[trend_df["房龄_计算"] <= 3]["均价"].mean()
            old = trend_df[trend_df["房龄_计算"] >= 15]["均价"].mean()
            if not pd.isna(young) and not pd.isna(old):
                diff = ((old - young) / young * 100)
                if diff < 0:
                    st.warning(f"⚠️ 房龄15年以上房源均价较3年内新房下降 {abs(diff):.1f}%")
                else:
                    st.success(f"✅ 房龄15年以上房源均价较3年内新房上涨 {diff:.1f}%")

    with tab_c:
        col_pie, col_table = st.columns([6, 4])
        with col_pie:
            with st.spinner("加载图表..."):
                from charts import create_huxing_pie_chart
                st.components.v1.html(create_huxing_pie_chart(df).render_embed(), height=450, scrolling=False)
        with col_table:
            dist = get_huxing_distribution(df)
            if not dist.empty:
                st.dataframe(dist, use_container_width=True, hide_index=True,
                             column_config={"户型": "户型类型", "数量": st.column_config.NumberColumn("数量", format="%d"),
                                            "占比": st.column_config.NumberColumn("占比(%)", format="%.1f%%")})

    with tab_d:
        col_bar, col_deco_table = st.columns([6, 4])
        with col_bar:
            with st.spinner("加载图表..."):
                from charts import create_decoration_bar_chart
                st.components.v1.html(create_decoration_bar_chart(df).render_embed(), height=450, scrolling=False)
        with col_deco_table:
            deco_stats = get_price_summary_by_deco(df)
            if not deco_stats.empty:
                st.dataframe(deco_stats, use_container_width=True, hide_index=True,
                             column_config={"装修情况": "装修类型", "房源数": st.column_config.NumberColumn("房源数", format="%d"),
                                            "均价": st.column_config.NumberColumn("均价(元/㎡)", format="%.0f"),
                                            "总价均值": st.column_config.NumberColumn("总价均值(万元)", format="%.1f")})


# ==================== Tab3: 房价预测 ====================

def render_prediction_tab(df):
    st.markdown("## 🔮 房价预测")
    st.markdown("---")

    # 训练模型
    with st.spinner("🏋️ 正在训练多特征预测模型（使用全部数据）..."):
        model_info = train_multifeature_model(df)

    if "error" in model_info:
        st.error(f"模型训练失败: {model_info['error']}")
        return

    # 模型指标
    st.success("✅ 模型训练完成")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("训练集 R²", f"{model_info['train_r2']:.4f}")
    with col_m2:
        st.metric("测试集 R²", f"{model_info['test_r2']:.4f}")
    with col_m3:
        st.metric("训练集 RMSE", f"{model_info['train_rmse']:.1f} 万")
    with col_m4:
        st.metric("测试集 RMSE", f"{model_info['test_rmse']:.1f} 万")

    st.markdown("---")
    st.markdown("### 🎯 输入房源信息进行预测")

    df_prepared = prepare_dataframe(df)

    pred_col1, pred_col2, pred_col3 = st.columns(3)

    with pred_col1:
        area = st.slider("面积 (㎡)", 20, 500, 100, 5)
        rooms = st.selectbox("户型（室数）", options=[1, 2, 3, 4, 5, 6], index=2)

    with pred_col2:
        age = st.slider("房龄（年）", 0, 40, 5, 1)
        floor_level = st.selectbox("楼层类别", options=["低层", "中层", "高层", "未知"], index=1)

    with pred_col3:
        decoration = st.selectbox("装修情况", options=["精装", "毛坯", "简装", "豪装", "未知"], index=0)
        district = st.selectbox("区域", options=MAIN_DISTRICTS, index=0)

    # 构建特征
    feature_cols = model_info["feature_cols"]
    features_dict = {}
    for col in feature_cols:
        if col == "特征_面积":
            features_dict[col] = area
        elif col == "特征_室数":
            features_dict[col] = rooms
        elif col == "特征_房龄":
            features_dict[col] = age
        elif col == f"楼层_{floor_level}":
            features_dict[col] = 1
        elif col.startswith("楼层_"):
            features_dict[col] = 0
        elif col == f"装修_{decoration}":
            features_dict[col] = 1
        elif col.startswith("装修_"):
            features_dict[col] = 0
        elif col == f"区_{district}":
            features_dict[col] = 1
        elif col.startswith("区_"):
            features_dict[col] = 0
        else:
            features_dict[col] = 0

    if st.button("🔮 预测房价", type="primary", use_container_width=True):
        with st.spinner("计算中..."):
            pred_total = predict_multifeature(model_info, features_dict)
            pred_unit_price = round(pred_total * 10000 / area, 0) if pred_total and area > 0 else 0

        if pred_total:
            st.balloons()

            result_col1, result_col2, result_col3 = st.columns(3)
            with result_col1:
                st.metric("💵 预测总价", f"{pred_total:.1f} 万元", delta=None)
            with result_col2:
                st.metric("📏 预测单价", f"{pred_unit_price:,.0f} 元/㎡")
            with result_col3:
                st.metric("📐 输入面积", f"{area} ㎡")

            # 置信区间（用RMSE估算）
            ci_low = pred_total - 1.96 * model_info["test_rmse"]
            ci_high = pred_total + 1.96 * model_info["test_rmse"]
            st.info(f"📊 **95% 置信区间**: {ci_low:.1f} - {ci_high:.1f} 万元"
                    f"（基于测试集 RMSE={model_info['test_rmse']:.1f}万）")

            # 输入参数汇总
            st.markdown("**输入参数:**")
            st.caption(f"面积={area}㎡ | 户型={rooms}室 | 房龄={age}年 | "
                      f"楼层={floor_level} | 装修={decoration} | 区域={district}")

            # 特征重要性
            st.markdown("---")
            st.markdown("### 📊 特征重要性（线性回归系数）")
            importance = model_info["feature_importance"]
            imp_df = pd.DataFrame([{"特征": k, "系数": round(v, 2)} for k, v in importance.items()])
            imp_df["影响"] = imp_df["系数"].apply(lambda x: "📈 正向" if x > 0 else "📉 负向")
            imp_df["|系数|"] = imp_df["系数"].abs()
            imp_df = imp_df.sort_values("|系数|", ascending=False)
            st.dataframe(imp_df[["特征", "系数", "影响"]], use_container_width=True, hide_index=True)
        else:
            st.error("预测失败，请检查输入参数")


# ==================== Tab4: 数据明细 ====================

def render_data_tab(df):
    st.markdown("## 📋 房源数据明细")

    # 聚类分析
    st.markdown("### 🏷️ KMeans 房源分类")
    with st.spinner("正在进行聚类分析（将房源分为3类：经济型/改善型/豪宅）..."):
        clustered_df = run_kmeans_clustering(df, n_clusters=3)

    if "分类" in clustered_df.columns:
        col_cluster1, col_cluster2 = st.columns([1, 1])
        with col_cluster1:
            cluster_dist = clustered_df["分类"].value_counts().reset_index()
            cluster_dist.columns = ["分类", "数量"]
            cluster_dist["占比"] = (cluster_dist["数量"] / cluster_dist["数量"].sum() * 100).round(1)
            st.dataframe(cluster_dist, use_container_width=True, hide_index=True)

            # 各类均价
            cluster_price = clustered_df.groupby("分类").agg(
                均价=("均价_数值", "mean"), 总价=("总价_数值", "mean"), 面积=("面积_数值", "mean")
            ).reset_index()
            cluster_price["均价"] = cluster_price["均价"].round(0).astype(int)
            cluster_price["总价"] = cluster_price["总价"].round(1)
            cluster_price["面积"] = cluster_price["面积"].round(1)
            st.dataframe(cluster_price, use_container_width=True, hide_index=True)

        with col_cluster2:
            with st.spinner("加载聚类散点图..."):
                from charts import create_clustering_scatter
                st.markdown('<div style="margin-top: -15px;">', unsafe_allow_html=True)
                st.components.v1.html(create_clustering_scatter(clustered_df).render_embed(), height=500, scrolling=False)
                st.markdown('</div>', unsafe_allow_html=True)

    # 数据表格
    st.markdown("---")
    st.markdown("### 📄 房源数据")

    # 显示列
    display_cols = ["标题", "所属城区", "户型", "面积", "均价", "总价", "装修情况", "楼层类别", "房龄_计算"]
    available = [c for c in display_cols if c in clustered_df.columns]

    # 如果装修在标题里
    if "装修情况" not in clustered_df.columns and "标题" in clustered_df.columns:
        clustered_df["装修情况"] = clustered_df["标题"].apply(parse_decoration)
        available = [c for c in display_cols if c in clustered_df.columns]

    # 分类列
    if "分类" in clustered_df.columns and "分类" not in available:
        available.insert(1, "分类")

    with st.expander("📄 点击展开/收起数据表格", expanded=False):
        st.dataframe(
            clustered_df[available].head(1000),
            use_container_width=True,
            hide_index=True,
            column_config={
                "标题": st.column_config.TextColumn("房源标题", width="large"),
                "分类": st.column_config.TextColumn("分类", width="small"),
                "所属城区": st.column_config.TextColumn("区域", width="small"),
                "户型": st.column_config.TextColumn("户型", width="medium"),
                "面积": st.column_config.TextColumn("面积", width="small"),
                "均价": st.column_config.TextColumn("均价", width="small"),
                "总价": st.column_config.TextColumn("总价", width="small"),
                "装修情况": st.column_config.TextColumn("装修", width="small"),
                "楼层类别": st.column_config.TextColumn("楼层", width="small"),
                "房龄_计算": st.column_config.NumberColumn("房龄(年)", format="%.0f"),
            },
        )
        st.caption(f"当前显示前1000条（共 {len(clustered_df):,} 条），筛选后数据量较大请耐心加载")

    # 数据导出提示
    st.info("💡 聚类结果已缓存在当前会话中，刷新页面后重新计算")


# ==================== 主函数 ====================

def main():
    render_css()
    filters = render_sidebar()

    with st.spinner("🔄 正在加载数据（167,297 条 5年数据）..."):
        df = load_data()
        time.sleep(0.2)

    # 预处理
    df = prepare_dataframe(df)
    filtered_df = apply_filters(df, filters)

    st.title("🏠 重庆二手房数据可视化平台")

    if filtered_df.empty:
        st.warning("⚠️ 当前筛选条件下没有数据，请调整筛选条件")
        return

    # Tab 布局
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 数据总览", "🏆 排行榜", "📈 图表分析", "🔮 房价预测", "📋 数据明细"
    ])

    with tab1:
        render_overview_tab(filtered_df)
    with tab2:
        render_ranking_tab(filtered_df)
    with tab3:
        render_charts_tab(filtered_df)
    with tab4:
        render_prediction_tab(filtered_df)
    with tab5:
        render_data_tab(filtered_df)

    st.markdown("---")
    st.caption("© 2026 重庆二手房数据分析项目 | 链家/贝壳 | Streamlit + Pyecharts + scikit-learn")


if __name__ == "__main__":
    main()
