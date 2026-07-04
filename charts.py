"""
charts.py - Pyecharts 图表生成模块

包含所有可视化图表的生成函数
"""

import pyecharts.options as opts
from pyecharts.charts import Bar, Scatter, HeatMap, Pie, Line, Page, Map
from pyecharts.globals import ThemeType
from pyecharts.commons.utils import JsCode
import pandas as pd
import numpy as np
import re
import json
import os

COLOR_SEQUENCE = [
    "#1E88E5", "#43A047", "#FFB300", "#E53935",
    "#8E24AA", "#00ACC1", "#FF6F00", "#3949AB",
    "#C0CA33", "#6D4C41"
]


def get_district_colors(districts):
    return {d: COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)] for i, d in enumerate(districts)}


def _empty_chart(message="暂无数据"):
    from pyecharts.charts import Bar as EmptyBar
    chart = (EmptyBar(init_opts=opts.InitOpts(width="100%", height="300px"))
        .add_xaxis(["暂无数据"]).add_yaxis("", [0], label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title=message, title_textstyle_opts=opts.TextStyleOpts(font_size=16), pos_left="center", pos_top="center"),
                         xaxis_opts=opts.AxisOpts(is_show=False), yaxis_opts=opts.AxisOpts(is_show=False)))
    return chart


# ==================== 地图名称映射 ====================

# ==================== 1. 重庆各区县分布总览 ====================

def create_chongqing_heatmap(df, price_col="均价_数值"):
    """
    重庆各区县房源数量排名 - 横向条形图
    展示房源数量Top20区县，颜色=房源数渐变
    替代地图展示（避免CDN地图数据在云端加载失败）
    """
    if df.empty:
        return _empty_chart("暂无数据")

    stats = df.groupby("所属城区").agg(
        count=("标题", "count"),
        price=("均价_数值", "mean")
    ).reset_index().sort_values("count", ascending=False).head(20)

    if stats.empty:
        return _empty_chart("暂无数据")

    districts = stats["所属城区"].tolist()[::-1]  # 反转，让最高的在上面
    counts = stats["count"].tolist()[::-1]

    chart = (
        Bar(init_opts=opts.InitOpts(width="100%", height="600px", theme=ThemeType.LIGHT))
        .add_xaxis(districts)
        .add_yaxis(
            "房源数量",
            counts,
            label_opts=opts.LabelOpts(is_show=True, position="right", font_size=11),
            itemstyle_opts=opts.ItemStyleOpts(
                color=JsCode("new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#B3D9FF'},{offset:1,color:'#1E88E5'}])")
            ),
        )
        .reversal_axis()  # 横向柱状图
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="重庆各区县房源数量Top20",
                subtitle="横轴 = 房源数量（套）",
                pos_left="center",
            ),
            xaxis_opts=opts.AxisOpts(name="房源数量", axislabel_opts=opts.LabelOpts(font_size=10)),
            yaxis_opts=opts.AxisOpts(
                name="区县",
                axislabel_opts=opts.LabelOpts(font_size=10),
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    return chart

    # 建立名称映射
    name_map = _build_district_name_mapping()

    # 构建数据对，将数据中的区名映射到地图中的标准区名
    data_pairs = []
    skipped = []
    for _, row in district_avg.iterrows():
        d = row["所属城区"]
        map_name = name_map.get(d, d)
        if map_name != d or d in name_map or d.endswith("区") or d.endswith("县"):
            data_pairs.append((map_name, round(row[price_col], 0)))
        else:
            skipped.append(d)

    if not data_pairs:
        return _empty_chart("暂无匹配的地图数据")

    # 找到价格范围用于颜色映射
    prices = [p[1] for p in data_pairs]
    vmin, vmax = min(prices), max(prices)

    chart = (
        Map(init_opts=opts.InitOpts(width="100%", height="600px", theme=ThemeType.LIGHT))
        .add(
            "均价 (元/㎡)",
            data_pairs,
            maptype="重庆",
            is_map_symbol_show=False,
            label_opts=opts.LabelOpts(is_show=True, color="#333", font_size=10),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}<br/>均价: {c} 元/㎡"),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="重庆各区房价分布",
                subtitle="颜色越深 → 房价越高 | 鼠标悬停查看详情",
                pos_left="center"
            ),
            visualmap_opts=opts.VisualMapOpts(
                is_piecewise=False,
                min_=vmin,
                max_=vmax,
                range_color=["#f0f9e8", "#bae4bc", "#7bccc4", "#43a2ca", "#0868ac"],
                pos_left="left",
                pos_bottom="bottom",
                textstyle_opts=opts.TextStyleOpts(color="#333"),
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}<br/>均价: {c} 元/㎡"),
        )
        .set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=1),
            emphasis_opts=opts.EmphasisOpts(
                itemstyle_opts=opts.ItemStyleOpts(area_color="#FF6F00", border_color="#fff")
            ),
        )
    )

    # 如果有跳过的区县，添加注释
    if skipped:
        # 图表底部加一行注释（可选）
        pass

    return chart


