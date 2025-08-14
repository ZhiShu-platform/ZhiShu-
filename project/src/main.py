# -*- coding: utf-8 -*-
"""Main entry point for the Emergency Management System.

This module provides both direct FastAPI server execution and LangGraph dev compatibility.
The system can be started in two ways:
1. Using LangGraph CLI: `langgraph dev` (recommended for development)
2. Direct execution: `python src/main.py` (alternative method)
"""

import sys
import os
import asyncio
import uvicorn
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime

# --- Import dotenv and load environment variables ---
from dotenv import load_dotenv
load_dotenv()
# ----------------------------------------

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Import Langfuse and create a global instance ---
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

try:
    langfuse_client = Langfuse(
        public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
        host=os.environ.get("LANGFUSE_HOST")
    )
    langfuse_handler = CallbackHandler()
    print("Langfuse client initialized successfully.")
except Exception as e:
    print(f"⚠️ Langfuse client initialization failed: {e}. Running without tracing.")
    langfuse_handler = None
    langfuse_client = None
# -------------------------------------------

# 从 agent.graph 导入我们的 LangGraph 实例和处理函数
from src.agent.graph import process_emergency_event, get_system_health
from src.core.config import config
from src.core.natural_language_handler import natural_language_handler


# --- Pydantic model for request body validation ---
# 使用Pydantic模型来定义预期的请求体结构
class Content(BaseModel):
    user_prompt: str
    multimodal_data: Dict[str, Any]

class Location(BaseModel):
    latitude: float
    longitude: float
    region: str
    country_iso: str

class EmergencyInput(BaseModel):
    session_id: str
    user_id: str
    type: str = "user_prompt"
    content: Content
    location: Location

# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown tasks."""
    # Startup
    print("Emergency Management System starting up...")
    try:
        health_status = await get_system_health()
        print(f"System health check passed: {health_status['system_health']['overall_status']}")
    except Exception as e:
        print(f"⚠️ System health check warning: {e}")
    
    print("Emergency Management System ready!")
    yield
    
    # Shutdown
    print("Emergency Management System shutting down...")
    if langfuse_client:
        print("Flushing Langfuse events...")
        langfuse_client.flush()
        langfuse_client.shutdown()
        print("Langfuse client shut down.")


app = FastAPI(
    title=config.app_title,
    description=config.app_description,
    version=config.app_version,
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """提供系统信息的根端点。"""
    return {
        "message": "欢迎使用应急管理系统 API！",
        "version": config.app_version,
        "status": "operational",
        "endpoints": {
            "health": "/system_health",
            "process": "/process_emergency_event",
            "docs": "/docs"
        }
    }


# --- API Endpoints ---

@app.post("/process_emergency_event")
async def process_emergency_event_api(input_data: EmergencyInput) -> Dict[str, Any]:
    """
    Process an emergency event and get the final report, including a human-readable summary.
    """
    try:
        # Pydantic模型会自动进行验证，所以我们不需要手动检查。
        # FastAPI 会在验证失败时自动返回 422 错误。
        
        # 转换 Pydantic 模型为字典，以便传递给LangGraph
        input_dict = input_data.model_dump()
        result_state = await process_emergency_event(input_dict)
        
        final_report = result_state.get("final_report", {})
        human_readable_summary = result_state.get("human_readable_summary", "抱歉，无法生成摘要。")

        return {
            "final_report": final_report,
            "human_readable_summary": human_readable_summary
        }
            
    except Exception as e:
        # 捕获其他所有异常，并返回一个通用的500错误
        print(f"Emergency processing failed: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Emergency processing failed: {str(e)}")


@app.get("/system_health")
async def get_system_health_api():
    """Get overall system health status."""
    try:
        return await get_system_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/chat")
async def chat_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    自然语言对话端点 - 支持一般性的自然语言交流
    
    请求体格式：
    {
        "message": "用户消息",
        "session_id": "会话ID",
        "user_id": "用户ID",
        "context": {} // 可选上下文信息
    }
    """
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        user_id = request.get("user_id", "anonymous")
        context = request.get("context", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        # 使用自然语言处理器处理消息
        response = await natural_language_handler.process_natural_language(
            text=message,
            session_id=session_id,
            user_id=user_id,
            context=context
        )
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Chat processing failed: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str) -> Dict[str, Any]:
    """获取指定会话的对话历史"""
    try:
        if session_id in natural_language_handler.conversation_contexts:
            conv_context = natural_language_handler.conversation_contexts[session_id]
            return {
                "session_id": session_id,
                "user_id": conv_context.user_id,
                "total_messages": len(conv_context.conversation_history),
                "last_interaction": conv_context.last_interaction.isoformat(),
                "conversation_history": conv_context.conversation_history
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@app.get("/graph/info")
async def get_graph_info():
    """Get information about the graph structure."""
    return {
        "graph_type": "EmergencyManagementGraph",
        "nodes": [
            "input_processing",
            "threat_detection",
            "alert_generation",
            "agent_coordination",
            "response_execution",
            "damage_assessment",
            "reporting",
            "generate_human_readable_summary"
        ],
        "entry_point": "input_processing",
        "description": "Multi-agent emergency management workflow"
    }


def main():
    """Main function for direct execution."""
    print("Starting Emergency Management System directly...")
    print("For development, consider using: langgraph dev")
    print("API documentation will be available at: http://127.0.0.1:2024/docs")
    
    # Start the FastAPI server
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=2024,
        reload=True,
        log_level="info",
        reload_dirs=["src"]
    )


if __name__ == "__main__":
    main()
