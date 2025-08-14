#!/usr/bin/env python3
"""
工作流管理后端API

提供工作流执行、MCP服务管理、实时状态监控等功能的REST API
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# 导入MCP服务管理器
from MCP.service_manager import MCPServiceManager, ModelService, ServiceStatus

# 导入工作流引擎
from workflow.engine import WorkflowEngine
from workflow.models import WorkflowDefinition, WorkflowInstance, WorkflowStep, StepStatus

app = FastAPI(
    title="MCP工作流管理系统",
    description="智能体工作流管理、MCP服务控制、实时监控API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局变量
mcp_manager: Optional[MCPServiceManager] = None
workflow_engine: Optional[WorkflowEngine] = None
active_connections: List[WebSocket] = []

# Pydantic模型
class MCPServiceRequest(BaseModel):
    service_name: str
    tool_name: str
    arguments: Dict[str, Any]

class WorkflowStartRequest(BaseModel):
    workflow_name: str
    parameters: Dict[str, Any]

class ServiceControlRequest(BaseModel):
    service_name: str
    action: str  # start, stop, restart

class WorkflowStepUpdate(BaseModel):
    step_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 初始化函数
async def initialize_system():
    """初始化系统"""
    global mcp_manager, workflow_engine
    
    try:
        # 初始化MCP服务管理器
        mcp_manager = MCPServiceManager()
        print("✅ MCP服务管理器初始化成功")
        
        # 初始化工作流引擎
        workflow_engine = WorkflowEngine(mcp_manager)
        print("✅ 工作流引擎初始化成功")
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await initialize_system()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# WebSocket端点
@app.websocket("/ws/workflow")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理WebSocket消息
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# MCP服务管理API
@app.get("/api/mcp/services")
async def get_mcp_services():
    """获取所有MCP服务状态"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP管理器未初始化")
    
    services = []
    for name, service in mcp_manager.services.items():
        services.append({
            "name": name,
            "display_name": service.display_name,
            "status": service.status.value,
            "conda_env": service.conda_env,
            "host_path": service.host_path,
            "port": service.port,
            "error_message": service.error_message,
            "pid": service.process.pid if service.process else None
        })
    
    return {"services": services}

@app.post("/api/mcp/services/start")
async def start_mcp_service(request: ServiceControlRequest):
    """启动MCP服务"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP管理器未初始化")
    
    try:
        if request.action == "start":
            result = await mcp_manager._start_service(request.service_name)
            return {"success": True, "message": f"服务 {request.service_name} 启动成功"}
        elif request.action == "stop":
            result = await mcp_manager._stop_service(request.service_name)
            return {"success": True, "message": f"服务 {request.service_name} 停止成功"}
        elif request.action == "restart":
            await mcp_manager._stop_service(request.service_name)
            result = await mcp_manager._start_service(request.service_name)
            return {"success": True, "message": f"服务 {request.service_name} 重启成功"}
        else:
            raise HTTPException(status_code=400, detail="不支持的操作")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")

@app.post("/api/mcp/services/start-all")
async def start_all_mcp_services():
    """启动所有MCP服务"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP管理器未初始化")
    
    try:
        result = await mcp_manager._start_all_services(parallel=True)
        return {"success": True, "message": "所有服务启动成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@app.post("/api/mcp/services/stop-all")
async def stop_all_mcp_services():
    """停止所有MCP服务"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP管理器未初始化")
    
    try:
        result = await mcp_manager._stop_all_services()
        return {"success": True, "message": "所有服务停止成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")

@app.post("/api/mcp/call")
async def call_mcp_service(request: MCPServiceRequest):
    """调用MCP服务工具"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP管理器未初始化")
    
    try:
        # 检查服务是否运行
        service = mcp_manager.services.get(request.service_name)
        if not service:
            raise HTTPException(status_code=404, detail=f"服务 {request.service_name} 不存在")
        
        if service.status != ServiceStatus.RUNNING:
            raise HTTPException(status_code=400, detail=f"服务 {request.service_name} 未运行")
        
        # 模拟MCP调用（实际应该调用真实的MCP服务）
        result = {
            "success": True,
            "service": request.service_name,
            "tool": request.tool_name,
            "arguments": request.arguments,
            "result": f"模拟{request.service_name}服务{request.tool_name}工具执行结果",
            "timestamp": datetime.now().isoformat(),
            "execution_time": 1.5
        }
        
        # 广播到WebSocket
        await manager.broadcast(json.dumps({
            "type": "mcp_call_result",
            "data": result
        }))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用失败: {str(e)}")