# ==================== 2. 价格分布柱状图 ====================

def create_price_distribution_chart(df, price_col="均价_数值", bins=15):
    if df.empty:
        return _empty_chart("暂无价格数据")
    prices = df[price_col].dropna()
    if len(prices) == 0:
        return _empty_chart("暂无价格数据")

    low = prices.quantile(0.005)
    high = prices.quantile(0.995)
    bin_edges = np.linspace(low, high, bins + 1)
    bin_edges = np.round(bin_edges / 100) * 100

    labels = []
    for i in range(len(bin_edges) - 1):
        lo = int(bin_edges[i])
        hi = int(bin_edges[i + 1])
        if i == len(bin_edges) - 2:
            labels.append(f"{lo}+")
        else:
            labels.append(f"{lo}-{hi}")

    counts = []
    for i in range(len(bin_edges) - 1):
        lo = bin_edges[i]
        hi = bin_edges[i + 1]
        if i == len(bin_edges) - 2:
            c = int(((prices >= lo) & (prices <= hi)).sum())
        else:
            c = int(((prices >= lo) & (prices < hi)).sum())
        counts.append(c)
    chart = (Bar(init_opts=opts.InitOpts(width="100%", height="400px", theme=ThemeType.LIGHT))
        .add_xaxis(labels)
        .add_yaxis("房源数量", counts,
            itemstyle_opts=opts.ItemStyleOpts(color=JsCode("new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#1E88E5'},{offset:1,color:'#64B5F6'}])")),
            label_opts=opts.LabelOpts(is_show=True, position="top"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="房源价格分布", subtitle=f"共 {len(prices)} 套房源", pos_left="center"),
            legend_opts=opts.LegendOpts(is_show=False),
            xaxis_opts=opts.AxisOpts(name="价格区间 (元/㎡)", name_location="middle", name_gap=35, axislabel_opts=opts.LabelOpts(rotate=45, font_size=10)),
            yaxis_opts=opts.AxisOpts(name="房源数量", name_location="middle", name_gap=45),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow", formatter="{b}<br/>房源数量: {c} 套"),
            datazoom_opts=[opts.DataZoomOpts(type_="inside", orient="horizontal", range_start=0, range_end=100)]))
    return chart


# ==================== 3. 面积-均价散点图（每个区域一个点） ====================

def create_scatter_chart(df, price_col="均价_数值", area_col="面积_数值"):
    if df.empty:
        return _empty_chart("暂无数据")

    stats = df.groupby("所属城区").agg(
        avg_area=(area_col, "mean"),
        avg_price=(price_col, "mean"),
        count=("标题", "count"),
    ).dropna().reset_index()
    stats = stats[stats["count"] >= 30].sort_values("avg_price")
    if stats.empty:
        return _empty_chart("暂无数据")

    district_colors = get_district_colors(stats["所属城区"].tolist())

    data_items = []
    for _, r in stats.iterrows():
        d = r["所属城区"]
        color = district_colors[d]
        data_items.append({
            "value": [round(r["avg_area"], 1), round(r["avg_price"], 0)],
            "name": d,
            "itemStyle": {"color": color, "opacity": 0.85},
            "label": {
                "show": True, "position": "right", "fontSize": 10,
                "color": "#333", "formatter": d,
            },
            "symbolSize": 16,
        })

    scatter = Scatter(init_opts=opts.InitOpts(width="100%", height="500px", theme=ThemeType.LIGHT))
    scatter.add_xaxis([])
    scatter.add_yaxis("各区价格", data_items)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="各区面积-均价分布", subtitle="一个点代表一个区域", pos_left="center"),
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            name="平均面积 (㎡)", name_location="middle", name_gap=40,
            axislabel_opts=opts.LabelOpts(font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.2)),
        ),
        yaxis_opts=opts.AxisOpts(
            name="平均均价 (元/㎡)", name_location="middle", name_gap=50,
            axislabel_opts=opts.LabelOpts(font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.2)),
        ),
        tooltip_opts=opts.TooltipOpts(trigger="item",
            formatter=JsCode("function(p){return p.name+'<br/>面积: '+p.value[0]+' ㎡<br/>均价: '+p.value[1]+' 元/㎡';}")))
    return scatter


