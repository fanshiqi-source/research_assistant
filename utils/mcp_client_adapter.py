# utils/mcp_client_adapter.py
"""
MCP 客户端适配器 - 兼容多种 MCP 库版本
使用统一的工具调用接口
"""

import sys
from typing import Dict, Any, Optional, Callable

class MCPToolResult:
    def __init__(self, content: str, error: Optional[str] = None):
        self.content = content
        self.error = error
        self.success = error is None

class MCPAdapter:
    def __init__(self):
        self._client = None
        self._client_type = "fallback"
        self._call_tool_func = self._fallback_call_tool
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            from mcp import Client
            self._client = Client()
            self._call_tool_func = self._mcp_call_tool
            self._client_type = "mcp"
            print("使用官方 MCP 库")
            return
        except ImportError:
            pass
        
        try:
            from langchain_mcp import get_mcp_client
            self._client = get_mcp_client()
            self._call_tool_func = self._langchain_mcp_call_tool
            self._client_type = "langchain_mcp"
            print("使用 langchain_mcp")
            return
        except ImportError:
            pass
        
        try:
            from langchain_mcp.client import MCPClient
            self._client = MCPClient()
            self._call_tool_func = self._langchain_mcp_call_tool
            self._client_type = "langchain_mcp"
            print("使用 langchain_mcp.MCPClient")
            return
        except ImportError:
            pass
        
        print("MCP 库不可用，使用本地工具系统作为回退")
    
    def get_client_type(self):
        return self._client_type
    
    def call_tool(self, tool_name, arguments):
        try:
            result = self._call_tool_func(tool_name, arguments)
            return MCPToolResult(
                content=result.get("content", ""),
                error=result.get("error")
            )
        except Exception as e:
            return MCPToolResult(content="", error=str(e))
    
    def list_tools(self):
        if self._client_type == "fallback":
            from tools import list_tools
            return list_tools()
        
        try:
            if hasattr(self._client, "list_tools"):
                return self._client.list_tools()
            elif hasattr(self._client, "tools") and hasattr(self._client.tools, "list"):
                return self._client.tools.list()
        except Exception:
            pass
        
        return []
    
    def _mcp_call_tool(self, tool_name, arguments):
        try:
            result = self._client.call_tool(tool_name, arguments)
            return {"content": str(result), "error": None}
        except Exception as e:
            return {"content": "", "error": str(e)}
    
    def _langchain_mcp_call_tool(self, tool_name, arguments):
        try:
            result = self._client.invoke_tool(tool_name, arguments)
            return {"content": str(result), "error": None}
        except Exception as e:
            return {"content": "", "error": str(e)}
    
    def _fallback_call_tool(self, tool_name, arguments):
        from tools import get_tool
        tool = get_tool(tool_name)
        if not tool:
            return {"content": "", "error": "Tool '{}' not found".format(tool_name)}
        result = tool.execute(arguments)
        content = result.get("content", "") or result.get("answer", "")
        return {
            "content": content,
            "error": result.get("error")
        }

_mcp_adapter = None

def get_mcp_adapter():
    global _mcp_adapter
    if _mcp_adapter is None:
        _mcp_adapter = MCPAdapter()
    return _mcp_adapter