# 模块三：多智能体协作系统与层级调度

[← 返回 Chapter 2 目录](../README.md)

---

## 任务背景
当复杂任务需要兼顾“开放信息检索”与“专业数学测算”时，单智能体会面临上下文过载的问题。
官方教程引入了 **多智能体层级架构（Manager-Subordinate Architecture）**：
- 官方原版脚本：[`multi_agent_step1.py`](../multi_agent_step1.py)
- 工业级加固脚本：[`multi_agent_step1_fixed.py`](../multi_agent_step1_fixed.py)

---

## 1. 机制解剖：把 Agent 当作 Tool 来管

在 `smolagents` 中，经理通过 `managed_agents=[web_agent]` 注册下属：
- 下属专员独立处理子任务，维护独立的上下文记忆空间；
- 处理完毕后，仅把最终结构化结论上报给主管经理；
- 主管经理的上下文大幅精简，专注于高阶逻辑规划与工具调用。

---

## 2. 原版代码在轻量模型上的“车祸现场”

在官方原版设置下，当脱离了顶级模型（如 DeepSeek-R1 671B）的光环，在常规商业模型（GLM-4-Flash）上出现了极度混乱的失控现象：
1. **下属死磕 20 步**：搜不到具体建筑的经纬度数字，盲目使用正则和不存在的 `geocode` 工具，打满 20 步强制退出；
2. **经理角色混乱**：试图调用下属的 `web_search` 被沙箱拦截；放着现成的 `@tool calculate_cargo_travel_time` 不用，自己手搓数学公式还漏了 `import math`；
3. **中文语法错误与死循环**：在 Python 沙箱中执行中文 `报告：` 抛出 `SyntaxError: invalid character '：'`；连续 12 步重复执行 `print(report)` 而不调用 `final_answer`，整整烧了 **20.4 万 Token**！

---

## 3. 关键代码改动对比 (`multi_agent_step1.py` vs `multi_agent_step1_fixed.py`)

#### 改动点 A：换用国内畅通稳定的必应搜索工具 (`BingSearchTool`)
解决海外 DuckDuckGo 频繁 `TimeoutException` 的网络痛点。

* **原版写法 (`multi_agent_step1.py`)**：
  ```python
  from smolagents import DuckDuckGoSearchTool
  # 直接使用海外 DuckDuckGo，无代理环境下极易超时或被封
  web_agent = CodeAgent(
      model=model,
      tools=[DuckDuckGoSearchTool()],
      name="web_search_agent",
      description="专职调研员：负责在互联网上搜索准确的地理位置、历史信息及取景地数据。",
  )
  ```

* **修复写法 (`multi_agent_step1_fixed.py`)**：
  ```python
  import urllib.request, urllib.parse
  from bs4 import BeautifulSoup
  from smolagents import Tool

  # 自定义国内必应搜索工具，稳定无阻，带异常捕获
  class BingSearchTool(Tool):
      name = "web_search"
      description = "在必应 (Bing) 上检索全球地理位置、电影取景地及经纬度坐标。"
      inputs = {"query": {"type": "string", "description": "要搜索的关键词或地点名"}}
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
  ```

---

#### 改动点 B：焊死步数熔断保护 (`max_steps`)
官方默认不限步数（默认上限 20 步），在常规模型死磕时会烧光 Token。

* **原版写法 (`multi_agent_step1.py`)**：
  ```python
  # 没有任何 step 限制，下属盲搜打满 20 步，经理在沙箱死循环 print 12 步！
  web_agent = CodeAgent(model=model, tools=[DuckDuckGoSearchTool()], ...)
  manager_agent = CodeAgent(model=model, tools=[calculate_cargo_travel_time], managed_agents=[web_agent])
  ```

* **修复写法 (`multi_agent_step1_fixed.py`)**：
  ```python
  # 下属设为最多 4 步，经理设为最多 5 步，彻底消灭 20 步死磕与 20 万 Token 浪费
  web_agent = CodeAgent(
      model=model,
      tools=[BingSearchTool()],
      name="web_search_agent",
      description="专职搜索员：负责快速搜索现实中的城市或著名建筑的大致经纬度坐标 (纬度, 经度)。",
      max_steps=4,  # 🔴 核心熔断线：下属最多 4 步
  )

  manager_agent = CodeAgent(
      model=model,
      tools=[calculate_cargo_travel_time],
      managed_agents=[web_agent],
      max_steps=5,  # 🔴 核心熔断线：经理最多 5 步
  )
  ```

---

#### 改动点 C：强提示词注入（封死语法错误与自作聪明）

* **原版任务提示 (`multi_agent_step1.py`)**：
  ```python
  task = """
  阿福需要找回蝙蝠车。请完成以下两步：
  1. 派你的调研员找出 2 个著名的《蝙蝠侠》电影取景地（包含经纬度坐标）；
  2. 使用你的测算工具，计算将道具从这些地点用货机运回哥谭市（纬度 40.7128, 经度 -74.0060）各自需要飞行多少小时。
  最后汇总成清晰的报告返回。
  """
  ```

* **修复任务提示 (`multi_agent_step1_fixed.py`)**：
  ```python
  # 明确契约：强制调用 calculate_cargo_travel_time、严禁手搓公式、强制 final_answer 提交
  task = """
  阿福需要找回失踪的蝙蝠车。请严格按照以下两步执行：
  步骤 1：直接调用你的下属 `web_search_agent` 查询 2 个《蝙蝠侠》电影取景城市的大致经纬度（例如芝加哥或伦敦等城市的经纬度元组）。
  步骤 2：拿到经纬度后，直接调用你手上的工具 `calculate_cargo_travel_time` 计算运回哥谭市（40.7128, -74.0060）所需的飞行时间。严禁自己手写数学公式！
  完成计算后，请直接调用 `final_answer("...")` 返回最终报告，严禁只使用 print。
  """
  ```

---

## 4. 优化成果数据对比

| 性能指标 | 原版裸奔运行 (`multi_agent_step1.py`) | 工业级防护版 (`multi_agent_step1_fixed.py`) |
| :--- | :--- | :--- |
| **下属步数** | 20 步（超时打满） | 4 步（及时熔断收敛） |
| **经理步数** | 21 步（死循环打满） | **第 5 步优雅完赛** |
| **Token 消耗** | **204,536 Tokens** | **16,281 Tokens**（节省 92%！） |
| **最终输出** | 错误代码交织的混杂文本 | 干净精确的航程报告（伦敦 9.17 小时，芝加哥 2.68 小时） |
