# tools/base_tool.py
"""
工具基类 - MCP 工具工厂体系
标准化可插拔工具单元
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """工具基类 - 所有工具必须继承此类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            params: 参数字典
            
        Returns:
            结果字典，必须包含 success 字段
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """返回工具参数 Schema，用于 MCP 协议"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }