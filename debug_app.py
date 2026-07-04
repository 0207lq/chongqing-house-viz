"""快速诊断 - 测试 pyecharts 在 streamlit 中的渲染"""
import sys
sys.path.insert(0, r'D:\my-project\visualization')
import streamlit as st

st.title("诊断测试")

st.write("Step 1: 导入模块...")
from mock_data import generate_mock_data
st.write("✅ mock_data")

# 生成数据
df = generate_mock_data(20)
st.write(f"✅ 数据生成: {len(df)} 条")

from charts import create_price_distribution_chart, create_chongqing_map, create_district_avg_price_chart
st.write("✅ charts")

st.write("Step 2: 渲染地图...")
try:
    from pyecharts.charts import Geo
    from pyecharts.globals import GeoType
    from pyecharts import options as opts

    geo = Geo()
    geo.add_schema(maptype="重庆")
    geo.add("test", [("渝北", 100)], type_=GeoType.SCATTER)
    geo.set_global_opts(title_opts=opts.TitleOpts(title="Test"))
    html = geo.render_embed()
    st.write(f"✅ 地图 HTML 渲染成功, 长度: {len(html)}")
    st.components.v1.html(html, height=400)
except Exception as e:
    st.error(f"❌ 地图: {e}")

st.write("Step 3: 渲染价格分布图...")
try:
    chart = create_price_distribution_chart(df)
    html = chart.render_embed()
    st.write(f"✅ 价格图 HTML 渲染成功, 长度: {len(html)}")
    st.components.v1.html(html, height=400)
except Exception as e:
    st.error(f"❌ 价格图: {e}")

st.write("Step 4: 渲染区域均价图...")
try:
    chart = create_district_avg_price_chart(df)
    html = chart.render_embed()
    st.write(f"✅ 区域图 HTML 渲染成功")
    st.components.v1.html(html, height=400)
except Exception as e:
    st.error(f"❌ 区域图: {e}")

st.write("Step 5: 渲染散点图...")
try:
    from charts import create_scatter_chart
    chart = create_scatter_chart(df)
    html = chart.render_embed()
    st.write(f"✅ 散点图 HTML 渲染成功")
    st.components.v1.html(html, height=400)
except Exception as e:
    st.error(f"❌ 散点图: {e}")

st.write("Step 6: 渲染热力图...")
try:
    from charts import create_price_heatmap
    chart = create_price_heatmap(df)
    html = chart.render_embed()
    st.write(f"✅ 热力图 HTML 渲染成功")
    st.components.v1.html(html, height=400)
except Exception as e:
    st.error(f"❌ 热力图: {e}")

st.success("全部诊断完成!")
