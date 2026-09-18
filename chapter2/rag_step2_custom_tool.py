import os
import sys
from dotenv import load_dotenv

# 确保 Windows 终端能正确打印多语言和特殊字符
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

# 引入官方教程所需的库
from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from smolagents import CodeAgent, OpenAIServerModel, Tool

# ==============================================================================
# 第一部分：定义私有文档（模拟韦恩庄园内部的派对策划档案库）
# ==============================================================================
party_ideas = [
    {
        "text": "A superhero-themed masquerade ball with luxury decor, including gold accents and velvet curtains.",
        "source": "Party Ideas 1",
    },
    {
        "text": "Hire a professional DJ who can play themed music for superheroes like Batman and Wonder Woman.",
        "source": "Entertainment Ideas",
    },
    {
        "text": "For catering, serve dishes named after superheroes, like 'The Hulk's Green Smoothie' and 'Iron Man's Power Steak.'",
        "source": "Catering Ideas",
    },
    {
        "text": "Decorate with iconic superhero logos and projections of Gotham and other superhero cities around the venue.",
        "source": "Decoration Ideas",
    },
    {
        "text": "Interactive experiences with VR where guests can engage in superhero simulations or compete in themed games.",
        "source": "Entertainment Ideas",
    },
]

# 将字典转为 LangChain 标准 Document 对象
source_docs = [
    Document(page_content=doc["text"], metadata={"source": doc["source"]})
    for doc in party_ideas
]

# ==============================================================================
# 第二部分：文档切块（Text Splitting / Chunking）
# 【为什么切块】：知识库文档往往很长，切成小块才能精准匹配关键词并节省上下文窗口
# ==============================================================================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    add_start_index=True,
    strip_whitespace=True,
    separators=["\n\n", "\n", ".", " ", ""],
)
docs_processed = text_splitter.split_documents(source_docs)

# ==============================================================================
# 第三部分：封装专属检索工具（Custom Retriever Tool）
# 【核心核心】：继承 smolagents.Tool，大模型通过 name、description 和 inputs 契约来调用它
# ==============================================================================
class PartyPlanningRetrieverTool(Tool):
    name = "party_planning_retriever"
    description = "Uses semantic search to retrieve relevant party planning ideas for Alfred’s superhero-themed party at Wayne Manor."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be a query related to party planning or superhero themes.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        # 初始化 BM25 检索器，设置每次检索最相关的 top-5 片段
        self.retriever = BM25Retriever.from_documents(docs, k=5)

    def forward(self, query: str) -> str:
        """模型在代码沙箱中调用此工具时，实际执行的方法"""
        assert isinstance(query, str), "Your search query must be a string"

        # 执行 BM25 检索
        docs = self.retriever.invoke(query)

        # 格式化输出为规范的字符串返回给智能体
        return "\nRetrieved ideas:\n" + "".join(
            [
                f"\n\n===== Idea {str(i)} =====\n" + doc.page_content
                for i, doc in enumerate(docs)
            ]
        )

# ==============================================================================
# 第四部分：实例化工具与 CodeAgent 智能体
# ==============================================================================
# 1. 实例化我们的自定义知识库检索工具
party_planning_retriever = PartyPlanningRetrieverTool(docs_processed)

# 2. 初始化大模型底座
model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
    flatten_messages_as_text=True,
)

# 3. 装配智能体：此时给智能体的工具不是盲目的 DuckDuckGo，而是我们专属打造的内部检索工具！
agent = CodeAgent(
    tools=[party_planning_retriever],
    model=model,
)

# 4. 运行官方评测任务
prompt = "Find ideas for a luxury superhero-themed party, including entertainment, catering, and decoration options."
print(f"👉 开始执行任务: {prompt}\n")

response = agent.run(prompt)

print("\n🎉 智能体最终输出的策划案:\n")
print(response)

