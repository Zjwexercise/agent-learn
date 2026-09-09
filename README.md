# 🤖 Agent-Learn: AI 智能体学习与实践

本项目用于系统记录学习 Hugging Face 官方 AI Agent 课程全流程的代码实现、对比实验与核心原理。

* **官方课程链接**：[Hugging Face - Agents Course (Unit 1: Dummy Agent Library)](https://huggingface.co/learn/agents-course/unit1/dummy-agent-library)
* **大模型驱动**：智谱 AI (GLM-4 / GLM-4-Flash)
* **开发者**：Zjwexercise

---

## 📅 2026-09-09 学习日志：Unit 1 - 手搓基础智能体 (Dummy Agent)

### 1. 核心原理：ReAct 循环机制 (Reason + Act)
AI Agent 与普通问答机器人的本质差异在于：模型不仅仅输出文本，还具备**自主思考、调用外部环境工具、观测反馈并得出结论**的闭环能力。

```text
用户提问 
  └─► 1. Thought (思考)       : 模型分析需求，决定调用工具
        └─► 2. Action (行动)        : 模型输出标准 JSON 指令
              └─► 🛑 触发 stop 截断 : 强制拦截模型生成，防止凭空捏造数据
                    └─► 3. Tool Exec (执行)   : 本地 Python 运行真实业务函数
                          └─► 4. Observation (观察) : 将真实数据回填上下文
                                └─► 5. Final Answer (结论) : 模型依据事实产出最终回答
```

---

### 2. 关键对比实验现象剖析

在 [`chapter1/DummyAgentLibrary.py`](chapter1/DummyAgentLibrary.py) 中，我们对比了 3 种不同阶段的输出差异：

| 实验阶段 | 关键代码设计 | 输出表现 | 本质原因 |
| :--- | :--- | :--- | :--- |
| **阶段 1：未加 Stop** | 无 `stop` 参数 | 模型自导自演编造了 `Observation` 和答案 | 模型是概率预测文本，未受外界物理阻断前会持续“幻想”后续对话 |
| **阶段 2：加了 Stop** | `stop=["Observation:"]` | 模型在输出 `Action` 后立即刹车并暂停 | 大模型推理引擎遇到停用词立即停止解码，将控制权让渡给宿主程序 |
| **阶段 3：真实闭环** | 运行本地函数并回填 `Observation` | 模型获得真实观测结果，输出精准的 `Final Answer` | **ReAct 范式闭环完成**，模型基于确定性外部事实推理出最终结论 |

---

### 3. 工程规范与安全实践
1. **环境变量管理**：敏感 API Key 移入根目录下的 `.env` 文件，并通过 `.gitignore` 彻底与代码仓库隔离。提供 `.env.example` 作为团队配置模板。
2. **虚拟环境隔离**：在项目根目录设立独立的 `.venv` 环境，避免全局安装依赖造成版本混乱（Dependency Hell）。
3. **网络与代理配置**：排查本地代理端口（如 7897）与国内镜像源握手失败（Error 10054）的场景，规范使用官方源与代理分流策略。

---

## 📂 项目结构
```text
agent-learn/
├── .venv/                      # 项目专属 Python 虚拟环境 (git ignored)
├── chapter1/
│   └── DummyAgentLibrary.py   # 第一章：手搓 Dummy Agent 完整对比实现
├── .env.example               # 环境变量配置模板
├── .gitignore                 # Git 忽略配置规则 (保护 .env 和 .venv)
└── README.md                  # 学习日志与项目索引
```

---

## 🚀 快速开始

1. 克隆仓库：
   ```bash
   git clone https://github.com/Zjwexercise/agent-learn.git
   cd agent-learn
   ```
2. 创建并激活虚拟环境：
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. 安装依赖：
   ```bash
   pip install zhipuai python-dotenv
   ```
4. 配置密钥：
   - 复制 `.env.example` 为 `.env`
   - 在 `.env` 中填入你的智谱 API Key
5. 运行第一章实验：
   ```bash
   python .\chapter1\DummyAgentLibrary.py
   ```
