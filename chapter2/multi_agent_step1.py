import math
import os
import sys
from typing import Optional, Tuple
from dotenv import load_dotenv

# 确保 Windows 终端能正确打印多语言和特殊字符
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from smolagents import CodeAgent, DuckDuckGoSearchTool, OpenAIServerModel, tool

# ==============================================================================
# 1. 官方原版工具：根据经纬度计算货运飞机航程时间（大圆航线公式 Haversine）
# ==============================================================================
@tool
def calculate_cargo_travel_time(
    origin_coords: Tuple[float, float],
    destination_coords: Tuple[float, float],
    cruising_speed_kmh: Optional[float] = 750.0,
) -> float:
    """
    计算货运飞机在地球两点之间的飞行时间（小时）。

    Args:
        origin_coords: 起点经纬度元组 (纬度, 经度)
        destination_coords: 终点经纬度元组 (纬度, 经度)
        cruising_speed_kmh: 飞机巡航速度，默认 750 km/h
    """

    def to_radians(degrees: float) -> float:
        return degrees * (math.pi / 180)

    lat1, lon1 = map(to_radians, origin_coords)
    lat2, lon2 = map(to_radians, destination_coords)

    EARTH_RADIUS_KM = 6371.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    distance = EARTH_RADIUS_KM * c

    # 增加 10% 的航线绕飞冗余 + 1 小比起飞降落耗时
    actual_distance = distance * 1.1
    flight_time = (actual_distance / cruising_speed_kmh) + 1.0
    return round(flight_time, 2)


# ==============================================================================
# 2. 初始化大模型底座
# ==============================================================================
model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
    flatten_messages_as_text=True,
)

# ==============================================================================
# 3. 专职调研员智能体 (Web Search Specialist)
# ==============================================================================
web_agent = CodeAgent(
    model=model,
    tools=[DuckDuckGoSearchTool()],
    name="web_search_agent",
    description="专职调研员：负责在互联网上搜索准确的地理位置、历史信息及取景地数据。",
)

# ==============================================================================
# 4. 主管经理智能体 (Manager Agent)
# ==============================================================================
manager_agent = CodeAgent(
    model=model,
    tools=[calculate_cargo_travel_time],  # 经理掌握航程计算工具
    managed_agents=[web_agent],  # 经理手下管辖 web_agent
)

# ==============================================================================
# 5. 执行复合任务：为阿福寻找蝙蝠车并计算运往哥谭的时间
# ==============================================================================
task = """
阿福需要找回蝙蝠车。请完成以下两步：
1. 派你的调研员找出 2 个著名的《蝙蝠侠》电影取景地（包含经纬度坐标）；
2. 使用你的测算工具，计算将道具从这些地点用货机运回哥谭市（纬度 40.7128, 经度 -74.0060）各自需要飞行多少小时。
最后汇总成清晰的报告返回。
"""

print("👉 主管经理智能体开始统筹执行任务...\n")
response = manager_agent.run(task)

print("\n🎉 最终给阿福的报告:\n")
print(response)

