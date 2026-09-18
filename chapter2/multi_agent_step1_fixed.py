import math
import os
import sys
from typing import Optional, Tuple
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from smolagents import CodeAgent, OpenAIServerModel, Tool, tool

# ==============================================================================
# 0. 稳定搜索工具：基于国内网络畅通的 Bing 搜索，彻底告别海外网络超时
# ==============================================================================
class BingSearchTool(Tool):
    name = "web_search"
    description = "在必应 (Bing) 上检索全球地理位置、电影取景地及经纬度坐标。"
    inputs = {
        "query": {
            "type": "string",
            "description": "要搜索的关键词或地点名",
        }
    }
    output_type = "string"

    def forward(self, query: str) -> str:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = "https://cn.bing.com/search?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            results = []
            for li in soup.find_all("li", class_="b_algo")[:3]:
                title = li.find("h2")
                snippet = li.find("p")
                t_text = title.get_text().strip() if title else ""
                s_text = snippet.get_text().strip() if snippet else ""
                if t_text or s_text:
                    results.append(f"【{t_text}】: {s_text}")
            return "\n\n".join(results) if results else f"未找到关于 {query} 的搜索结果。"
        except Exception as e:
            return f"搜索请求异常: {e}"

# 1. 航程测算工具
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
    lat1, lon1 = map(math.radians, origin_coords)
    lat2, lon2 = map(math.radians, destination_coords)

    EARTH_RADIUS_KM = 6371.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    distance = EARTH_RADIUS_KM * c

    actual_distance = distance * 1.1
    flight_time = (actual_distance / cruising_speed_kmh) + 1.0
    return round(flight_time, 2)


model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
    flatten_messages_as_text=True,
)

# 2. 改进后的专职调研员：限制最大步数并优化提示
web_agent = CodeAgent(
    model=model,
    tools=[BingSearchTool()],
    name="web_search_agent",
    description="专职搜索员：负责快速搜索现实中的城市或著名建筑的大致经纬度坐标 (纬度, 经度)。",
    max_steps=4,  # 熔断保护：最多搜索 4 步，禁止无限期死磕
)

# 3. 改进后的主管经理：加入清晰的执行约束与防死循环提示
manager_agent = CodeAgent(
    model=model,
    tools=[calculate_cargo_travel_time],
    managed_agents=[web_agent],
    max_steps=5,  # 熔断保护：经理最多 5 步
)

# 4. 优化后的任务指令：指令明确、输入输出清晰
task = """
阿福需要找回失踪的蝙蝠车。请严格按照以下两步执行：
步骤 1：直接调用你的下属 `web_search_agent` 查询 2 个《蝙蝠侠》电影取景城市的大致经纬度（例如芝加哥或伦敦等城市的经纬度元组）。
步骤 2：拿到经纬度后，直接调用你手上的工具 `calculate_cargo_travel_time` 计算运回哥谭市（40.7128, -74.0060）所需的飞行时间。严禁自己手写数学公式！
完成计算后，请直接调用 `final_answer("...")` 返回最终报告，严禁只使用 print。
"""

print("👉 优化版主管经理智能体启动...\n")
response = manager_agent.run(task)

print("\n🎉 最终给阿福的报告:\n")
print(response)

