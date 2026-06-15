# agent/agents/base_agent.py
"""
多Agent协作基类 - 亮点1
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from agent.state import ResearchState

class BaseAgent(ABC):
    def __init__(self, llm):
        self.llm = llm
    
    @abstractmethod
    def run(self, state: ResearchState) -> Dict[str, Any]:
        """执行Agent逻辑，返回状态更新字典"""
        pass