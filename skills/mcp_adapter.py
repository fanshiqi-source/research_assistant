# skills/mcp_adapter.py
"""
MCP+Skill一体化工具调用 - 亮点4
实现MCP协议风格的工具发现与调用
"""

from typing import Dict, Any, List
from skills import get_skill, _skills

class MCPAdapter:
    """MCP协议适配器，提供统一的工具调用接口"""
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具（MCP tools/list）"""
        tools = []
        for name, skill in _skills.items():
            tools.append({
                "name": skill.name,
                "description": skill.description,
                "inputSchema": skill.get_schema()
            })
        return tools
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具（MCP tools/call）"""
        skill = get_skill(tool_name)
        if not skill:
            return {"error": f"Tool '{tool_name}' not found"}
        return skill.execute(arguments)
    
    def execute_step(self, step_description: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """根据步骤描述自动选择合适的工具执行（智能路由）"""
        # 简单实现：根据关键词匹配工具
        step_lower = step_description.lower()
        if "搜索" in step_lower:
            question = ""
            for m in state.get("messages", []):
                if m.get("role") == "user":
                    question = m.get("content", "")
                    break
            return self.call_tool("web_search", {"query": question})
        elif "阅读" in step_lower or "获取" in step_lower:
            # 需要从state中获取待阅读的URL
            urls = []
            for f in state.get("findings", []):
                if "urls" in f:
                    urls.extend(f["urls"])
            if urls:
                return self.call_tool("web_fetch", {"url": urls[0]})
        elif "报告" in step_lower:
            return self.call_tool("report_gen", {"findings": state.get("findings", []), "question": ""})
        return {"error": "No matching tool found", "step": step_description}