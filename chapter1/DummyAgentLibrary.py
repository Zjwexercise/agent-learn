import os
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# Load environment variables from .env file
load_dotenv()

# This system prompt is a bit more complex and actually contains the function description already appended.
# Here we suppose that the textual description of the tools has already been appended.

SYSTEM_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

get_weather: Get the current weather in a given location

The way you use the tools is by specifying a json blob.
Specifically, this json should have an `action` key (with the name of the tool to use) and an `action_input` key (with the input to the tool going here).

The only values that should be in the "action" field are:
get_weather: Get the current weather in a given location, args: {"location": {"type": "string"}}
example use :

{{
  "action": "get_weather",
  "action_input": {"location": "New York"}
}}


ALWAYS use the following format:

Question: the input question you must answer
Thought: you should always think about one action to take. Only one action at a time in this format:
Action:

$JSON_BLOB (inside markdown cell)

Observation: the result of the action. This Observation is unique, complete, and the source of truth.
(this Thought/Action/Observation can repeat N times, you should take several steps when needed. The $JSON_BLOB must be formatted as markdown and only use a SINGLE action at a time.)

You must always end your output with the following format:

Thought: I now know the final answer
Final Answer: the final answer to the original input question

Now begin! Reminder to ALWAYS use the exact characters `Final Answer:` when you provide a definitive answer. """



# 1. Initialize Zhipu AI Client from environment (.env)
API_KEY = os.environ.get("ZHIPUAI_API_KEY")
if not API_KEY:
    raise ValueError("未检测到 ZHIPUAI_API_KEY，请检查项目根目录的 .env 文件配置！")

client = ZhipuAI(api_key=API_KEY)

# Use glm-4-flash (fast and free/inexpensive) or glm-4 / glm-4-plus
MODEL_NAME = "glm-4-flash"


output = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {"role": "user", "content": "The capital of china is"},
    ],
    stream=False,
    max_tokens=1024,
)
print(output.choices[0].message.content)

# ==========================================
# 阶段 1：没有 stop 参数 —— 观察模型的自导自演与幻觉
# ==========================================
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "What's the weather in London?"},
]

print("=" * 60)
print("【阶段 1：未加 stop】模型尝试自己编造 Observation 和答案：")
print("=" * 60)

output1 = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages,
    stream=False,
    max_tokens=200,
)
print(output1.choices[0].message.content)


# ==========================================
# 阶段 2：加上 stop 参数 —— 成功截断，强行阻止模型瞎编
# ==========================================
print("\n" + "=" * 60)
print("【阶段 2：加了 stop】模型在准备执行 Action 时被强行刹车：")
print("=" * 60)

output2 = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages,
    stop=["Observation:"],  # 遇到 Observation: 立即停止生成
    stream=False,
    max_tokens=200,
)
step2_content = output2.choices[0].message.content.strip()
print(step2_content)


# ==========================================
# 阶段 3：执行真正的 Python 函数，闭环生成 Final Answer（你之前漏掉的部分）
# ==========================================
print("\n" + "=" * 60)
print("【阶段 3：真实函数介入】将真实工具返回的结果喂回给模型：")
print("=" * 60)

# 定义真实/模拟工具
def get_weather(location):
    return f"the weather in {location} is sunny with low temperatures (15°C).\n"

# 1. 真实运行 Python 函数
real_observation = get_weather("London")
print(f"-> 真实 Python 函数执行结果: {real_observation.strip()}")


# 2. 确保拼接格式完整（包含 Observation:）
if not step2_content.endswith("Observation:"):
    assistant_reply = step2_content + "\nObservation: " + real_observation
else:
    assistant_reply = step2_content + " " + real_observation

# 3. 将包含真实 Observation 的对话历史重新喂给模型
messages_final = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "What's the weather in London?"},
    {"role": "assistant", "content": assistant_reply},
]

output3 = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages_final,
    stream=False,
    max_tokens=200,
)

print("\n-> 模型基于真实数据的最终回答：")
print(output3.choices[0].message.content)