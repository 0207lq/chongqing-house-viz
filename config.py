"""
config.py - 项目配置文件

包含重庆区县信息、数据路径、颜色主题等配置
"""

# ==================== 重庆区县配置 ====================
# 格式: [中文名, 拼音, 经度, 纬度]
CHONGQING_DISTRICTS = [
    {"name": "渝北", "pinyin": "yubei", "lng": 106.631, "lat": 29.718},
    {"name": "江北", "pinyin": "jiangbei", "lng": 106.574, "lat": 29.606},
    {"name": "南岸", "pinyin": "nanan", "lng": 106.563, "lat": 29.523},
    {"name": "九龙坡", "pinyin": "jiulongpo", "lng": 106.511, "lat": 29.502},
    {"name": "沙坪坝", "pinyin": "shapingba", "lng": 106.456, "lat": 29.541},
    {"name": "大渡口", "pinyin": "dadukou", "lng": 106.482, "lat": 29.484},
    {"name": "北碚", "pinyin": "beibei", "lng": 106.396, "lat": 29.805},
    {"name": "巴南", "pinyin": "banan", "lng": 106.540, "lat": 29.402},
    {"name": "渝中", "pinyin": "yuzhong", "lng": 106.569, "lat": 29.553},
    {"name": "两江新区", "pinyin": "liangjiangxinqu", "lng": 106.573, "lat": 29.677},
    {"name": "綦江", "pinyin": "qijiang", "lng": 106.651, "lat": 29.028},
    {"name": "长寿", "pinyin": "changshou", "lng": 107.081, "lat": 29.834},
    {"name": "涪陵", "pinyin": "fuling", "lng": 107.390, "lat": 29.703},
    {"name": "江津", "pinyin": "jiangjin", "lng": 106.259, "lat": 29.290},
    {"name": "合川", "pinyin": "hechuan", "lng": 106.276, "lat": 29.973},
    {"name": "永川", "pinyin": "yongchuan", "lng": 105.927, "lat": 29.356},
    {"name": "璧山", "pinyin": "bishan", "lng": 106.231, "lat": 29.592},
    {"name": "铜梁", "pinyin": "tongliang", "lng": 106.056, "lat": 29.845},
    {"name": "大足", "pinyin": "dazu", "lng": 105.722, "lat": 29.707},
    {"name": "南川", "pinyin": "nanchuan", "lng": 107.099, "lat": 29.158},
    {"name": "酉阳", "pinyin": "youyang", "lng": 108.768, "lat": 28.841},
    {"name": "云阳", "pinyin": "yunyang", "lng": 108.697, "lat": 30.931},
    {"name": "梁平", "pinyin": "liangping", "lng": 107.802, "lat": 30.674},
    {"name": "奉节", "pinyin": "fengjie", "lng": 109.464, "lat": 31.018},
    {"name": "石柱", "pinyin": "shizhu", "lng": 108.114, "lat": 30.000},
    {"name": "巫溪", "pinyin": "wuxi", "lng": 109.630, "lat": 31.399},
    {"name": "巫山", "pinyin": "wushan", "lng": 109.879, "lat": 31.075},
    {"name": "黔江", "pinyin": "qianjiang", "lng": 108.771, "lat": 29.533},
    {"name": "丰都", "pinyin": "fengdu", "lng": 107.731, "lat": 29.864},
    {"name": "武隆", "pinyin": "wulong", "lng": 107.760, "lat": 29.326},
    {"name": "荣昌", "pinyin": "rongchang", "lng": 105.594, "lat": 29.405},
    {"name": "城口", "pinyin": "chengkou", "lng": 108.664, "lat": 31.948},
    {"name": "秀山", "pinyin": "xiushan", "lng": 109.007, "lat": 28.448},
    {"name": "万州", "pinyin": "wanzhou", "lng": 108.409, "lat": 30.808},
    {"name": "垫江", "pinyin": "dianjiang", "lng": 107.333, "lat": 30.327},
    {"name": "开州", "pinyin": "kaizhou", "lng": 108.393, "lat": 31.161},
    {"name": "忠县", "pinyin": "zhongxian", "lng": 108.037, "lat": 30.300},
]

# 所有区县（用于筛选）
MAIN_DISTRICTS = [d["name"] for d in CHONGQING_DISTRICTS]

# ==================== 房龄区间 ====================
AGE_INTERVALS = ["2年内", "2-5年", "5-10年", "10年以上"]

# ==================== 颜色主题 ====================
THEME_COLORS = {
    "primary": "#1E88E5",
    "secondary": "#FF6F00",
    "success": "#43A047",
    "info": "#00ACC1",
    "warning": "#FFB300",
    "danger": "#E53935",
}

# ==================== 数据路径 ====================
# 项目根目录（基于本文件位置）
import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 完整数据库路径
REAL_DB_PATH = os.path.join(
    PROJECT_ROOT,
    "..",
    "2026_7_2",
    "Anjuke-WebCrawler-Visualization-BigDataAnalysis-main",
    "case",
    "project",
    "data",
    "Database",
    "house_data.db"
)

# 清洗后的数据库路径（含数值型字段）
CLEAN_DB_PATH = os.path.join(
    PROJECT_ROOT,
    "..",
    "2026_7_2",
    "Anjuke-WebCrawler-Visualization-BigDataAnalysis-main",
    "case",
    "project",
    "data",
    "CleanData",
    "house_data_cleaned_5years_167299 条.db"
)

# 本地部署路径（Streamlit Cloud 等使用）
LOCAL_DB_PATH = os.path.join(PROJECT_ROOT, "data", "house_data_cleaned.db")
