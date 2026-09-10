from gradio_client import Client
from visualize_helper import save_and_open_html

print("正在连接 Hugging Face Beam Search Visualizer...")
client = Client("agents-course/beam_search_visualizer")

print("正在运行 Beam Search (束搜索: 4 beams, 5 steps, 返回 3 条候选句子)...")
result = client.predict(
    input_text="Conclusion: thanks a lot. That's all for today",
    number_steps=5,
    number_beams=4,
    length_penalty=1,
    num_return_sequences=3,
    api_name="/get_beam_search_html"
)

# result[0] 是 HTML 树状图，result[1] 是生成结果总结 Markdown
html_code, summary_text = result[0], result[1]

# 保存为独立网页并自动在浏览器中打开
save_and_open_html(
    html_raw=html_code,
    summary_raw=summary_text,
    output_filepath="test3_beam_search_b4.html",
    title="测试 3：束搜索 (Beam Search: beams=4, return=3) 多序列生成过程",
    auto_open=True
)