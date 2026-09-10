import os
import webbrowser
import re
from html.parser import HTMLParser

HTML_SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <style>
        :root {
            --body-text-color: #1e293b;
            --primary-500: #bae6fd;
            --primary-400: #7dd3fc;
            --secondary-500: #86efac;
            --border-color: #cbd5e1;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f1f5f9;
            color: var(--body-text-color);
            padding: 30px;
            margin: 0;
        }
        .header {
            margin-bottom: 20px;
        }
        h1 {
            color: #0f172a;
            font-size: 26px;
            margin-bottom: 6px;
        }
        .subtitle {
            color: #64748b;
            font-size: 14px;
        }
        .summary-box {
            background: #ffffff;
            border-left: 5px solid #0284c7;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            font-size: 14px;
            line-height: 1.6;
        }
        .summary-title {
            font-weight: 700;
            color: #0369a1;
            margin-bottom: 6px;
        }
        .tree-card {
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 24px;
            overflow-x: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        /* Hugging Face Tree Styles */
        .custom-container {
            display: inline-block;
            min-width: 100%;
        }
        .tree {
            display: inline-block;
            font-size: 12px;
            white-space: nowrap;
            padding: 10px;
        }
        .tree ul {
            padding-left: 28px;
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin: 0;
            list-style-type: none;
        }
        .tree li {
            display: flex;
            align-items: center;
            position: relative;
            padding-left: 20px;
        }
        .tree li::before, .tree li::after {
            content: '';
            position: absolute;
            left: 0;
            border-left: 2px solid #94a3b8;
            width: 20px;
        }
        .tree li::before {
            top: 0;
            height: 50%;
        }
        .tree li::after {
            top: 50%;
            height: 50%;
            border-top: 2px solid #94a3b8;
        }
        .tree li:only-child::after, .tree li:only-child::before {
            display: none;
        }
        .tree li:first-child::before, .tree li:last-child::after {
            border: 0 none;
        }
        .tree li:last-child::before {
            border-bottom: 2px solid #94a3b8;
            border-radius: 0 0 0 6px;
        }
        .tree li:first-child::after {
            border-radius: 6px 0 0 0;
        }
        .tree ul ul::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            border-top: 2px solid #94a3b8;
            width: 20px;
        }
        .tree li a {
            border: 1px solid #cbd5e1;
            background: #ffffff;
            border-radius: 6px;
            padding: 8px 12px;
            display: inline-flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: inherit;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            transition: all 0.2s ease;
        }
        .tree li a:hover {
            border-color: #0284c7;
            box-shadow: 0 2px 8px rgba(2,132,199,0.15);
        }
        .tree li a span {
            font-weight: 600;
            font-size: 13px;
        }
        table {
            border-collapse: collapse;
            font-size: 12px;
            margin: 0;
        }
        th, td {
            padding: 4px 8px;
            text-align: left;
            border: 1px solid #e2e8f0;
        }
        th {
            background: #f8fafc;
            font-weight: 600;
            color: #475569;
        }
        .chosen-token {
            background-color: #bae6fd !important;
            font-weight: bold;
            color: #0369a1 !important;
        }
        .selected-sequence {
            background-color: #86efac !important;
            border: 2px solid #16a34a !important;
            font-weight: bold;
            color: #14532d;
        }
        .nonselected-sequence {
            background-color: #e2e8f0 !important;
            color: #64748b;
        }
        .end-of-text {
            font-weight: bold;
        }
        .legend {
            display: flex;
            gap: 20px;
            margin-bottom: 16px;
            font-size: 13px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid #94a3b8;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 {{TITLE}}</h1>
        <div class="subtitle">Hugging Face Agents Course 第一章：LLM 生成解码策略（Decoding Strategy）可视化</div>
    </div>

    <div class="summary-box">
        <div class="summary-title">📌 解码说明与最终生成序列：</div>
        <div>{{SUMMARY_HTML}}</div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <span class="legend-color" style="background-color: #bae6fd;"></span>
            <span><b>选中候选词 (Chosen Token)</b>：当前步得分最高并被选择的 Token</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #86efac; border: 2px solid #16a34a;"></span>
            <span><b>最终胜出序列 (Selected Sequence)</b>：满足结束条件或束搜索总分最高路径</span>
        </div>
    </div>

    <div class="tree-card">
        {{TREE_HTML}}
    </div>
</body>
</html>
"""

def print_terminal_summary(summary_raw):
    """在终端格式化打印清晰的解码概要"""
    print("\n" + "="*70)
    print(" 📖 解码总结 (Decoding Summary):")
    print("="*70)
    lines = summary_raw.strip().split("\n")
    for line in lines:
        if line.startswith("#"):
            print(f"  {line.lstrip('#').strip()}")
        elif line.startswith("- "):
            print(f"  -> 生成序列: {line[2:].strip()}")
        else:
            print(f"  {line}")
    print("="*70 + "\n")

def save_and_open_html(html_raw, summary_raw, output_filepath, title="Decoding 过程可视化", auto_open=True):
    """保存为独立 HTML 并在浏览器中打开"""
    # 格式化 summary 中的换行和 markdown 序列高亮
    summary_html = summary_raw.replace("\n", "<br>")
    summary_html = re.sub(r"`(.*?)`", r"<code style='background:#f1f5f9;padding:2px 6px;border-radius:4px;color:#d97706;'>\1</code>", summary_html)

    page = HTML_SHELL.replace("{{TITLE}}", title)
    page = page.replace("{{SUMMARY_HTML}}", summary_html)
    page = page.replace("{{TREE_HTML}}", html_raw)
    
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(page)
        
    abs_path = os.path.abspath(output_filepath)
    print(f"  可视化网页已生成: {output_filepath}")
    print(f"  完整路径: {abs_path}")
    
    print_terminal_summary(summary_raw)
    
    if auto_open:
        try:
            webbrowser.open(f"file:///{abs_path}")
            print(" 已自动在浏览器中打开！\n")
        except Exception:
            print(" 请双击上述 HTML 文件在浏览器中查看。\n")
    return abs_path

