# agent/agents/__init__.py
"""
Agent模块初始化文件
注册所有Agent类型供Supervisor调用
"""

from agent.agents.base_agent import BaseAgent
from agent.agents.classifier_agent import ClassifierAgent
from agent.agents.planner_agent import PlannerAgent
from agent.agents.researcher_agent import ResearcherAgent
from agent.agents.chat_agent import ChatAgent

__all__ = [
    "BaseAgent",
    "ClassifierAgent",
    "PlannerAgent",
    "ResearcherAgent",
    "ChatAgent"
]
