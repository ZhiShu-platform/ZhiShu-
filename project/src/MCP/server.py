"""
MCP Server

FastAPI-based server for the Model Control Plane.
Provides REST API endpoints for model management and execution.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.router import mcp_router
from .core.tool_registry import tool_registry
from .core.environment_manager import environment_manager
from .adapters.climada_adapter import ClimadaAdapter
from .adapters.lisflood_adapter import LisfloodAdapter
from .tools.climada_tools import get_climada_tools
from .tools.lisflood_tools import get_lisflood_tools

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Model Control Plane (MCP) Server",
    description="REST API for managing and executing scientific models",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    priority: Optional[int] = 0

class ToolExecutionResponse(BaseModel):
    execution_id: str
    status: str
    message: str

class ModelRegistrationRequest(BaseModel):
    model_name: str
    model_path: Optional[str] = None
    conda_environment: Optional[str] = None

# Global state
_models_initialized = False

async def initialize_models():
    """Initialize model adapters and register tools."""
    global _models_initialized
    
    if _models_initialized:
        return
    
    try:
        # Initialize Climada adapter
        climada_adapter = ClimadaAdapter()
        mcp_router.register_model(climada_adapter)
        
        # Register Climada tools
        climada_tools = get_climada_tools()
        for tool_name, tool_info in climada_tools.items():
            tool_registry.register_tool(
                name=tool_name,
                callable_obj=tool_info["class"],
                model_name="climada",
                category=tool_info["category"],
                description=tool_info["description"],
                estimated_runtime=tool_info.get("estimated_runtime"),
                memory_requirements=tool_info.get("memory_requirements"),
                tags=tool_info.get("tags", []),
                examples=tool_info.get("examples", [])
            )
        
        # Initialize Lisflood adapter
        lisflood_adapter = LisfloodAdapter()
        mcp_router.register_model(lisflood_adapter)
        
        # Register Lisflood tools
        lisflood_tools = get_lisflood_tools()
        for tool_name, tool_info in lisflood_tools.items():
            tool_registry.register_tool(
                name=tool_name,
                callable_obj=tool_info["class"],
                model_name="lisflood",
                category=tool_info["category"],
                description=tool_info["description"],
                estimated_runtime=tool_info.get("estimated_runtime"),
                memory_requirements=tool_info.get("memory_requirements"),
                tags=tool_info.get("tags", []),
                examples=tool_info.get("examples", [])
            )
        
        _models_initialized = True
        logger.info("MCP models initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        raise

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server."""
    await initialize_models()

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Model Control Plane (MCP) Server",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "tools": "/tools",
            "execute": "/execute",
            "status": "/status",
            "models": "/models",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        health_results = await mcp_router.health_check()
        env_list = await environment_manager.list_environments()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "router": health_results,
            "environments": len(env_list),
            "tools_registered": len(tool_registry.list_tools())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/tools")
async def list_tools(
    model_name: Optional[str] = None,
    category: Optional[str] = None
):
    """List available tools."""
    try:
        tools = tool_registry.list_tools(model_name=model_name, category=category)
        return {
            "tools": [tool.to_dict() for tool in tools],
            "total_count": len(tools),
            "filter_applied": {
                "model_name": model_name,
                "category": category
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return tool.to_dict()

@app.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(request: ToolExecutionRequest, background_tasks: BackgroundTasks):
    """Execute a tool asynchronously."""
    try:
        # Start execution in background
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.tool_name}"
        
        # Execute tool through router
        result = await mcp_router.execute_tool(
            tool_name=request.tool_name,
            parameters=request.parameters,
            execution_id=execution_id,
            priority=request.priority
        )
        
        return ToolExecutionResponse(
            execution_id=execution_id,
            status=result.status.value,
            message=f"Tool '{request.tool_name}' executed with status: {result.status.value}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@app.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get the status of a specific execution."""
    try:
        status = await mcp_router.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.delete("/executions/{execution_id}")
async def cancel_execution(execution_id: str):
    """Cancel a queued or running execution."""
    try:
        cancelled = await mcp_router.cancel_execution(execution_id)
        if not cancelled:
            raise HTTPException(
                status_code=404, 
                detail=f"Execution '{execution_id}' not found or cannot be cancelled"
            )
        
        return {"message": f"Execution '{execution_id}' cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")

@app.get("/models")
async def list_models():
    """List registered models."""
    try:
        models = mcp_router.list_models()
        model_stats = {}
        
        for model_name in models:
            tools = tool_registry.get_tools_by_model(model_name)
            model_stats[model_name] = {
                "tools_count": len(tools),
                "categories": list(set(tool.category for tool in tools))
            }
        
        return {
            "models": model_stats,
            "total_models": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.get("/categories")
async def list_categories():
    """List available tool categories."""
    try:
        categories = tool_registry.list_categories()
        category_stats = {}
        
        for category in categories:
            tools = tool_registry.get_tools_by_category(category)
            category_stats[category] = {
                "tools_count": len(tools),
                "models": list(set(tool.model_name for tool in tools))
            }
        
        return {
            "categories": category_stats,
            "total_categories": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")

@app.get("/environments")
async def list_environments():
    """List available Conda environments."""
    try:
        environments = await environment_manager.list_environments()
        return {
            "environments": environments,
            "total_count": len(environments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list environments: {str(e)}")

@app.get("/stats")
async def get_server_stats():
    """Get comprehensive server statistics."""
    try:
        router_stats = mcp_router.get_router_stats()
        registry_stats = tool_registry.get_registry_stats()
        environments = await environment_manager.list_environments()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "router": router_stats,
            "registry": registry_stats,
            "environments": len(environments),
            "server_status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)