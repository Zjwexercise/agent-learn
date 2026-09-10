from typing import Any, Optional
from smolagents.tools import Tool
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

def _extract_query(q: Any) -> str:
    if isinstance(q, str):
        return q
    if isinstance(q, dict):
        for k in ("query", "q", "topic", "description", "keyword", "keywords", "text"):
            if k in q:
                return _extract_query(q[k])
        return " ".join(str(v) for v in q.values() if not isinstance(v, (dict, list)))
    if isinstance(q, (list, tuple)):
        return " ".join(_extract_query(item) for item in q)
    return str(q)

class DuckDuckGoSearchTool(Tool):
    name = "web_search"
    description = "Performs a duckduckgo web search based on your query then returns the top search results."
    inputs = {'query': {'type': 'any', 'description': 'The search query string (e.g. "科技最新动态").'}}
    output_type = "string"

    def __init__(self, max_results=3, **kwargs):
        super().__init__()
        self.max_results = max_results
        if DDGS is None:
            raise ImportError(
                "You must install package `ddgs` or `duckduckgo-search` to run this tool."
            )
        self.ddgs = DDGS(**kwargs)

    def forward(self, query: Any) -> str:
        clean_query = _extract_query(query).strip()
        if not clean_query:
            return "未能解析出有效的搜索关键词，请提供具体的搜索词。"
        try:
            results = self.ddgs.text(clean_query, max_results=self.max_results)
            if not results:
                return f"未能搜索到关于「{clean_query}」的网页结果，请尝试更简短或更换关键词。"
            postprocessed_results = [f"[{r.get('title', '')}]({r.get('href', '')})\n{r.get('body', '')[:120]}" for r in results]
            return "## Search Results\n\n" + "\n\n".join(postprocessed_results)
        except Exception as e:
            return f"执行搜索「{clean_query}」时出错: {str(e)}"



