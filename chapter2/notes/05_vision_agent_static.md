# 模块五：静态视觉智能体 (Vision Agent)

[← 返回 Chapter 2 目录](../README.md)

---

## 核心实现 ([vision_step1_static.py](../vision_step1_static.py))

本节让智能体具备视觉理解能力：给它一张监控抓拍图片，让其自主观察人物发色、妆容与服饰，识破伪装身份。
本节让智能体具备视觉理解能力：给它一张监控抓拍图片，让其直接观察人物发色、妆容与服饰特征，识破访客身份。

```python
# 1. 载入图像（必须加合规 User-Agent 避免 429 拦截）
headers = {"User-Agent": "SecurityBot/1.0 (contact: admin@test.com)"}
resp = requests.get(image_url, headers=headers, timeout=10)
img = Image.open(BytesIO(resp.content)).convert("RGB")
代码主体其实只有四步：用 requests 加上合规 User-Agent 下载图片；底座换上多模态模型 glm-4v-flash；初始化一个不带任何工具的 CodeAgent；最后调用 agent.run(..., images=[img]) 传入图片执行。

# 2. 选用多模态模型（注意：绝不能加 flatten_messages_as_text=True）
model = OpenAIServerModel(
    model_id="glm-4v-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
)
---

# 3. 构建智能体（tools 为空，视觉能力完全内生）
agent = CodeAgent(tools=[], model=model, max_steps=5)
## 关键认知：它凭什么不用工具就能看图？

# 4. 传入图片，执行任务
response = agent.run("观察图像特征，判断是 The Joker 还是 Wonder Woman", images=[img])
```
刚写这段代码时最反直觉的一点是：CodeAgent(tools=[]) 里的工具列表是空的。

之前查天气要写工具，算航程要写工具，但这次看图却一个工具都没传。原因在于这代多模态模型（VLM）本身长了眼睛——图片在预训练阶段就已经作为视觉 Token 融入了神经网络。它和早年“纯文本模型 + 外部 OCR / YOLO 识别工具”的拼装方案完全不同，识图是大模型出厂自带的内生能力，不需要给它挂外部拐杖。

那 smolagents 到底帮我们做了什么？主要是抹平了协议转换的麻烦。我们在本地随手传的是一个 PIL.Image 对象，框架在底层自动帮我们转成了 Base64 编码，并打包成大模型接口规范的 JSON 载荷；更重要的是，框架把图片存进了智能体的初始记忆节点（TaskStep），这样即使智能体在沙箱里思考或者重试多步，这张底图也始终都在上下文里，不会走两步就丢失。

---

## 核心技术点解析
## 实操排错备忘

### 1. 为什么 `tools=[]` 是空的却能识图？（内生视觉 vs 外挂 Tool）
* **传统做法（外挂 Tool）**：大模型本身是纯文本“瞎子”，必须挂载外部 OCR 或物体检测工具（写代码调用 YOLO/OpenCV），读出文字标签后再推理。
* **现代做法（VLM 内生多模态）**：`glm-4v-flash` 在训练时神经网络就直接吃进图像像素（Vision Tokens）。**识图是大模型脑子自带的本能，不是外挂技能**，因此不需要任何 Tool。
今天调试时踩了三个很典型的坑：

### 2. `agent.run(task, images=[img])` 底层做了什么？
用户传的是本地 `PIL.Image` 对象，而云端 API 只认网络 JSON。`smolagents` 在幕后做了两件事：
1. **自动序列化**：在 `utils.py` 里自动将 PIL 图像转为 PNG 字节流，并编码为 `data:image/png;base64,...` 标准格式。
2. **锁入持久记忆**：写入 `memory.py` 的 `TaskStep` 中。在智能体多步 ReAct 循环中，无论经过多少轮推理，底图都始终保持在上下文中，不会丢图。
一是配置模型时千万别写 flatten_messages_as_text=True。前几章为了纯文本防污染加了这个参数，但多模态请求必须传递包含图片对象的结构化消息体，一旦强行展平为纯文本，底层会直接抛 AssertionError 崩溃。

---
二是维基百科的图片下载有反爬限制，如果不带请求头直接 get 会返回 429 拒收，必须在 headers 显式补一个自定义的 User-Agent。

## 三大工程踩坑与避坑

| 踩坑现象 | 本质原因 | 极简解法 |
| :--- | :--- | :--- |
| **`AssertionError` 断言崩溃** | 之前为了纯文本加了 `flatten_messages_as_text=True`，底层无法将图片硬压为文本。 | **传图片时必须去掉该参数**，保留原生多模态消息体。 |
| **维基百科 `429 / 403` 拦截** | 没带身份标识的空请求直接被反爬 WAF 拒收。 | `requests.get` 请求头显式加上合规的 `User-Agent`。 |
| **`1210: 输入图片数量超过限制`** | 视觉模型看图容易用自然语言散聊，漏写 `<code>` 导致沙箱报错重试；反复重发图片撑爆了单次上限。 | **Prompt 强约束**：显式要求“必须用 `<code>` 和 `</code>` 包裹 Python 代码”。 |
三是多模态模型在看到图片后容易直接用大白话聊天，忘了用 <code> 包裹 Python 代码，导致沙箱报错并自动重试。多轮重试会把图片反复重复发送，很快就会触发接口的“图片数量超限（1210）”报错。只要在任务提示词里硬性加上一句“代码必须写在 <code> 标签内”，模型第一步就会老老实实写出规范代码直接收敛。
