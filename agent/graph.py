# agent/graph.py
from langgraph.graph import StateGraph, START, END
from agent.state import ResearchState
from agent.supervisor import Supervisor
from langgraph.checkpoint.base import BaseCheckpointSaver

def create_agent_app(checkpointer: BaseCheckpointSaver):
    from langchain_openai import ChatOpenAI
    import os
    
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=0.3
    )
    
    supervisor = Supervisor(llm)
    
    def classifier_node(state: ResearchState):
        return supervisor.execute_agent("classifier", state)
    
    def planner_node(state: ResearchState):
        return supervisor.execute_agent("planner", state)
    
    def researcher_node(state: ResearchState):
        return supervisor.execute_agent("researcher", state)
    
    def chat_node(state: ResearchState):
        return supervisor.execute_agent("chat", state)
    
    def entry_router(state: ResearchState) -> str:
        if state.get("research_mode_override") is True:
            return "planner"
        if state.get("research_mode_override") is False:
            return "chat"
        # 删除了原来的“如果已有报告就直接聊天”的短路逻辑
        return "classifier"
    
    def route_after_classifier(state: ResearchState) -> str:
        task_type = state.get("task_type", "chat")
        return "planner" if task_type == "research" else "chat"
    
    def should_continue_research(state: ResearchState) -> str:
        if state.get("report_generated"):
            return END
        if state.get("current_step", 0) >= len(state.get("plan", [])):
            return END
        return "researcher"
    
    builder = StateGraph(ResearchState)
    builder.add_node("classifier", classifier_node)
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("chat", chat_node)
    
    builder.add_conditional_edges(START, entry_router, {
        "classifier": "classifier",
        "planner": "planner",
        "chat": "chat"
    })
    builder.add_conditional_edges("classifier", route_after_classifier, {
        "planner": "planner",
        "chat": "chat"
    })
    builder.add_edge("planner", "researcher")
    builder.add_conditional_edges("researcher", should_continue_research, {
        "researcher": "researcher",
        END: END
    })
    builder.add_edge("chat", END)
    
    return builder.compile(checkpointer=checkpointer)