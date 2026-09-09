import os
import sys
import math
import datetime
import pytz
import yaml

# 保证从任何目录运行都能正确定位本地 tools 与 Gradio_UI 模块
sys.path.append(os.path.dirname(__file__))

# 兼容 Windows 控制台的 UTF-8 输出
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from dotenv import load_dotenv, find_dotenv
from smolagents import CodeAgent, OpenAIServerModel, tool
from tools.final_answer import FinalAnswerTool
from tools.web_search import DuckDuckGoSearchTool
from tools.visit_webpage import VisitWebpageTool
from Gradio_UI import GradioUI

# -------------------------------------------------------------
# 1. 加载配置与模型初始化 (安全读取 .env，不泄露密钥)
# -------------------------------------------------------------
load_dotenv(find_dotenv())
api_key = os.environ.get("ZHIPUAI_API_KEY")

if not api_key:
    raise ValueError("未在根目录 .env 中检测到 ZHIPUAI_API_KEY，请检查密钥配置！")

# 使用智谱 GLM-4 模型 (flatten_messages_as_text=True 确保智谱精准解析用户提问)
model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=api_key,
    flatten_messages_as_text=True,
)

# -------------------------------------------------------------
# 2. 定义智能体工具箱 (在此基础上修改和添加新工具)
# -------------------------------------------------------------

# 常用城市与 IANA 时区对照表
CITY_TIMEZONE_MAP = {
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "shenyang": "Asia/Shanghai",
    "tokyo": "Asia/Tokyo",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "new york": "America/New_York",
    "san francisco": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "sydney": "Australia/Sydney",
}

@tool
def get_current_time_in_timezone(location_or_timezone: str) -> str:
    """获取指定城市或有效时区的当前本地时间。
    Args:
        location_or_timezone: 城市名称 (如 'Beijing', 'Paris', 'London') 或标准时区字符串 (如 'America/New_York', 'Asia/Shanghai')。
    """
    key = location_or_timezone.lower().strip()
    tz_str = CITY_TIMEZONE_MAP.get(key, location_or_timezone)
    try:
        tz = pytz.timezone(tz_str)
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"{location_or_timezone} 的当前时间为: {local_time}"
    except Exception as e:
        return f"查询时区 '{location_or_timezone}' 失败: {str(e)}"

@tool
def get_weather(location: str) -> str:
    """查询指定城市的实时天气情况与气温信息。
    Args:
        location: 城市名称 (例如 'Beijing', 'Paris', 'London', 'Shenyang')。
    """
    mock_weather = {
        "beijing": "晴空万里，微风，气温 23°C，体感舒适",
        "shanghai": "多云转晴，气温 25°C，湿度 60%",
        "shenyang": "晴，秋高气爽，气温 15°C - 24°C",
        "paris": "晴朗，气温 20°C，湿度 45%，微风",
        "london": "多云，偶有零星小雨，气温 16°C",
        "new york": "阴天，气温 18°C，西北风 3级",
        "tokyo": "晴天，气温 22°C，紫外线中等",
    }
    key = location.lower().strip()
    report = mock_weather.get(key, f"天气良好，晴间多云，气温约 20°C")
    return f"{location} 当前天气: {report}"

@tool
def calculator(expression: str) -> str:
    """计算数学表达式的结果（如 '2 ** 10', 'sqrt(144) + 25 * 3' 等）。
    Args:
        expression: 要计算的数学表达式字符串。
    """
    try:
        # 安全计算命名空间
        allowed_names = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "pow": math.pow,
            "log": math.log,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "round": round,
        }
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算表达式 '{expression}' 失败: {str(e)}"

@tool
def my_custom_tool(text: str) -> str:
    """对给定文本进行字数统计、行数分析及特征提取。
    Args:
        text: 需要分析的文本内容。
    """
    char_count = len(text)
    word_count = len(text.split())
    line_count = len(text.splitlines())
    return f"【文本分析】总字符数: {char_count}，词数: {word_count}，行数: {line_count}"

# 实例化官方工具
final_answer = FinalAnswerTool()
web_search = DuckDuckGoSearchTool(max_results=5)
visit_webpage = VisitWebpageTool()

# -------------------------------------------------------------
# 3. 加载 prompts.yaml 提示词配置
# -------------------------------------------------------------
prompts_file = os.path.join(os.path.dirname(__file__), "prompts.yaml")
with open(prompts_file, "r", encoding="utf-8") as stream:
    prompt_templates = yaml.safe_load(stream)

# -------------------------------------------------------------
# 4. 构建 CodeAgent (装配所有添加的工具)
# -------------------------------------------------------------
agent = CodeAgent(
    model=model,
    tools=[
        final_answer,                  # 必需的结束回答工具
        get_current_time_in_timezone,  # 时间查询工具
        get_weather,                   # 天气查询工具
        calculator,                    # 数学计算工具
        web_search,                    # 网页检索工具 (DuckDuckGo)
        visit_webpage,                 # 网页抓取与阅读工具
        my_custom_tool,                # 文本分析工具
    ],
    max_steps=6,
    verbosity_level=1,
    prompt_templates=prompt_templates,
)

# -------------------------------------------------------------
# 5. 入口：支持命令行自测与 Gradio 网页端交互
# -------------------------------------------------------------
if __name__ == "__main__":
    if "--cli" in sys.argv:
        test_query = "请帮我查一下巴黎的天气，以及北京现在的当地时间？"
        print(f"👉 [CLI 模式] 提问: {test_query}\n")
        response = agent.run(test_query)
        print(f"\n🎉 [CLI 模式] 智能体最终回答:\n{response}")
    else:
        print("🚀 正在启动 Gradio Web 可视化交互界面...")
        print("💡 提示：在命令行加参数 --cli 可直接进行终端快速测试 (例如: python app.py --cli)")
        GradioUI(agent).launch(inbrowser=True)
