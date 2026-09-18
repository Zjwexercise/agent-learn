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

from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from smolagents import CodeAgent, OpenAIServerModel, Tool, tool

# ==============================================================================
# 1. 知识库档案：韦恩集团内部收录的《蝙蝠侠》全球取景地与真实经纬度档案
# ==============================================================================
filming_records = [
    {
        "text": "Location: Wollaton Hall, Nottingham, UK. Role: Wayne Manor in The Dark Knight Rises. Coordinates: (52.9478, -1.2094). Status: Batmobile prototype kept in secret underground vault.",
        "source": "WarnerBros-Archive-UK",
    },
    {
        "text": "Location: Chicago Board of Trade Building, Chicago, USA. Role: Wayne Enterprises Headquarters in Batman Begins. Coordinates: (41.8781, -87.6298). Status: Tumbler prop vehicle parked in lower garage.",
        "source": "WarnerBros-Archive-US",
    },
    {
        "text": "Location: Glasgow Necropolis, Glasgow, Scotland. Role: Gotham City cemetery chase scene in The Batman. Coordinates: (55.8625, -4.2322). Status: Stunt Batcycle and support vehicles located here.",
        "source": "WarnerBros-Archive-Scotland",
    },
    {
        "text": "Location: Mehrangarh Fort, Jodhpur, India. Role: The Pit prison underground escape in The Dark Knight Rises. Coordinates: (26.2978, 73.0186). Status: Heavy armor vehicle wreckage on site.",
        "source": "WarnerBros-Archive-Asia",
    },
]

source_docs = [
    Document(page_content=r["text"], metadata={"source": r["source"]})
    for r in filming_records
]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
docs_processed = text_splitter.split_documents(source_docs)

# ==============================================================================
# 2. 封装专属 RAG 检索工具：给专职下属使用（返回干净的结构化列表）
# ==============================================================================
class BatmanLocationRetrieverTool(Tool):
    name = "batman_location_retriever"
    description = (
        "查询韦恩集团内部的《蝙蝠侠》全球取景地真实档案，包含地点名称、电影角色和精准经纬度坐标。"
        "返回一个包含各地点详细档案文本的 Python 字符串列表。"
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "查询关键词，例如地点名、城市名或电影角色",
        }
    }
    output_type = "any"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.retriever = BM25Retriever.from_documents(docs, k=3)

    def forward(self, query: str) -> list[str]:
        docs = self.retriever.invoke(query)
        return [d.page_content for d in docs]

# ==============================================================================
# 3. 官方航程测算工具：给经理使用
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


# ==============================================================================
# 4. 构建多智能体团队 (Multi-Agent Team)
# ==============================================================================
model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
    flatten_messages_as_text=True,
)

# 专属档案调研专员 (Retriever Specialist Agent)
retriever_tool = BatmanLocationRetrieverTool(docs_processed)

archive_agent = CodeAgent(
    model=model,
    tools=[retriever_tool],
    name="batman_archive_agent",
    description="专职档案员：能够使用 batman_location_retriever 检索电影取景地精准的经纬度坐标与车辆状态。",
    max_steps=3,
)

# 主管调度经理 (Manager Agent)
manager_agent = CodeAgent(
    model=model,
    tools=[calculate_cargo_travel_time],
    managed_agents=[archive_agent],
    max_steps=4,
)

# ==============================================================================
# 5. 执行复合任务：Multi-Agent RAG 协同作战
# ==============================================================================
task = """
阿福急需找回蝙蝠车以备派对使用。请按以下流程处理：
1. 指派你的档案员 `batman_archive_agent` 查询 2 个留存有道具蝙蝠车的取景地及其坐标。
2. 使用你的 `calculate_cargo_travel_time` 工具，计算将车辆运回哥谭市（40.7128, -74.0060）各自需要几小时飞行时间。
3. 整理成一份清晰易懂的报告，使用 final_answer 提交。
"""

print("👉 多智能体 RAG 系统启动...\n")
response = manager_agent.run(task)

print("\n🎉 呈送阿福的最终决策报告:\n")
print(response)

