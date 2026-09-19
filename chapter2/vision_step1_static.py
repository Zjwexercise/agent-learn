import os
import sys
from io import BytesIO
from PIL import Image
import requests
from dotenv import load_dotenv

# 确保 Windows 终端能正确打印多语言与特殊字符
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from smolagents import CodeAgent, OpenAIServerModel

# ==============================================================================
# 1. 准备多模态图片数据 (模拟庄园门口监控抓拍的访客照片)
# ==============================================================================
# 官方教程使用的是维基百科上的角色插图/蜡像照片
image_urls = [
    "https://upload.wikimedia.org/wikipedia/en/9/98/Joker_%28DC_Comics_character%29.jpg"
]

print("📸 正在下载访客监控抓拍图像...")
images = []
# 维基百科反爬策略要求带有合规的 User-Agent 标头，否则会返回 429/403
headers = {
    "User-Agent": "WayneManorSecurityBot/1.0 (contact: alfred@wayne.com)"
}

for url in image_urls:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert("RGB")
            images.append(img)
            print(f"✅ 成功载入图片，尺寸: {img.size} 像素")
        else:
            print(f"⚠️ 图片下载失败，HTTP 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 图片下载异常: {e}")

if not images:
    print("❌ 未能获取到任何有效图片，程序终止。")
    sys.exit(1)

# ==============================================================================
# 2. 初始化视觉多模态大模型 (VLM)
# ==============================================================================
# 注意：处理视觉图像时，切勿设置 flatten_messages_as_text=True，
# 否则底层框架会因无法将 Base64 图片展平为纯文本而触发断言报错！
model = OpenAIServerModel(
    model_id="glm-4v-flash",
    api_base="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.environ.get("ZHIPUAI_API_KEY"),
)

# ==============================================================================
# 3. 构建视觉核验智能体 (Vision CodeAgent)
# ==============================================================================
agent = CodeAgent(
    tools=[],       # 静态视觉阶段主要依靠模型的内生图文理解与 Python 沙箱对比
    model=model,
    max_steps=5,    # 焊死步数熔断线，防止异常死磕
    verbosity_level=1,
)

# ==============================================================================
# 4. 执行安检任务：图文细节提取与身份鉴别
# ==============================================================================
task = """
我是韦恩庄园的管家阿福。
门口有一位访客声称自己是“神奇女侠 (Wonder Woman)”，但我怀疑是“小丑 (The Joker)”恶意伪装混入派对！

请仔细观察抓拍图像中的人物：
1. 提取其外貌、发色、妆容与服饰特征；
2. 严谨判断这位访客到底是“The Joker”还是“Wonder Woman”；
3. 将你的推理过程和最终结论整理好，必须通过 final_answer 返回。

【重要规范】：请严格在 <code> 和 </code> 标签内编写 Python 代码！
例如：
<code>
final_answer("...")
</code>
"""

print("\n🧐 视觉智能体开始核验访客身份...\n")
response = agent.run(task, images=images)

print("\n🎉 阿福拿到的安检核验报告:")
print("=" * 60)
print(response)
print("=" * 60)

