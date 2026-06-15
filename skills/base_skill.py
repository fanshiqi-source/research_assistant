# skills/base_skill.py
"""
Skill技能体系基类 - 亮点3
标准化可插拔Skill单元
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class Skill(ABC):
    """技能基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能，返回结果字典"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """返回技能参数Schema，用于MCP协议"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }