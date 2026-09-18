# 📖 Unit 2: 知识检索与检索增强型智能体 (Retrieval Agents / Agentic RAG)

本目录为 Hugging Face 官方课程 **Unit 2** 的代码实践、避坑分析与架构演进记录。

重点探索：**当大模型面对海量开放网络信息或私有数据时，智能体如何自主规划检索、规避类型陷阱，并通过多智能体与 RAG（检索增强生成）协同完成高阶复杂任务**。

---

## 🗺️ 模块导航与学习笔记 (Notes & Deep Dives)

为了方便体系化学习与查阅，详细的原理解析、Mermaid 执行时序图和代码对比均已按模块归档至 `notes/` 目录：

| 模块序号 | 模块主题与文档 | 对应实践脚本 | 核心攻坚要点 |
| :--- | :--- | :--- | :--- |
| **模块一** | 📄 [**开放网络检索与智能体行为解剖**](notes/01_web_search_agent.md) | [`rag_step1_web.py`](rag_step1_web.py) | 剖析 17 步死磕复盘：Markdown 字符串误判、搜索 `#` 号荒诞自愈、print 与 final_answer 沙箱机制 |
| **模块二** | 📄 [**专属本地知识库构建与契约陷阱**](notes/02_custom_rag_tool.md) | [`rag_step2_custom_tool.py`](rag_step2_custom_tool.py)<br>[`rag_step2_fixed.py`](rag_step2_fixed.py) | BM25 检索工具封装；破解 `{'entertainment': 'R', 't', 'e'}` 字符串切片静默 Bug；规范 `list[str]` 契约 |
| **模块三** | 📄 [**多智能体协作系统与层级调度**](notes/03_multi_agent_system.md) | [`multi_agent_step1.py`](multi_agent_step1.py)<br>[`multi_agent_step1_fixed.py`](multi_agent_step1_fixed.py) | 揭示轻量模型在官方代码下的“车祸现场”；换用必应稳定搜索、焊死 `max_steps` 熔断线、强提示词注入 |
| **模块四** | 📄 [**终极架构：多智能体与私有 RAG 合体**](notes/04_multi_agent_rag.md) | [`multi_agent_step2_rag.py`](multi_agent_step2_rag.py) | 解决网络搜索噪声大痛点；构建企业级《蝙蝠侠》私有取景档案库；下属秒查坐标，经理秒算航程 |

---

## 🚀 脚本清单与运行指引 (Quick Start)

所有实践均遵循**保留原始探索，新解法独立成文件**的工程规范：

```bash
# 1. 体验官方第一步：网络搜索智能体（观察开放网络检索的不可控性）
python chapter2/rag_step1_web.py

# 2. 体验官方第二步：原生 BM25 工具（观察 'R','t','e' 字符串切片 Bug）
python chapter2/rag_step2_custom_tool.py

# 3. 运行修复版第二步：标准原生列表返回（体验结构化输出）
python chapter2/rag_step2_fixed.py

# 4. 体验官方多智能体：经理 + 搜索员（观察 20 步与死循环问题）
python chapter2/multi_agent_step1.py

# 5. 运行加固版多智能体：必应搜索 + 步数熔断（Token 节省 92%）
python chapter2/multi_agent_step1_fixed.py

# 6. 运行终极合体版：多智能体 + 私有 RAG 档案库（5 秒精准交付决策）
python chapter2/multi_agent_step2_rag.py
```

---

## 📊 演进路线全景总览 (Evolution Roadmap)

| 演进阶段 | 代码文件 | 核心技术 / 解决痛点 | 典型表现 |
| :--- | :--- | :--- | :--- |
| **阶段 1：开放搜索 RAG** | [`rag_step1_web.py`](rag_step1_web.py) | DuckDuckGo 单智能体搜索 | 17 步死磕、把字符串当字典、搜 `#` 号维基百科 |
| **阶段 2：专属本地 RAG** | [`rag_step2_custom_tool.py`](rag_step2_custom_tool.py) | BM25 检索器封装 | 触发切片静默 Bug：`{'entertainment': 'R', 'catering': 't', 'decoration': 'e'}` |
| **阶段 3：结构化契约修复** | [`rag_step2_fixed.py`](rag_step2_fixed.py) | `output_type="any"` 返回 `list[str]` | 2 步利落完成，输出完整段落内容，彻底根治单字 Bug |
| **阶段 4：原生多智能体** | [`multi_agent_step1.py`](multi_agent_step1.py) | `managed_agents` 层级调度 | 官方作者靠顶级模型掩盖缺陷；小模型下属打满20步，经理连续print死循环12次 |
| **阶段 5：工程化加固** | [`multi_agent_step1_fixed.py`](multi_agent_step1_fixed.py) | Bing 搜索 + `max_steps` 熔断 + 强约束提示 | 阻断死循环，自愈容错，Token 消耗暴降 92% |
| **阶段 6：终极合体** | [`multi_agent_step2_rag.py`](multi_agent_step2_rag.py) | **Multi-Agent + 私有 RAG 档案库** | 下属 5 秒精准命中档案坐标，经理秒算航程呈送阿福，架构彻底稳健！ |

---

## 💡 核心工程避坑铁律 (Key Takeaways)

1. **给 CodeAgent 写的工具必须“言行一致”**：能返回列表/字典等原生对象就绝不返回假装成列表的长字符串。
2. **所有生产 Agent 必须焊死熔断器**：严格配置 `max_steps`，防止模型在沙箱中死循环并疯狂消耗 Token。
3. **私有 RAG 优于嘈杂 Web**：对于关键业务与精准参数（如经纬度、配置项），通过切块与索引接入私有知识库，效率与稳定性远超开放搜索引擎。
