---
title: First Agent Template
emoji: ⚡
colorFrom: pink
colorTo: yellow
sdk: gradio
sdk_version: 5.23.1
app_file: app.py
pinned: false
tags:
- smolagents
- agent
- smolagent
- tool
- agent-course
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# 🤖 First Agent Template (Hugging Face Agents Course Unit 1)

本项目克隆自 Hugging Face 官方课程空间：[agents-course/First_agent_template](https://huggingface.co/spaces/agents-course/First_agent_template)，并结合国内开发环境与现代 `smolagents` 特性进行了全面优化与功能拓展。

## 🌟 主要改动与新增特性

1. **模型引擎升级 (Zhipu GLM-4)**：
   - 官方模板默认使用 `HfApiModel`，在公网容易过载且响应较慢；
   - 本项目通过 `OpenAIServerModel` 接入智谱清言 `glm-4-flash` 大模型，推理速度快且调用稳定；
   - 启用 `flatten_messages_as_text=True`，彻底解决复杂 JSON 结构导致的问题与回答不匹配现象；
   - 密钥统一存放在根目录 `.env` 文件（不提交到 Git，防止泄漏）。

2. **工具箱极大丰富 (Extensive Tools)**：
   - `final_answer`：官方必备的总结与最终输出工具；
   - `get_current_time_in_timezone`：时区与时间查询工具（支持全球主要城市名映射）；
   - `get_weather`：城市实时天气与体感查询工具；
   - `calculator`：高精度数学表达式安全计算器；
   - `DuckDuckGoSearchTool` (`web_search`)：公网实时搜索；
   - `VisitWebpageTool` (`visit_webpage`)：网页内容抓取与阅读；
   - `my_custom_tool`：文本统计与结构特征分析工具。

3. **Gradio 6 前端兼容性修复**：
   - 修复了在新版 Gradio 下 `Chatbot.__init__() got an unexpected keyword argument 'type'` 异常；
   - 本地运行时默认 `share=False`，防止公网隧道下载超时卡顿。

4. **双运行模式**：
   - **Web 图形界面**：`python app.py`
   - **CLI 命令行模式**：`python app.py --cli`

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
在项目根目录 `.env` 中填入：
```bash
ZHIPUAI_API_KEY="your_api_key_here"
```

### 3. 运行测试
- 命令行测试：
  ```bash
  python app.py --cli
  ```
- 启动浏览器 Web UI：
  ```bash
  python app.py
  ```
