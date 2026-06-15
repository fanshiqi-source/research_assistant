from datetime import datetime
from skills.base_skill import Skill
from langchain_core.messages import HumanMessage

class ReportGenSkill(Skill):
    @property
    def name(self) -> str:
        return "report_gen"

    @property
    def description(self) -> str:
        return "根据研究发现生成结构化报告，并自动存储到知识库"

    def execute(self, params: dict) -> dict:
        findings = params.get("findings", [])
        question = params.get("question", "研究")
        llm = params.get("llm")  # 可选，若没有则需要全局获取

        # 如果没有传入llm，尝试从外部获取（这里简单处理，实际最好由调用方传入）
        if llm is None:
            from langchain_openai import ChatOpenAI
            import os
            llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                temperature=0.3
            )

        report = f"# 关于“{question}”的研究报告\n\n"
        report += f"**研究时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        report += "## 研究发现\n"

        for i, f in enumerate(findings, 1):
            if f.get("topic"):
                report += f"\n### {i}. {f['topic']}\n"
            if f.get("answer"):
                report += f"{f['answer']}\n"
            if f.get("content"):
                report += f"{f['content']}\n"
            if f.get("source"):
                report += f"\n*来源：{f['source']}*\n"

        # 调用LLM生成结论
        context = "\n".join([f.get("content", "") for f in findings if f.get("content")])[:2000]
        conclusion_prompt = f"基于以下研究发现，为研究报告撰写一段总结性结论：\n{context}"
        conclusion = llm.invoke([HumanMessage(content=conclusion_prompt)]).content

        report += f"\n## 结论\n{conclusion}\n"

        # 将报告存储到向量知识库（延迟导入避免循环依赖）
        from skills import get_skill
        vector_store_skill = get_skill("vector_store")
        if vector_store_skill:
            try:
                metadata = {
                    "question": question,
                    "timestamp": datetime.now().isoformat(),
                    "type": "research_report"
                }
                vector_store_skill.execute({
                    "documents": [report],
                    "metadatas": [metadata]
                })
                print(f"📚 报告已存储到知识库")
            except Exception as e:
                print(f"存储到知识库失败: {e}")

        return {"success": True, "report": report}