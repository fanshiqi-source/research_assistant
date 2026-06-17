# tools/__init__.py
"""
MCP 工具工厂 - 亮点
管理所有可插拔工具，支持动态注册和获取
遵循 MCP 协议规范
"""

from tools.base_tool import BaseTool
from tools.web_search_tool import WebSearchTool
from tools.web_fetch_tool import WebFetchTool
from tools.report_gen_tool import ReportGenTool
from tools.vector_tool import VectorSearchTool, VectorStoreTool

# 工具注册表
_tools = {
    "web_search": WebSearchTool(),
    "web_fetch": WebFetchTool(),
    "report_gen": ReportGenTool(),
    "vector_search": VectorSearchTool(),
    "vector_store": VectorStoreTool(),
}

def get_tool(name: str) -> BaseTool:
    """
    根据工具名称获取工具实例
    
    Args:
        name: 工具名称（如 "web_search", "report_gen"）
        
    Returns:
        BaseTool实例，如果未找到返回None
    """
    return _tools.get(name)

def register_tool(name: str, tool: BaseTool):
    """
    动态注册新工具
    
    Args:
        name: 工具名称
        tool: BaseTool实例
    """
    _tools[name] = tool

def list_tools() -> list:
    """列出所有可用工具"""
    return [
        {"name": name, "description": tool.description}
        for name, tool in _tools.items()
    ]

def get_tools_schema() -> list:
    """获取所有工具的 MCP Schema"""
    return [tool.get_schema() for tool in _tools.values()]