"""
本地小模型 (Ollama) + smolagents 实战测试脚本
- 解决云端模型审查/敏感词拦截痛点，实现 100% 本地免审查搜索
- 核心调优：通过 extra_body 限制上下文为 4096，防止默认 32k 导致 Ollama 内存溢出 panic (Error 500)
- 范式实践：使用 ToolCallingAgent 规避小模型在 CodeAgent 下的“单步抢跑”陷阱
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from smolagents import ToolCallingAgent, DuckDuckGoSearchTool, OpenAIServerModel

# 1. 连接本地运行的 1.5B 开源模型
# 关键设置：添加 extra_body 限制上下文为 4096，防止 32k 耗尽物理内存导致 Ollama 崩溃
model = OpenAIServerModel(
    model_id="qwen2.5-coder:1.5b",
    api_base="http://127.0.0.1:11434/v1",
    api_key="ollama",
    extra_body={"options": {"num_ctx": 4096, "num_batch": 256}},
)

# 2. 赋予特工网络搜索能力
# 小模型推荐使用 ToolCallingAgent（分步思维清晰，避免在 CodeAgent 中单步提前退出）
agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
    max_steps=3
)

# 3. 执行任务
task = "请使用 web_search 搜索最新的 AI 科技动态，并用中文简短总结核心要点。"
print(">>> [本地特工已就绪，正在自由探索世界...]\n")
agent.run(task)
