# agent/agents/classifier_agent.py
from agent.agents.base_agent import BaseAgent
from agent.state import ResearchState
from langchain_core.messages import HumanMessage
from utils.input_normalizer import analyze_input

class ClassifierAgent(BaseAgent):
    """问题类型分流Agent - 亮点8"""
    
    def run(self, state: ResearchState) -> dict:
        # 强制研究模式覆盖
        override = state.get("research_mode_override")
        if override is True:
            return {"task_type": "research"}
        if override is False:
            return {"task_type": "chat"}

        messages = state.get("messages", [])
        user_msg = ""
        for m in reversed(messages):
            if getattr(m, "type", "") == "human":
                user_msg = m.content
                break
            elif isinstance(m, dict) and m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        # 使用增强的输入分析
        analysis = analyze_input(user_msg)
        intent = analysis.get("intent", "question")
        keywords = analysis.get("keywords", [])
        
        print(f"📊 输入分析结果: 意图={intent}, 关键词={keywords}")
        
        # 基于意图判断任务类型
        if intent == "research":
            return {"task_type": "research", "intent": intent, "keywords": keywords}
        
        # LLM最终确认
        prompt = f"""判断以下用户问题是否需要进行网络搜索和资料整理来回答。
只回答一个单词：research（需要研究）或 chat（直接对话即可）。

问题：{user_msg}
"""
        res = self.llm.invoke([HumanMessage(content=prompt)])
        task = "research" if "research" in res.content.lower() else "chat"
        return {"task_type": task, "intent": intent, "keywords": keywords}