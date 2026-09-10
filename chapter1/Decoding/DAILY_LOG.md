# 📅 学习日志：2026-09-10

## 🎯 今日目标
* 探索大模型底层解码（Decoding）机制，实现生成决策树的本地可视化。

## ➕ 新增文件与功能
* [`visualize_helper.py`](visualize_helper.py)：通用 HTML 决策树渲染模块（注入 CSS 树形图样式，支持浏览器一键弹窗）；
* [`test1.py`](test1.py)：贪婪搜索（Greedy Search）测试脚本；
* [`test2.py`](test2.py)：束搜索（Beam Search: 2 beams）测试脚本；
* [`test3.py`](test3.py)：多候选束搜索（Beam Search: 4 beams, return 3）测试脚本；
* `test1_greedy.html` / `test2_beam_search_b2.html` / `test3_beam_search_b4.html`：本地渲染出的独立可视化网页。

## ✏️ 代码修改与排错
* **接口修正**：纠正 `test2.py` 误调用滑块联动接口的问题，修复为正规解码接口 `/get_beam_search_html`；
* **格式优化**：将原脚本直接将裸 HTML 写入文本文件的做法，重构为解析数据并自动生成完整交互网页。

## 🔨 执行记录
* 运行 `python test1.py`：成功生成并验证贪婪搜索单路径决策树；
* 运行 `python test2.py`：成功生成并验证 2 束并行决策树；
* 运行 `python test3.py`：成功生成并验证 4 束多候选决策树。

