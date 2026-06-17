# main.py
"""
个人研究助理Agent - FastAPI 服务入口文件

本文件是项目的主入口，负责：
1. 创建 FastAPI 应用实例
2. 配置 CORS 跨域中间件
3. 注册 API 路由（同步聊天、流式聊天、健康检查）
4. 加载前端静态文件
5. 管理应用生命周期（向量存储预热）

技术栈：
- FastAPI: 高性能 Web 框架
- LangGraph: Agent 工作流编排
- SQLite: 会话持久化存储
- ChromaDB: 向量知识库

API 端点：
- GET /: 返回前端页面
- POST /chat: 同步聊天接口
- POST /chat/stream: 流式聊天接口（支持步骤进度推送）
- GET /health: 健康检查
"""

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

# 加载环境变量
load_dotenv()
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from agent.graph import create_agent_app
from memory.persistent_memory import get_memory_saver

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期钩子
    
    启动时：预热向量存储，提前加载 embedding 模型
    关闭时：可添加清理逻辑
    """
    # 预热向量存储，避免首次请求时的冷启动延迟
    from utils.vector_store import get_vector_store
    vs = get_vector_store()
    vs.search("warmup", n_results=1)
    print("✅ 向量存储预热完成，embedding 模型已加载。")
    yield
    # 可以在此添加关闭时的清理逻辑（如关闭数据库连接等）

# 创建 FastAPI 应用实例
app = FastAPI(title="个人研究助理Agent", lifespan=lifespan)

# 挂载前端静态文件
from fastapi.staticfiles import StaticFiles
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# 配置 CORS 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有来源（生产环境应限制具体域名）
    allow_methods=["*"],      # 允许所有 HTTP 方法
    allow_headers=["*"],      # 允许所有请求头
)

# 初始化 Agent 应用
memory_saver = get_memory_saver()
agent_app = create_agent_app(memory_saver)

class ChatRequest(BaseModel):
    """
    聊天请求模型
    
    Attributes:
        message: 用户输入的消息内容
        session_id: 会话 ID，用于多会话隔离（默认为 "default"）
        research_mode: 可选的研究模式覆盖（True=强制研究，False=强制对话，None=自动判断）
    """
    message: str
    session_id: str = "default"
    research_mode: Optional[bool] = None

class ChatResponse(BaseModel):
    """
    聊天响应模型
    
    Attributes:
        response: 助手的回复内容
        session_id: 会话 ID
        tokens_used: 本次对话消耗的 Token 数量
        research_used: 是否使用了研究模式
    """
    response: str
    session_id: str
    tokens_used: int
    research_used: bool

@app.get("/")
async def root():
    """
    首页路由 - 返回前端聊天界面
    
    Returns:
        HTMLResponse: 前端聊天页面内容
    """
    index_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>个人研究助理Agent</h1><p>请确保 frontend/index.html 存在</p>")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    同步聊天接口
    
    处理用户消息，调用 Agent 工作流，返回响应。
    支持自动分类研究/对话模式，支持多会话隔离。
    
    Args:
        request: ChatRequest 对象
            - message: 用户输入消息
            - session_id: 会话ID（多会话隔离）
            - research_mode: 可选的模式覆盖
    
    Returns:
        ChatResponse: 包含回复内容、会话ID、Token消耗、是否使用研究模式
    """
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

# Vite 健康检查路由（处理浏览器/扩展的 @vite/client 请求）
@app.get("/@vite/{rest:path}")
async def vite_client(rest: str = ""):
    """处理 Vite 开发服务器的客户端请求"""
    return {"status": "ok"}

@app.get("/health")
async def health():
    """
    健康检查接口
    
    用于检查服务是否正常运行。
    
    Returns:
        dict: 包含状态信息 {"status": "ok"}
    """
    return {"status": "ok"}

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口（Server-Sent Events）
    
    支持实时推送研究步骤进度，提供更好的用户体验。
    使用 SSE（Server-Sent Events）协议，逐步返回步骤信息和最终结果。
    
    Args:
        request: ChatRequest 对象
            - message: 用户输入消息
            - session_id: 会话ID（多会话隔离）
            - research_mode: 可选的模式覆盖
    
    Returns:
        StreamingResponse: 流式响应，包含步骤进度和最终结果
    """
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
        """
        生成流式响应数据
        
        迭代执行 Agent 工作流，实时推送步骤进度，并在最后返回最终结果。
        
        Yields:
            str: SSE 格式的数据流（data: {...}\n\n）
        """
        final_state = None
        step_count = 0
        
        # 迭代执行 Agent 工作流
        for output in agent_app.stream(state, config=config):
            for node_name, node_output in output.items():
                final_state = node_output
                
                # 检测步骤更新，推送进度
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
    """
    应用启动入口
    
    使用 uvicorn 启动 FastAPI 服务。
    
    运行方式：
        python main.py
    
    服务地址：
        http://localhost:8000
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)