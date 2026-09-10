from gradio_client import Client
from visualize_helper import save_and_open_html

print("正在连接 Hugging Face Decoding Visualizer...")
client = Client("agents-course/decoding_visualizer")

print("正在运行 Greedy Search (贪婪搜索) 解码...")
result = client.predict(
    input_text="The Capital of France is",
    api_name="/get_beam_search_html"
)

# result[0] 是 HTML 树状图，result[1] 是生成结果总结 Markdown
html_code, summary_text = result[0], result[1]

# 保存为独立网页并自动在浏览器中打开
save_and_open_html(
    html_raw=html_code,
    summary_raw=summary_text,
    output_filepath="test1_greedy.html",
    title="测试 1：贪婪搜索 (Greedy Search) 解码过程",
    auto_open=True
)
