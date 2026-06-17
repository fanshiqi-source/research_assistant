# agent/agents/researcher_agent.py
"""
研究执行Agent - 核心研究执行者
负责按计划执行研究步骤：搜索、阅读、整理、报告
使用Skill体系调用各类工具完成具体任务
"""

from agent.agents.base_agent import BaseAgent
from agent.state import ResearchState
from skills import get_skill
from utils.mcp_client_adapter import get_mcp_adapter, MCPToolResult
from utils.skill_parser import get_skill_parser
from langchain_core.messages import HumanMessage, AIMessage
import json


class ResearcherAgent(BaseAgent):
    """研究执行Agent - 按计划调用Skill工具执行研究步骤"""

    def run(self, state: ResearchState) -> dict:
        plan = state.get("plan", [])
        idx = state.get("current_step", 0)
        findings = state.get("findings", [])

        # 研究完成：所有步骤执行完毕
        if idx >= len(plan):
            if not state.get("report_generated"):
                original_q = self._get_latest_user_message(state)
                if findings:
                    context = []
                    for f in findings:
                        if f.get("answer"):
                            context.append(f["answer"])
                        if f.get("content"):
                            context.append(f["content"][:500])
                    prompt = f"用户问题：{original_q}\n\n基于以下研究结果，生成一份详细的总结报告：\n" + "\n".join(context)[:3000]
                else:
                    prompt = f"用户问题：{original_q}\n\n请直接基于自身知识回答这个问题。"
                resp = self.llm.invoke([HumanMessage(content=prompt)])
                return {
                    "messages": [AIMessage(content=resp.content)],
                    "report_generated": True,
                    "findings": findings
                }
            # 已生成报告，返回空更新（状态由外部维护）
            return {}

        step = plan[idx]
        # 获取当前研究主题（最新用户问题）
        current_topic = self._get_latest_user_message(state)

        # 输出步骤进度信息
        step_info = f"步骤{idx + 1}/{len(plan)}: {step}..."
        print(f"\n🔍 {step_info}")

        # 获取技能解析器（用于获取可用技能列表）
        parser = get_skill_parser()
        available_skills = parser.list_skills()

        # -------------------- 报告生成 --------------------
        if "报告" in step:
            skill = get_skill("report_gen")
            if skill:
                # 传入 llm 实例，供 skill 内部生成结论
                result = skill.execute({
                    "findings": findings,
                    "question": current_topic,
                    "llm": self.llm
                })
                return {
                    "messages": [AIMessage(content=result["report"])],
                    "current_step": idx + 1,
                    "findings": findings,
                    "report_generated": True
                }
            else:
                # 降级：直接调用 LLM 生成报告
                prompt = f"请根据以下研究发现，生成关于“{current_topic}”的研究报告：\n{json.dumps(findings, ensure_ascii=False, indent=2)}"
                resp = self.llm.invoke([HumanMessage(content=prompt)])
                return {
                    "messages": [AIMessage(content=resp.content)],
                    "current_step": idx + 1,
                    "findings": findings,
                    "report_generated": True
                }

        # -------------------- 网络搜索 --------------------
        elif "搜索" in step:
            # 使用技能文档决策辅助
            if available_skills:
                print(f"📚 可用技能文档: {available_skills}")
                prompt = parser.get_decision_prompt(current_topic, step)
                resp = self.llm.invoke([HumanMessage(content=prompt)])
                try:
                    decision = json.loads(resp.content)
                    if decision.get("decision") == "use_skill":
                        skill_name = decision.get("skill_name")
                        parameters = decision.get("parameters", {})
                        print(f"🤖 LLM决定使用技能: {skill_name}")
                        print(f"   参数: {parameters}")
                        
                        skill = get_skill(skill_name)
                        if skill:
                            result = skill.execute(parameters)
                            # 提取搜索结果中的URLs
                            urls = []
                            if result.get("success") and result.get("raw_data"):
                                try:
                                    data = json.loads(result["raw_data"])
                                    urls = [r["url"] for r in data.get("results", [])[:3]]
                                except:
                                    pass
                            
                            findings.append({
                                "topic": f"搜索：{parameters.get('query', current_topic)}",
                                "answer": result.get("answer", "") or result.get("content", "") or str(result),
                                "urls": urls,
                                "source": "技能文档驱动"
                            })
                            return {"current_step": idx + 1, "findings": findings}
                except json.JSONDecodeError:
                    print(f"⚠️ 无法解析LLM决策，使用默认逻辑")
            
            # 默认逻辑
            skill = get_skill("web_search")
            if skill:
                query = current_topic
                result = skill.execute({"query": query})
                if result.get("success"):
                    data = json.loads(result["raw_data"])
                    findings.append({
                        "topic": f"搜索：{query}",
                        "answer": data.get("answer", ""),
                        "urls": [r["url"] for r in data.get("results", [])[:3]],
                        "source": "Tavily"
                    })
            return {"current_step": idx + 1, "findings": findings}

        # -------------------- 阅读网页 --------------------
        elif "阅读" in step:
            urls = []
            for f in findings:
                if "urls" in f:
                    urls.extend(f["urls"])
            if urls:
                skill = get_skill("web_fetch")
                if skill:
                    result = skill.execute({"url": urls[0]})
                    if result.get("success"):
                        findings.append({
                            "topic": f"网页: {urls[0]}",
                            "content": result["content"][:800],
                            "source": urls[0]
                        })
            return {"current_step": idx + 1, "findings": findings}

        # -------------------- 整理/总结 --------------------
        elif "整理" in step or "总结" in step:
            context = []
            for f in findings:
                if f.get("answer"):
                    context.append(f["answer"])
                if f.get("content"):
                    context.append(f["content"][:500])
            prompt = f"基于以下信息总结3-5个核心发现：\n" + "\n".join(context)[:3000]
            resp = self.llm.invoke([HumanMessage(content=prompt)])
            findings.append({
                "topic": "核心发现",
                "content": resp.content,
                "source": "综合分析"
            })
            return {"current_step": idx + 1, "findings": findings}

        # -------------------- 其他步骤（使用MCP适配器）----------------
        else:
            adapter = get_mcp_adapter()
            result = adapter.call_tool("web_search", {"query": current_topic})
            if result.success:
                findings.append({
                    "topic": f"MCP工具调用: {step}",
                    "content": result.content[:800],
                    "source": f"MCP ({adapter.get_client_type()})"
                })
            return {"current_step": idx + 1, "findings": findings}

    def _get_latest_user_message(self, state: ResearchState) -> str:
        """从state中提取最新用户消息（兼容属性和字典）"""
        messages = state.get("messages", [])
        for m in reversed(messages):
            # LangChain 对象：type 属性为 "human"
            if getattr(m, "type", "") == "human":
                return m.content
            # 字典访问
            if isinstance(m, dict) and m.get("role") == "user":
                return m.get("content", "")
        return ""