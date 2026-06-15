# agent/state.py
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages

class ResearchState(TypedDict):
    """Agent共享状态"""
    messages: Annotated[List[Dict[str, str]], add_messages]
    plan: List[str]
    current_step: int
    findings: List[Dict[str, Any]]
    report_generated: bool
    task_type: str  # "research" 或 "chat"
    research_mode_override: Optional[bool]  # 强制指定模式