# ==================== 4. 各区域均价对比 ====================

def create_district_avg_price_chart(df, price_col="均价_数值"):
    if df.empty:
        return _empty_chart("暂无数据")
    district_avg = df.groupby("所属城区")[price_col].mean().reset_index()
    district_avg.columns = ["区域", "均价"]
    district_avg = district_avg.sort_values("均价", ascending=False)
    chart = (Bar(init_opts=opts.InitOpts(width="100%", height="450px", theme=ThemeType.LIGHT))
        .add_xaxis(district_avg["区域"].tolist())
        .add_yaxis("均价 (元/㎡)", [round(v, 0) for v in district_avg["均价"].tolist()],
            itemstyle_opts=opts.ItemStyleOpts(color=JsCode("new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#43A047'},{offset:1,color:'#A5D6A7'}])")),
            label_opts=opts.LabelOpts(is_show=True, position="top", formatter="{c} 元/㎡", font_size=10))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各区域均价对比", subtitle="按均价从高到低排序", pos_left="center"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45, font_size=9)),
            yaxis_opts=opts.AxisOpts(name="均价 (元/㎡)"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            legend_opts=opts.LegendOpts(is_show=False)))
    return chart


# ==================== 5. 价格热力图（区域×户型） ====================

def create_price_heatmap(df, price_col="均价_数值"):
    if df.empty:
        return _empty_chart("暂无数据")
    df = df.copy()
    df["户型_简化"] = df["户型"].apply(
        lambda x: re.match(r"(\d+\s*室)", str(x)).group(1).strip() if re.match(r"(\d+\s*室)", str(x)) else str(x)[:4])
    pivot = df.pivot_table(values=price_col, index="所属城区", columns="户型_简化", aggfunc="mean")
    if pivot.empty:
        return _empty_chart("暂无热力图数据")

    districts, huxing_types = pivot.index.tolist(), pivot.columns.tolist()
    heat_data = []
    non_zero_vals = []
    for i, d in enumerate(districts):
        for j, h in enumerate(huxing_types):
            raw = pivot.loc[d, h]
            if pd.isna(raw):
                heat_data.append([j, i, -1])
            else:
                val = round(raw, 0)
                heat_data.append([j, i, val])
                if val > 0:
                    non_zero_vals.append(val)
    if not non_zero_vals:
        return _empty_chart("暂无热力图数据")

    vmin, vmax = int(min(non_zero_vals)), int(max(non_zero_vals))

    pieces = [
        {"min": -1, "max": 0, "color": "#E8E8E8", "label": "无数据"},
        {"min": 1, "max": 8000, "color": "#FFFFCC", "label": "≤8000"},
        {"min": 8001, "max": 10000, "color": "#FFEDA0", "label": "8000~10000"},
        {"min": 10001, "max": 12000, "color": "#FED976", "label": "10000~12000"},
        {"min": 12001, "max": 14000, "color": "#FEB24C", "label": "12000~14000"},
        {"min": 14001, "max": 16000, "color": "#FD8D3C", "label": "14000~16000"},
        {"min": 16001, "max": 20000, "color": "#FC4E2A", "label": "16000~20000"},
        {"min": 20001, "max": max(vmax, 20001), "color": "#BD0026", "label": "≥20000"},
    ]

    import json as _json
    districts_js = _json.dumps(districts, ensure_ascii=False)
    huxing_js = _json.dumps(huxing_types, ensure_ascii=False)

    chart = (HeatMap(init_opts=opts.InitOpts(width="100%", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(huxing_types).add_yaxis("均价", districts, heat_data,
            label_opts=opts.LabelOpts(is_show=True, font_size=10, color="#333"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="区域×户型 价格热力图", subtitle="颜色越深 → 均价越高 | 灰色 = 无数据", pos_left="center"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30, font_size=9)),
            yaxis_opts=opts.AxisOpts(is_inverse=True),
            visualmap_opts=opts.VisualMapOpts(
                is_piecewise=True,
                pos_left="right", pos_top="center",
                pieces=pieces),
            tooltip_opts=opts.TooltipOpts(formatter=JsCode(f"""
                function(p) {{
                    var districts = {districts_js};
                    var huxing = {huxing_js};
                    var val = p.value[2];
                    if (val <= 0) {{
                        return districts[p.value[1]] + ' - ' + huxing[p.value[0]] + '<br/>无数据';
                    }}
                    return districts[p.value[1]] + ' - ' + huxing[p.value[0]] + '<br/>均价: ' + val + ' 元/㎡';
                }}
            """))))
    return chart


# ==================== 6. 面积-总价散点图（带趋势线） ====================

def create_area_total_trend_scatter(df):
    """面积 vs 总价 散点图 + 线性趋势线"""
    if df.empty:
        return _empty_chart("暂无数据")
    data = df[["面积_数值", "总价_数值"]].dropna()
    if len(data) < 5:
        return _empty_chart("数据不足")
    if len(data) > 2000:
        data = data.sample(2000, random_state=42)

    scatter_data = [[round(row["面积_数值"], 1), round(row["总价_数值"], 1)] for _, row in data.iterrows()]

    from sklearn.linear_model import LinearRegression
    X = data[["面积_数值"]].values
    y = data["总价_数值"].values
    model = LinearRegression().fit(X, y)
    x_range = np.linspace(data["面积_数值"].min(), data["面积_数值"].max(), 50)
    y_pred = model.predict(x_range.reshape(-1, 1))
    trend_data = [[round(float(x_range[i]), 1), round(float(y_pred[i]), 1)] for i in range(len(x_range))]

    scatter = Scatter(init_opts=opts.InitOpts(width="100%", height="450px", theme=ThemeType.LIGHT))
    scatter.add_xaxis([])
    scatter.add_yaxis("房源", scatter_data,
        symbol_size=5, label_opts=opts.LabelOpts(is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color="#1E88E5", opacity=0.5))

    from pyecharts.charts import Line as OverlayLine
    line_chart = (
        OverlayLine()
        .add_xaxis([])
        .add_yaxis("趋势线", trend_data,
            is_smooth=True, symbol_size=0,
            linestyle_opts=opts.LineStyleOpts(color="#E53935", width=3),
            label_opts=opts.LabelOpts(is_show=False))
    )
    scatter = scatter.overlap(line_chart)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="面积与总价关系分析", pos_left="center"),
        xaxis_opts=opts.AxisOpts(
            name="面积 (㎡)", type_="value", min_=0,
            axislabel_opts=opts.LabelOpts(font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.2)),
        ),
        yaxis_opts=opts.AxisOpts(
            name="总价 (万元)", type_="value", min_=0,
            axislabel_opts=opts.LabelOpts(font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.2)),
        ),
        tooltip_opts=opts.TooltipOpts(trigger="item",
            formatter=JsCode("function(p) { return '面积: ' + p.value[0] + ' ㎡<br/>总价: ' + p.value[1] + ' 万元'; }")),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center"))
    legend_data = scatter.options.get("legend", [{}])[0].get("data", [])
    scatter.options["legend"][0]["data"] = [d for d in legend_data if d == "房源"]
    return scatter


