# tools/web_search_tool.py
"""
网络搜索工具 - WebSearchTool
使用Tavily API进行网络搜索
"""

import os
import json
from tavily import TavilyClient
from tools.base_tool import BaseTool

class WebSearchTool(BaseTool):
    """网络搜索工具"""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "使用Tavily搜索引擎搜索网络信息，获取最新资讯"
    
    def execute(self, params: dict) -> dict:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        try:
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            response = client.search(query=query, max_results=max_results, include_answer=True)
            results = {
                "query": query,
                "answer": response.get("answer", ""),
                "results": [
                    {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:500]}
                    for r in response.get("results", [])
                ]
            }
            return {
                "success": True,
                "raw_data": json.dumps(results, ensure_ascii=False),
                "summary": results.get("answer", "")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}