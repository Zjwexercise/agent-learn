import os
import sys
from dotenv import load_dotenv

# 确保 Windows 终端能正确打印多语言和特殊字符
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from smolagents import CodeAgent, OpenAIServerModel, Tool

# 1. 模拟知识库
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

source_docs = [
    Document(page_content=doc["text"], metadata={"source": doc["source"]})
    for doc in party_ideas
]

# 2. 文档切块
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    add_start_index=True,
    strip_whitespace=True,
    separators=["\n\n", "\n", ".", " ", ""],
)
docs_processed = text_splitter.split_documents(source_docs)

# ==============================================================================
# 修复核心：将工具的输出契约改为真正的 Python 列表 (list[str])
# ==============================================================================
class PartyPlanningRetrieverTool(Tool):
    name = "party_planning_retriever"
    # 在描述中明确告知大模型：返回的是一个字符串列表 (List of strings)
    description = "Uses semantic search to retrieve relevant party planning ideas for Alfred's party at Wayne Manor. Returns a list of strings, each string being a distinct idea."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be a query related to party planning or superhero themes.",
        }
    }
    # 修复点 1：output_type 改为 "any"，允许返回 Python 原生列表
    output_type = "any"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.retriever = BM25Retriever.from_documents(docs, k=5)

    def forward(self, query: str) -> list[str]:
        assert isinstance(query, str), "Your search query must be a string"
        docs = self.retriever.invoke(query)
        # 修复点 2：直接返回原生文档内容列表，而不是拼接成一整段容易引起下标误解的大字符串
        return [doc.page_content for doc in docs]

# 3. 实例化工具与模型
party_planning_retriever = PartyPlanningRetrieverTool(docs_processed)

model = OpenAIServerModel(
    model_id="glm-4-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
    flatten_messages_as_text=True,
)

agent = CodeAgent(
    tools=[party_planning_retriever],
    model=model,
)

prompt = "Find ideas for a luxury superhero-themed party, including entertainment, catering, and decoration options."
print(f"👉 开始执行任务: {prompt}\n")

response = agent.run(prompt)

print("\n🎉 智能体最终输出的策划案:\n")
print(response)