# 工作流管理API
@app.get("/api/workflows")
async def get_workflows():
    """获取所有工作流定义"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="工作流引擎未初始化")
    
    workflows = workflow_engine.get_workflow_definitions()
    return {"workflows": workflows}

@app.get("/api/workflows/instances")
async def get_workflow_instances():
    """获取所有工作流实例"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="工作流引擎未初始化")
    
    instances = workflow_engine.get_workflow_instances()
    return {"instances": instances}

@app.post("/api/workflows/start")
async def start_workflow(request: WorkflowStartRequest, background_tasks: BackgroundTasks):
    """启动工作流"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="工作流引擎未初始化")
    
    try:
        # 启动工作流
        instance_id = workflow_engine.start_workflow(request.workflow_name, request.parameters)
        
        # 在后台执行工作流
        background_tasks.add_task(workflow_engine.execute_workflow_background, instance_id)
        
        return {
            "success": True,
            "instance_id": instance_id,
            "message": f"工作流 {request.workflow_name} 启动成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@app.get("/api/workflows/instances/{instance_id}")
async def get_workflow_instance(instance_id: str):
    """获取工作流实例详情"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="工作流引擎未初始化")
    
    instance = workflow_engine.get_workflow_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="工作流实例不存在")
    
    return {"instance": instance}

@app.post("/api/workflows/instances/{instance_id}/cancel")
async def cancel_workflow(instance_id: str):
    """取消工作流实例"""
    if not workflow_engine:
        raise HTTPException(status_code=500, detail="工作流引擎未初始化")
    
    try:
        success = workflow_engine.cancel_workflow(instance_id)
        if success:
            return {"success": True, "message": "工作流取消成功"}
        else:
            raise HTTPException(status_code=400, detail="无法取消已完成的工作流")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")

# 实时监控API
@app.get("/api/monitor/status")
async def get_system_status():
    """获取系统状态"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP管理器未初始化")
    
    # 统计服务状态
    service_stats = {
        "total": len(mcp_manager.services),
        "running": 0,
        "stopped": 0,
        "error": 0
    }
    
    for service in mcp_manager.services.values():
        if service.status == ServiceStatus.RUNNING:
            service_stats["running"] += 1
        elif service.status == ServiceStatus.STOPPED:
            service_stats["stopped"] += 1
        else:
            service_stats["error"] += 1
    
    # 工作流统计
    workflow_stats = {
        "total": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }
    
    if workflow_engine:
        instances = workflow_engine.get_workflow_instances()
        workflow_stats["total"] = len(instances)
        for instance in instances:
            if instance.status == "running":
                workflow_stats["running"] += 1
            elif instance.status == "completed":
                workflow_stats["completed"] += 1
            elif instance.status == "failed":
                workflow_stats["failed"] += 1
    
    return {
        "timestamp": datetime.now().isoformat(),
        "service_stats": service_stats,
        "workflow_stats": workflow_stats,
        "active_connections": len(manager.active_connections)
    }

@app.get("/api/monitor/logs")
async def get_system_logs(limit: int = 100):
    """获取系统日志"""
    # 这里应该实现真实的日志获取逻辑
    logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "系统运行正常",
            "source": "system"
        }
    ]
    
    return {"logs": logs}

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_manager": mcp_manager is not None,
        "workflow_engine": workflow_engine is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
