"""
mock_data.py - 模拟数据模块

在真实数据库接入前，提供20条模拟的重庆房源数据用于开发测试
"""

import pandas as pd
import random
import numpy as np


def generate_mock_data(n=20, seed=42):
    """
    生成模拟的重庆房源数据

    Args:
        n: 生成条数（默认20）
        seed: 随机种子，保证可复现

    Returns:
        pd.DataFrame: 模拟数据
    """
    random.seed(seed)
    np.random.seed(seed)

    # 各区配置（名称 + 平均单价元/㎡ + 平均面积㎡）
    districts_config = [
        ("渝北", 12500, 100),
        ("江北", 14000, 95),
        ("南岸", 12000, 98),
        ("九龙坡", 10500, 95),
        ("沙坪坝", 11000, 92),
        ("大渡口", 8500, 100),
        ("北碚", 9000, 105),
        ("巴南", 8000, 105),
        ("渝中", 14500, 85),
        ("两江新区", 13000, 100),
    ]

    # 户型分布
    huxing_options = [
        "1 室 1 厅 1 卫", "2 室 1 厅 1 卫", "2 室 2 厅 1 卫",
        "3 室 2 厅 1 卫", "3 室 2 厅 2 卫", "4 室 2 厅 2 卫",
        "4 室 2 厅 3 卫", "5 室 2 厅 3 卫"
    ]
    huxing_weights = [0.03, 0.05, 0.10, 0.20, 0.40, 0.12, 0.07, 0.03]

    # 朝向
    direction_options = ["东", "南", "西", "北", "东南", "西南", "东北", "西北", "南北"]
    direction_weights = [0.10, 0.25, 0.08, 0.07, 0.15, 0.12, 0.05, 0.03, 0.15]

    # 楼层类型 + 总层数
    floor_types = ["低层", "中层", "高层"]
    floor_weights = [0.30, 0.40, 0.30]

    # 建造年份范围（2016-2025）
    years = list(range(2016, 2026))

    # 小区名称前缀
    community_prefixes = [
        "龙湖", "万科", "恒大", "融创", "保利", "金科", "碧桂园",
        "华润", "中海", "绿地", "鲁能", "协信", "东原", "旭辉"
    ]
    community_suffixes = [
        "花园", "名城", "天街", "都会", "公馆", "府", "城", "湾",
        "半岛", "中心", "国际", "春晓", "林语", "一号"
    ]

    data_rows = []

    for i in range(n):
        # 1. 随机选取区域
        district_info = random.choice(districts_config)
        district_name = district_info[0]
        avg_price = district_info[1]
        avg_area = district_info[2]

        # 2. 面积（在平均面积上下浮动20%）
        area = round(np.random.normal(avg_area, avg_area * 0.15), 2)
        area = max(30, min(300, area))

        # 3. 户型（根据面积调整）
        if area < 50:
            huxing = random.choices(
                ["1 室 1 厅 1 卫", "2 室 1 厅 1 卫"],
                weights=[0.6, 0.4]
            )[0]
        elif area < 80:
            huxing = random.choice(["2 室 1 厅 1 卫", "2 室 2 厅 1 卫"])
        elif area < 120:
            huxing = random.choices(
                ["3 室 2 厅 1 卫", "3 室 2 厅 2 卫"],
                weights=[0.3, 0.7]
            )[0]
        elif area < 150:
            huxing = random.choices(
                ["3 室 2 厅 2 卫", "4 室 2 厅 2 卫"],
                weights=[0.5, 0.5]
            )[0]
        else:
            huxing = random.choices(
                ["4 室 2 厅 2 卫", "4 室 2 厅 3 卫", "5 室 2 厅 3 卫"],
                weights=[0.5, 0.3, 0.2]
            )[0]

        # 4. 均价（在区域均价上浮动±25%）
        unit_price = max(5000, int(np.random.normal(avg_price, avg_price * 0.15)))

        # 5. 总价 = 面积 × 均价 / 10000（转换为万）
        total_price = round(area * unit_price / 10000, 1)

        # 6. 朝向
        direction = random.choices(direction_options, weights=direction_weights)[0]

        # 7. 楼层
        total_floor = random.choices([6, 8, 11, 18, 26, 28, 32, 33, 40], weights=[5, 15, 10, 15, 10, 10, 15, 10, 10])[0]
        floor_type = random.choices(floor_types, weights=floor_weights)[0]
        floor_str = f"{floor_type}(共{total_floor}层)"

        # 8. 建造年份
        build_year = random.choice(years)
        build_year_str = f"{build_year}年建造"

        # 9. 房龄
        age = 2026 - build_year
        if age <= 2:
            age_interval = "2年内"
        elif age <= 5:
            age_interval = "2-5年"
        elif age <= 10:
            age_interval = "5-10年"
        else:
            age_interval = "10年以上"

        # 10. 小区名
        community = f"{random.choice(community_prefixes)}{random.choice(community_suffixes)}"

        # 11. 区域地址
        address = f"{district_name}{random.choice(['新牌坊', '冉家坝', '观音桥', '杨家坪', '三峡广场', '李家沱', '大学城', '茶园', '照母山', '中央公园'])}"

        # 12. 标题
        title = f"{district_name} {community} {huxing[:2]}房 {'精装' if random.random() > 0.5 else '简装'} {total_price}万"

        data_rows.append({
            "标题": title,
            "户型": huxing,
            "面积": f"{area}㎡",
            "方位": direction,
            "楼层": floor_str,
            "建造年份": build_year_str,
            "所属小区": community,
            "所属区域": address,
            "总价": f"{total_price} 万",
            "均价": f"{unit_price}元/㎡",
            "所属城区": district_name,
            "房龄区间": age_interval,
            # 解析后的数值字段（便于分析）
            "均价_数值": unit_price,
            "总价_数值": total_price,
            "面积_数值": area,
            "房龄_计算": age,
        })

    df = pd.DataFrame(data_rows)
    return df


def get_district_list():
    """获取重庆主要城区列表"""
    return [
        "渝北", "江北", "南岸", "九龙坡", "沙坪坝",
        "大渡口", "北碚", "巴南", "渝中", "两江新区"
    ]


if __name__ == "__main__":
    df = generate_mock_data(20)
    print(f"生成 {len(df)} 条模拟数据")
    print(df[["所属城区", "户型", "总价_数值", "面积_数值", "均价_数值"]].to_string())
