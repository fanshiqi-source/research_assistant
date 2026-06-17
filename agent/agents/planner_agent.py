# agent/agents/planner_agent.py
"""
智能推理规划Agent - 亮点6
基于Plan-and-Execute范式，自动生成研究步骤
步骤包括：搜索 → 阅读 → 整理 → 报告
"""

from agent.agents.base_agent import BaseAgent
from agent.state import ResearchState
from langchain_core.messages import HumanMessage, SystemMessage
import json

class PlannerAgent(BaseAgent):
    """智能推理规划Agent - 基于最新用户问题生成研究计划"""

    def run(self, state: ResearchState) -> dict:
        # 获取最新用户消息
        latest_user_msg = ""
        for m in reversed(state.get("messages", [])):
            if getattr(m, "type", "") == "human":
                latest_user_msg = m.content
                break
            elif isinstance(m, dict) and m.get("role") == "user":
                latest_user_msg = m.get("content", "")
                break

        if not latest_user_msg:
            return {"plan": []}

        system = SystemMessage(content="""你是研究规划专家。请根据用户最新提出的问题，制定清晰的研究步骤。
输出严格JSON：{"steps": ["步骤1", "步骤2", ...]}
步骤命名必须包含以下关键词之一（每个步骤选择最合适的一个）：
- "搜索"：搜索网络资料
- "阅读"：阅读网页内容
- "整理"或"总结"：整理研究发现
- "报告"：生成最终研究报告

典型流程示例：["搜索相关资料", "阅读关键网页", "整理研究发现", "生成报告"]""")
        resp = self.llm.invoke([system, HumanMessage(content=f"研究问题：{latest_user_msg}")])
        try:
            content = resp.content
            start = content.find("{")
            end = content.rfind("}") + 1
            plan = json.loads(content[start:end])["steps"]
        except:
            plan = [f"搜索关于'{latest_user_msg}'的资料", "阅读关键网页", "整理发现", "生成报告"]

        return {"plan": plan, "current_step": 0, "findings": [], "report_generated": False}