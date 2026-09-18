# 模块二：专属本地知识库构建与契约陷阱

[← 返回 Chapter 2 目录](../README.md)

---

## 任务背景
为了解决开放网络检索脏、乱、慢且容易陷入死循环的痛点，官方教程引入了**私有知识库检索工具**。
- 官方原版脚本：[`rag_step2_custom_tool.py`](../rag_step2_custom_tool.py)
- 工业级修复脚本：[`rag_step2_fixed.py`](../rag_step2_fixed.py)

技术栈：LangChain `Document` + `RecursiveCharacterTextSplitter` + `BM25Retriever` + smolagents `Tool`。

---

## 1. 官方原版代码的隐蔽 Bug：`{'entertainment': 'R', 'catering': 't', 'decoration': 'e'}`

在官方原版 `rag_step2_custom_tool.py` 中，工具实现如下：
```python
output_type = "string"
return "\nRetrieved ideas:\n" + "".join(
    [f"\n\n===== Idea {str(i)} =====\n" + doc.page_content for i, doc in enumerate(docs)]
)
```

### 崩溃现象：
大模型在 Step 1 看到日志里有 `===== Idea 0 =====`, `===== Idea 1 =====` 等编号。
在 Step 2，大模型自作聪明写出切片代码：
```python
entertainment_ideas = luxury_superhero_ideas[1]  # 本意：提取 Idea 1
catering_ideas = luxury_superhero_ideas[3]       # 本意：提取 Idea 3
decoration_ideas = luxury_superhero_ideas[2]     # 本意：提取 Idea 2
```
**结果**：`luxury_superhero_ideas` 是个纯字符串 `\nRetrieved ideas:\n...`。
- `[1]` 取到了字符串下标 1 的字符 **`'R'`**
- `[2]` 取到了字符串下标 2 的字符 **`'e'`**
- `[3]` 取到了字符串下标 3 的字符 **`'t'`**
（刚好是单词 **`Retrieved`** 的前三个字符！）

因为 Python 语法允许对字符串切片，程序没有任何报错，大模型以为自己圆满完成任务，直接提交了荒诞的答案：
```python
{'entertainment': 'R', 'catering': 't', 'decoration': 'e'}
```

---

## 2. 根治方案：工业级结构化契约 (`rag_step2_fixed.py`)

解决的核心在于**“知行合一”**：既然大模型在写 Python 代码时倾向于按项（Index）读取数据，就应该直接给它真正的结构化列表，而不是伪装成带编号的字符串。

```python
class PartyPlanningRetrieverTool(Tool):
    name = "party_planning_retriever"
    # 明确在契约中说明：返回的是字符串列表
    description = (
        "Uses semantic search to retrieve party ideas. "
        "Returns a list of strings, each string being a distinct idea."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform.",
        }
    }
    # 核心修复 1：output_type 改为 "any"，支持原生 Python 对象
    output_type = "any"

    def forward(self, query: str) -> list[str]:
        docs = self.retriever.invoke(query)
        # 核心修复 2：直接返回原生文档内容列表
        return [doc.page_content for doc in docs]
```

### 修复后的效果验证：
模型在调用后，拿到的是真正的 `list[str]`，输出的策划案完整包含了：
- `entertainment`: `['A superhero-themed masquerade ball...', 'Interactive experiences with VR...', ...]`
- `catering`: `['For catering, serve dishes named after superheroes, like Hulk Smoothie...']`
- `decoration`: `['Decorate with iconic superhero logos and projections of Gotham...']`
彻底消除了 `'R', 't', 'e'` 的切片静默 Bug！

---

## 3. 新手血泪复盘：同一段官方代码跑三次出三种花样？

> **“新手灵魂拷问”**：
> 我明明一字不差照抄 Hugging Face 官方教程，为什么第一遍秒过，第二遍返回单字 `'R','t','e'`，第三遍死磕 16 步当复读机狂烧 6.8 万 Token？

| 实验阶段 | 智能体行为 | 输出结果 | 本质原因 |
| :--- | :--- | :--- | :--- |
| **第 1 次运行** | 碰巧灵光一闪，分三次查不同主题 | 完美生成策划案（1步完成） | 大模型采样的“理想路径 (Happy Path)”，录教程时的偶发运气 |
| **第 2 次运行** | 以为字符串有编号就是列表，用 `[1],[2]` 切片 | `{'entertainment': 'R', ...}` | **视觉欺骗 + 静默失败**：Python 允许 `str[1]` 取单个字符，程序不报错但逻辑全废 |
| **第 3 次运行** | 不满意当前结果，死磕换词搜“表演者”10次 | 16步、烧6.8万Token、4倍复读机 | **知识库太小 + 字符串相加**：知识库只有5条，模型疯狂重构查询撞墙，最后用 `+` 拼成了4倍长文本 |

### 官方教程为什么没发现？
1. **测试覆盖不足**：只要看到控制台没报红、任务退出了，作者就截图交差，没有在多个开源/常规模型上进行长效回归测试；
2. **Demo 代码去掉了防具**：为了代码简短好看，官方砍掉了返回类型约束、防死循环熔断和知识库边界校验；
3. **传统习惯撞上 CodeAgent**：LangChain 时代大家都习惯返回纯文本大字符串，但现代 `CodeAgent` 是会写 Python 代码的！把弱类型文本塞给爱写代码的智能体，必然导致灾难。

### 给新手的 3 条铁律：
1. **永远不要原封不动把教程代码直接搬进生产环境**；
2. **给 CodeAgent 写的工具必须“言行一致”**：能返回列表/字典就绝不返回假装成列表的长字符串；
3. **给检索工具加边界保护**：检索结果为空或知识库耗尽时，必须明确反馈“无更多结果”，防止智能体化身永动机。
