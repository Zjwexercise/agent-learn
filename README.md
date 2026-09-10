# 🤖 Agent-Learn: AI 智能体学习与实践

本项目用于系统记录学习 [Hugging Face 官方 AI Agent 课程](https://huggingface.co/learn/agents-course) 全流程的代码实现、对比实验与核心原理。

* **课程来源**：[Hugging Face - Agents Course](https://huggingface.co/learn/agents-course)
* **大模型底座**：智谱 AI (GLM-4 / GLM-4-Flash) · 本地 Ollama (Qwen2.5-Coder)
* **技术栈**：Python 3.10+ · smolagents · Gradio · ZhipuAI · Ollama
* **开发者**：Zjwexercise

---

## 🗺️ 课程章节导航 (Course Roadmap)

每个章节的**详细教学、原理解析与深度避坑指南**均独立归档在对应目录下：

| 章节目录 | 课题内容 | 核心技术与产出 | 状态 |
| :--- | :--- | :--- | :--- |
| 📖 [**`chapter1/`**](chapter1/README.md) | **Unit 1: 智能体基础与工具初识** | 手搓白盒 ReAct 闭环、CodeAgent 范式、Space 模板工程化、7 大工具拓展及本地模型 (Ollama) 实战与排错 | ✅ 已完成 |
| ⏳ **`chapter2/`** | **Unit 2: 框架深入与高级工具** | 后续进阶课程内容 | 📅 学习中... |

---

## 📋 学习日志速览 (Daily Log / TL;DR)

> **2026-09-10 学习纪要 (本地模型攻坚与智能体范式对比)**
> - **背景痛点**：突破云端商业模型安全审查与敏感词拦截限制，探索 100% 本地隐私与免审查智能体闭环。
> - **排错攻坚**：
>   1. **Ollama 500 崩溃**：解决小内存机器下 32k 上下文导致 llama-runner 内存分配失败（`failed to allocate compute pp buffers`），通过 `extra_body` 裁剪上下文至 4096 完美修复。
>   2. **终端编码修复**：解决 Windows 控制台打印多语言搜索内容时的 `UnicodeEncodeError: 'gbk'` 崩溃。
> - **原理解析**：深入对比 `CodeAgent` 与 `ToolCallingAgent`。揭示小模型（1.5B 级别）在生成代码时无法预知变量结果而容易“单步抢跑”提早退出，采用 `ToolCallingAgent` 实现严格分步思考与真实内容总结。
> **2026-09-10 学习纪要 (本地模型攻坚 + LLM 解码策略可视化探秘)**
> - **模块一：本地模型与智能体范式 (Ollama 实战)**：
>   - 突破商业模型安全审查限制，解决 Ollama 32k 上下文导致的 500 内存溢出（`failed to allocate compute pp buffers`），裁剪至 4096 恢复稳定。
>   - 深入对比 `CodeAgent` 与 `ToolCallingAgent`：揭示 1.5B 小模型在代码生成时的“单步抢跑”问题，验证 `ToolCallingAgent` 的强鲁棒性。
> - **模块二：大模型解码策略探秘 (Decoding & Beam Search)**：
>   - 搭建专用的 HTML 决策树渲染模块 [`visualize_helper.py`](chapter1/Decoding/visualize_helper.py)，将 Gradio 树状数据转化为直观漂亮的浏览器可视化页面。
>   - 实验对比 **Greedy Search（贪心搜索）** 与 **Beam Search（束搜索）**，理清 `number_steps`、`number_beams`、`length_penalty`、`num_return_sequences` 四大核心参数。
>   - 挖掘底层模型差异：破案 GPT-2 原始基座模型无对齐导致的“复读机”概率陷阱，观察标点与 `<|endoftext|>` 终止符，深刻理解 Token 运作本质。
> **2026-09-10 学习纪要 (本地模型攻坚 + 解码策略探秘)**
> - **🎯 学习目标**：突破商业模型审查与内存限制实现本地化；探索 LLM 逐词解码与束搜索机制。
> - **🔨 做了什么**：
>   1. 调优 Ollama 上下文从 32k 至 4096，排查并修复 Windows GBK 终端乱码；
>   2. 对比 `CodeAgent` 与 `ToolCallingAgent` 范式，验证小模型防抢跑机制；
>   3. 接入 HF 官方 Decoding Space，运行并对比 Greedy 与 Beam Search 决策树，排查 GPT-2 复读成因。
> - **➕ 添加了什么**：
>   1. [`test.py`](test.py)：本地 Ollama + ToolCallingAgent 独立免审查测试脚本；
>   2. [`chapter1/Decoding/`](chapter1/Decoding/)：解码策略模块（含 3 套测试脚本、HTML 决策树渲染器与可视化网页）。
> - **✏️ 改了什么**：
>   1. 工具模块 `tools/web_search.py` 增强输入格式解析与鲁棒性；
>   2. 纠正 Decoding 脚本接口调用，由文本输出重构为浏览器交互网页。
> *(注：具体技术原理解析与详细避坑心得，见各子目录 README 说明文档)*

> **2026-09-09 学习纪要 (Unit 1)**
> - **核心概念**：掌握 ReAct 机制底层闭环（Stop 截断防幻觉），理解工业级框架 `smolagents` 对循环的内化封装及 `CodeAgent`（代码块作为 Action）的效率跃迁。
> - **代码实践**：手写实现白盒 Dummy Agent；克隆并复现 Hugging Face 官方 `First_agent_template` 智能体。
> - **排错攻坚**：定位并解决 Prompt 样例污染（输入展平 `flatten_messages_as_text=True`）、Gradio 6 `type` 参数失效、官方 Space `visit_webpage.py` 遗漏 `import re` 等问题。
> - **功能交付**：交付支持 Gradio Web 网页端与 CLI 命令行双模式的完整智能体，装配天气、高精度计算器、时区、搜索等 7 项工具。

---

## 📂 项目全局结构

```text
agent-learn/
├── .env.example                       # 环境变量模板 (安全隔离 API 密钥)
├── .gitignore                         # 严格过滤 .env 与 .venv
├── README.md                          # 仓库全局索引与速览日志
├── test.py                            # 本地开源模型 (Ollama) 实战测试脚本
└── chapter1/                          # 📖 Unit 1 完整实践 (详见 chapter1/README.md)
    ├── README.md                      # Unit 1 完整教程与详细原理解析
    ├── dummy_agent/                   # 模块一：手搓基础智能体 (单文件独立运行)
    │   └── DummyAgentLibrary.py
    └── First_agent_template/          # 模块二：官方 Space 模板智能体 (多工具+Web UI)
        ├── app.py
        ├── Gradio_UI.py
        ├── prompts.yaml
        ├── requirements.txt
        └── tools/
```

---

## 🚀 全局快速开始

1. **准备 Python 虚拟环境**：
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r chapter1/First_agent_template/requirements.txt
   ```

2. **配置环境变量**：
   复制 `.env.example` 为 `.env` 并填入智谱 API 密钥：
   ```bash
   ZHIPUAI_API_KEY="your_zhipuai_api_key"
   ```

3. **查看章节详细指导**：
   👉 [**前往 Chapter 1 详细教程与操作指引**](chapter1/README.md)