# ==================== 7. 房龄趋势折线图 ====================

def create_age_trend_chart(df):
    """房龄 vs 均价 折线图"""
    if df.empty:
        return _empty_chart("暂无数据")
    data = df.dropna(subset=["房龄_计算", "均价_数值"])
    if data.empty:
        return _empty_chart("暂无数据")

    trend = data.groupby("房龄_计算").agg(均价=("均价_数值", "mean"), 房源数=("标题", "count")).reset_index()
    trend = trend[(trend["房源数"] >= 5) & (trend["房龄_计算"] >= 0) & (trend["房龄_计算"] <= 50)]

    if trend.empty:
        return _empty_chart("数据不足")
    trend = trend.sort_values("房龄_计算")
    ages = [f"{int(a)}年" for a in trend["房龄_计算"]]
    prices = trend["均价"].round(0).astype(int).tolist()

    chart = (Line(init_opts=opts.InitOpts(width="100%", height="400px", theme=ThemeType.LIGHT))
        .add_xaxis(ages)
        .add_yaxis("均价 (元/㎡)", prices,
            is_smooth=True,
            symbol="circle", symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(width=3, color="#1E88E5"),
            itemstyle_opts=opts.ItemStyleOpts(color="#1E88E5"),
            label_opts=opts.LabelOpts(is_show=False))
        .set_series_opts(areastyle_opts=opts.AreaStyleOpts(color=JsCode("new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(30,136,229,0.3)'},{offset:1,color:'rgba(30,136,229,0.01)'}])")))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="房龄-均价趋势图", subtitle="房龄越老价格变化趋势", pos_left="center"),
            xaxis_opts=opts.AxisOpts(name="房龄（年）", axislabel_opts=opts.LabelOpts(rotate=45, font_size=9)),
            yaxis_opts=opts.AxisOpts(name="均价 (元/㎡)"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", formatter="{b}<br/>均价: {c} 元/㎡"),
            datazoom_opts=[opts.DataZoomOpts(type_="inside", orient="horizontal")]))
    return chart


