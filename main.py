# main.py
import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Iterator
from dotenv import load_dotenv
import json
from contextlib import asynccontextmanager

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent.graph import create_agent_app
from memory.persistent_memory import get_memory_saver

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：预热向量存储，提前加载 embedding 模型
    from utils.vector_store import get_vector_store
    vs = get_vector_store()
    vs.search("warmup", n_results=1)
    print("✅ 向量存储预热完成，embedding 模型已加载。")
    yield
    # 可以在此添加关闭时的清理逻辑

app = FastAPI(title="个人研究助理Agent", lifespan=lifespan)

from fastapi.staticfiles import StaticFiles
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_saver = get_memory_saver()
agent_app = create_agent_app(memory_saver)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    research_mode: Optional[bool] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tokens_used: int
    research_used: bool

@app.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>个人研究助理Agent</h1><p>请确保 frontend/index.html 存在</p>")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    from utils.input_normalizer import normalize_input
    from utils.token_monitor import TokenMonitor
    from agent.state import ResearchState
    from memory.persistent_memory import get_memory

    config = {"configurable": {"thread_id": request.session_id}}
    normalized_message = normalize_input(request.message)
    
    memory = get_memory()
    history_messages = memory.load_conversation(request.session_id)
    
    prev_state = memory.load_memory(request.session_id, "research_state")
    prev_findings = []
    prev_report_generated = False
    if prev_state:
        try:
            state_data = json.loads(prev_state)
            prev_findings = state_data.get("findings", [])
            prev_report_generated = state_data.get("report_generated", False)
        except:
            pass
    
    new_message = {"role": "user", "content": normalized_message}
    all_messages = history_messages + [new_message]

    state: ResearchState = {
        "messages": all_messages,
        "research_mode_override": request.research_mode,
        "plan": [],
        "current_step": 0,
        "findings": prev_findings,
        "report_generated": prev_report_generated,
        "task_type": "",
    }

    final_state = None
    for output in agent_app.stream(state, config=config):
        for node_name, node_output in output.items():
            final_state = node_output

    response_text = ""
    final_messages = []
    if final_state and "messages" in final_state:
        for msg in final_state["messages"]:
            if getattr(msg, "type", "") == "ai":
                response_text = msg.content
                final_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                response_text = msg.get("content", "")
                final_messages.append(msg)
    
    memory.save_conversation(request.session_id, final_messages)
    
    if final_state and final_state.get("report_generated"):
        research_state_data = {
            "findings": final_state.get("findings", []),
            "report_generated": True
        }
        memory.save_memory(request.session_id, "research_state", json.dumps(research_state_data, ensure_ascii=False))
    
    if not response_text:
        response_text = "抱歉，我无法处理您的请求。"

    monitor = TokenMonitor()
    tokens = monitor.estimate_tokens(normalized_message + response_text)
    research_used = final_state.get("report_generated", False) if final_state else False

    return ChatResponse(
        response=response_text,
        session_id=request.session_id,
        tokens_used=tokens,
        research_used=research_used
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    from utils.input_normalizer import normalize_input
    from utils.token_monitor import TokenMonitor
    from agent.state import ResearchState
    from memory.persistent_memory import get_memory

    config = {"configurable": {"thread_id": request.session_id}}
    normalized_message = normalize_input(request.message)
    
    memory = get_memory()
    history_messages = memory.load_conversation(request.session_id)
    
    prev_state = memory.load_memory(request.session_id, "research_state")
    prev_findings = []
    prev_report_generated = False
    if prev_state:
        try:
            state_data = json.loads(prev_state)
            prev_findings = state_data.get("findings", [])
            prev_report_generated = state_data.get("report_generated", False)
        except:
            pass
    
    new_message = {"role": "user", "content": normalized_message}
    all_messages = history_messages + [new_message]

    state: ResearchState = {
        "messages": all_messages,
        "research_mode_override": request.research_mode,
        "plan": [],
        "current_step": 0,
        "findings": prev_findings,
        "report_generated": prev_report_generated,
        "task_type": "",
    }

    def generate_stream() -> Iterator[str]:
        final_state = None
        step_count = 0
        
        for output in agent_app.stream(state, config=config):
            for node_name, node_output in output.items():
                final_state = node_output
                
                if "current_step" in node_output and "plan" in node_output:
                    current_step = node_output["current_step"]
                    plan = node_output["plan"]
                    if current_step > step_count and plan:
                        step_count = current_step
                        if current_step <= len(plan):
                            step_info = {
                                "type": "step",
                                "step": current_step,
                                "total": len(plan),
                                "message": f"步骤{current_step}/{len(plan)}: {plan[current_step-1] if current_step > 0 else '开始...'}"
                            }
                            yield f"data: {json.dumps(step_info, ensure_ascii=False)}\n\n"
        
        response_text = ""
        final_messages = []
        if final_state and "messages" in final_state:
            for msg in final_state["messages"]:
                if getattr(msg, "type", "") == "ai":
                    response_text = msg.content
                    final_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    response_text = msg.get("content", "")
                    final_messages.append(msg)
        
        memory.save_conversation(request.session_id, final_messages)
        
        if final_state and final_state.get("report_generated"):
            research_state_data = {
                "findings": final_state.get("findings", []),
                "report_generated": True
            }
            memory.save_memory(request.session_id, "research_state", json.dumps(research_state_data, ensure_ascii=False))
        
        if not response_text:
            response_text = "抱歉，我无法处理您的请求。"
        
        monitor = TokenMonitor()
        tokens = monitor.estimate_tokens(normalized_message + response_text)
        research_used = final_state.get("report_generated", False) if final_state else False
        
        result = {
            "type": "result",
            "response": response_text,
            "session_id": request.session_id,
            "tokens_used": tokens,
            "research_used": research_used
        }
        yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)