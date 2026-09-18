import os
import sys
from dotenv import load_dotenv
from smolagents import CodeAgent, DuckDuckGoSearchTool, OpenAIServerModel

# 确保 Windows 终端能正确打印多语言和特殊字符
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

# 1. 初始化检索工具（Hugging Face 官方原生工具）
# 【会发生什么】：DuckDuckGoSearchTool 仅负责根据关键词向 DuckDuckGo 搜索，
# 并返回搜索结果的「标题、摘要片段(Snippet)、网页链接(URL)」。它不会打开并读取完整网页正文。
search_tool = DuckDuckGoSearchTool()

# 2. 初始化大模型（使用项目已有的智谱 GLM-4-Flash 底座）
model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
    flatten_messages_as_text=True,
)

# 3. 构建 CodeAgent 智能体
# 【会发生什么】：
# - CodeAgent 拥有一个内置的安全 Python 沙箱解释器。
# - 传入 tools=[search_tool] 表示沙箱中「只注册了 search_tool 这一个外部函数」。
# - 如果模型在后续步骤中“自作聪明”想调用未提供的函数（如 visit_webpage 读取网页），
#   沙箱会直接报错拦截 (InterpreterError: Forbidden function evaluation)，
#   迫使智能体调整策略，只利用它已经检索到的数据来作答。
agent = CodeAgent(
    model=model,
    tools=[search_tool],
)

# 4. 官方教程原题：为管家阿福策划豪华超级英雄派对
prompt = "Search for luxury superhero-themed party ideas, including decorations, entertainment, and catering."
print(f"👉 开始执行任务: {prompt}\n")

# 【执行 agent.run(prompt) 时，底层会经历的完整 RAG 与 ReAct 循环】：
#
#  ▶ 第 1 步【Thought (思考) & Code (行动)】：
#    大模型分析需求，发现自己需要派对点子，决定调用 search_tool(query="luxury superhero themed party...")
#
#  ▶ 第 2 步【Sandbox 执行 & Observation (检索检索结果注入)】-> 【RAG 的 R 与 A】：
#    沙箱执行 Python 搜索代码，DuckDuckGo 返回网页标题和摘要。这些外部检索到的内容被自动拼装进上下文（Augment）。
#
#  ▶ 第 3 步【模型的尝试与沙箱限制】：
#    模型看到搜索摘要后，想深入看网页细节，可能会尝试写代码调用 `visit_webpage(url)`。
#    由于我们只给了 `search_tool`，沙箱报错拦截：`Forbidden function evaluation 'visit_webpage'`。
#
#  ▶ 第 4 步【自我调整与最终生成】-> 【RAG 的 G】：
#    模型收到报错后意识到无法访问网页正文，于是灵活调整策略，
#    基于第一步检索到的丰富摘要和参考链接，调用 `final_answer(...)` 生成最终的豪华派对策划案。
response = agent.run(prompt)

print("\n🎉 智能体最终输出的策划案:\n")
print(response)