# ==================== 8. 户型分布饼图 ====================

def create_huxing_pie_chart(df):
    """户型分布饼图"""
    if df.empty:
        return _empty_chart("暂无数据")
    from analysis import get_huxing_distribution
    dist = get_huxing_distribution(df)
    if dist.empty:
        return _empty_chart("暂无数据")

    data_pairs = [list(z) for z in zip(dist["户型"].tolist(), dist["数量"].tolist())]

    chart = (Pie(init_opts=opts.InitOpts(width="100%", height="400px", theme=ThemeType.LIGHT))
        .add("户型", data_pairs,
            radius=["35%", "60%"],
            center=["50%", "55%"],
            label_opts=opts.LabelOpts(formatter="{b}: {d}%", font_size=11),
            itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="户型分布占比", pos_left="center"),
            legend_opts=opts.LegendOpts(pos_top="30px", orient="horizontal")))
    return chart


# ==================== 9. 装修情况柱状图 ====================

def create_decoration_bar_chart(df):
    """装修情况柱状图（各装修类型的房源数量和均价）"""
    if df.empty:
        return _empty_chart("暂无数据")
    from analysis import get_decoration_distribution, get_price_summary_by_deco
    dist = get_decoration_distribution(df)
    if dist.empty:
        return _empty_chart("暂无数据")

    deco_order = ["毛坯", "简装", "精装", "豪装", "未知"]
    dist["装修情况"] = pd.Categorical(dist["装修情况"], categories=deco_order, ordered=True)
    dist = dist.sort_values("装修情况")

    bar = (Bar(init_opts=opts.InitOpts(width="100%", height="400px", theme=ThemeType.LIGHT))
        .add_xaxis(dist["装修情况"].tolist())
        .add_yaxis("房源数量", dist["数量"].tolist(),
            itemstyle_opts=opts.ItemStyleOpts(color=JsCode("new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#FFB300'},{offset:1,color:'#FFD54F'}])")),
            label_opts=opts.LabelOpts(is_show=True, position="top"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="装修情况分布", pos_left="center"),
            xaxis_opts=opts.AxisOpts(name="装修类型"),
            yaxis_opts=opts.AxisOpts(name="房源数量"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            legend_opts=opts.LegendOpts(is_show=False)))
    return bar


# ==================== 10. 聚类散点图 ====================

def create_clustering_scatter(df):
    """KMeans 聚类结果散点图（面积×总价，按分类着色）"""
    if df.empty:
        return _empty_chart("暂无数据")
    if "分类" not in df.columns:
        return _empty_chart("请先运行聚类分析")

    data = df.dropna(subset=["面积_数值", "总价_数值", "分类"])
    if data.empty:
        return _empty_chart("聚类数据不足")

    cluster_colors = {"经济型": "#43A047", "改善型": "#1E88E5", "豪宅": "#E53935", "老破小": "#8E24AA", "未知": "#BDBDBD"}
    cluster_order = ["经济型", "改善型", "豪宅", "老破小", "未知"]

    scatter = Scatter(init_opts=opts.InitOpts(width="100%", height="500px", theme=ThemeType.LIGHT))
    scatter.add_xaxis([])

    for cat in cluster_order:
        d = data[data["分类"] == cat]
        if d.empty:
            continue
        if len(d) > 1000:
            d = d.sample(1000, random_state=42)
        pairs = [[round(row["面积_数值"], 1), round(row["总价_数值"], 1)]
                 for _, row in d.iterrows()]
        scatter.add_yaxis(cat, pairs,
            symbol_size=6, label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color=cluster_colors.get(cat, "#BDBDBD"), opacity=0.6))

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="房源聚类分布（KMeans）", pos_left="center", pos_top="0"),
        xaxis_opts=opts.AxisOpts(
            name="面积 (㎡)", type_="value", min_=0,
            axislabel_opts=opts.LabelOpts(font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.2)),
        ),
        yaxis_opts=opts.AxisOpts(
            name="总价 (万元)", type_="value", min_=0,
            axislabel_opts=opts.LabelOpts(font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.2)),
        ),
        tooltip_opts=opts.TooltipOpts(trigger="item",
            formatter=JsCode("function(p) { return p.seriesName + '<br/>面积: ' + p.value[0] + ' ㎡<br/>总价: ' + p.value[1] + ' 万元'; }")),
        legend_opts=opts.LegendOpts(pos_bottom="40", pos_left="center"))
    scatter.options["grid"] = [{"top": 65}]
    return scatter
