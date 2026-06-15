# agent/supervisor.py
"""
中心化调度器 - 亮点2
统一管控所有子Agent，负责任务分发和结果汇聚
"""

from typing import Dict, Any, List, Optional
from agent.agents.base_agent import BaseAgent
from agent.agents.classifier_agent import ClassifierAgent
from agent.agents.planner_agent import PlannerAgent
from agent.agents.researcher_agent import ResearcherAgent
from agent.agents.chat_agent import ChatAgent
from agent.state import ResearchState

class Supervisor:
    """中心调度器"""
    
    def __init__(self, llm):
        self.llm = llm
        self.agents: Dict[str, BaseAgent] = {
            "classifier": ClassifierAgent(llm),
            "planner": PlannerAgent(llm),
            "researcher": ResearcherAgent(llm),
            "chat": ChatAgent(llm)
        }
    
    def route(self, state: ResearchState) -> str:
        """根据当前状态决定下一个Agent"""
        # 如果报告已生成，后续对话全部路由到chat
        if state.get("report_generated"):
            return "chat"
        
        # 如果有研究计划但未完成，继续researcher
        if state.get("plan") and state.get("current_step", 0) < len(state.get("plan", [])):
            return "researcher"
        
        # 如果有研究模式覆盖
        if state.get("research_mode_override") is True:
            return "planner"
        if state.get("research_mode_override") is False:
            return "chat"
        
        # 默认先分类
        return "classifier"
    
    def execute_agent(self, agent_name: str, state: ResearchState) -> Dict[str, Any]:
        """执行指定Agent并返回状态更新"""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")
        return agent.run(state)