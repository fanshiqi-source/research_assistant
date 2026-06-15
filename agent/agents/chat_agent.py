from agent.agents.base_agent import BaseAgent
from agent.state import ResearchState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from skills import get_skill

class ChatAgent(BaseAgent):
    def run(self, state: ResearchState) -> dict:
        # 提取用户消息
        user_msg = ""
        for m in reversed(state.get("messages", [])):
            if getattr(m, "type", "") == "human":
                user_msg = m.content
                break
            elif isinstance(m, dict) and m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        if not user_msg:
            user_msg = "你好"

        # 构建上下文：之前的研究发现
        context = ""
        if state.get("report_generated") and state.get("findings"):
            context += "【上一轮研究发现】\n"
            for f in state["findings"]:
                if f.get("content"):
                    context += f"- {f['content'][:300]}\n"
                if f.get("answer"):
                    context += f"- {f['answer'][:300]}\n"
            context += "\n"

        # 向量检索：从知识库中查找相似历史报告
        vector_search_skill = get_skill("vector_search")
        if vector_search_skill:
            try:
                result = vector_search_skill.execute({"query": user_msg, "n_results": 3})
                if result.get("success") and result.get("results"):
                    context += "【知识库相关内容】\n"
                    for i, item in enumerate(result["results"], 1):
                        if item.get("score", 0) > 0.5:
                            context += f"{i}. {item.get('content', '')[:400]}\n"
            except Exception as e:
                print(f"向量检索失败: {e}")

        system_prompt = f"""你是一个智能、体贴的助手。请根据用户的消息内容直接、具体地回应。

{context}

- 如果用户问好，友好回应并主动提供帮助。
- 如果用户表达情绪（如不满、调侃），恰当安抚或幽默回应。
- 如果用户给出无意义字符（如"666"），可以表示没理解请重说，或者幽默化解。
- 不要每次都输出相同的开场白。
- 如果用户追问与之前研究相关的问题，请结合上面的研究发现和知识库内容回答。
- 如果知识库中有相关内容，请优先参考知识库的信息。"""
        system = SystemMessage(content=system_prompt)
        resp = self.llm.invoke([system, HumanMessage(content=user_msg)])
        return {"messages": [AIMessage(content=resp.content)]}