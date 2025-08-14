"""
MCP Router

Intelligent routing system for distributing tool execution requests
to appropriate model adapters. Integrates with LangGraph for workflow
orchestration.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph

from .base_model import BaseModel, ModelResult, ModelStatus
from .environment_manager import environment_manager
from .tool_registry import tool_registry, ToolMetadata

logger = logging.getLogger(__name__)


class MCPRouter:
    """
    Intelligent router for MCP tool execution.
    
    Routes tool execution requests to appropriate model adapters based on
    tool metadata, model availability, and system load.
    """
    
    def __init__(self):
        self._models: Dict[str, BaseModel] = {}
        self._active_executions: Dict[str, str] = {}  # execution_id -> model_name
        self._execution_queue: List[Dict[str, Any]] = []
        self._max_concurrent_executions = 3
    
    def register_model(self, model: BaseModel):
        """
        Register a model adapter with the router.
        
        Args:
            model: Model adapter instance
        """
        self._models[model.name] = model
        logger.info(f"Registered model '{model.name}' with router")
    
    def unregister_model(self, model_name: str) -> bool:
        """
        Unregister a model adapter.
        
        Args:
            model_name: Name of the model to unregister
            
        Returns:
            True if model was unregistered, False if not found
        """
        if model_name not in self._models:
            return False
        
        del self._models[model_name]
        
        # Remove any queued executions for this model
        self._execution_queue = [
            exec_req for exec_req in self._execution_queue
            if exec_req.get("model_name") != model_name
        ]
        
        logger.info(f"Unregistered model '{model_name}' from router")
        return True
    
    def list_models(self) -> List[str]:
        """List all registered models."""
        return list(self._models.keys())
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        execution_id: Optional[str] = None,
        priority: int = 0
    ) -> ModelResult:
        """
        Execute a tool through the appropriate model adapter.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            execution_id: Optional execution ID
            priority: Execution priority (higher = more urgent)
            
        Returns:
            ModelResult with execution results
        """
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        
        # Get tool metadata
        tool_metadata = tool_registry.get_tool(tool_name)
        if not tool_metadata:
            return self._create_error_result(
                tool_name,
                execution_id,
                f"Tool '{tool_name}' not found in registry"
            )
        
        # Get model adapter
        model_name = tool_metadata.model_name
        if model_name not in self._models:
            return self._create_error_result(
                tool_name,
                execution_id,
                f"Model '{model_name}' not available"
            )
        
        model = self._models[model_name]
        
        # Validate parameters
        validation_error = self._validate_parameters(tool_metadata, parameters)
        if validation_error:
            return self._create_error_result(tool_name, execution_id, validation_error)
        
        # Check if we need to queue the execution
        if len(self._active_executions) >= self._max_concurrent_executions:
            return await self._queue_execution(
                tool_name, parameters, execution_id, priority, model_name
            )
        
        # Execute directly
        return await self._execute_directly(model, tool_name, parameters, execution_id)
    
    def _validate_parameters(
        self, 
        tool_metadata: ToolMetadata, 
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """Validate tool parameters against metadata."""
        required_params = []
        for param_name, param_info in tool_metadata.parameters.items():
            if isinstance(param_info, dict) and param_info.get("required", False):
                required_params.append(param_name)
        
        # Check required parameters
        missing_params = [p for p in required_params if p not in parameters]
        if missing_params:
            return f"Missing required parameters: {missing_params}"
        
        return None
    
    async def _execute_directly(
        self,
        model: BaseModel,
        tool_name: str,
        parameters: Dict[str, Any],
        execution_id: str
    ) -> ModelResult:
        """Execute tool directly without queueing."""
        # Track active execution
        self._active_executions[execution_id] = model.name
        
        try:
            # Validate model environment
            if not await model.validate_environment():
                return self._create_error_result(
                    tool_name,
                    execution_id,
                    f"Model '{model.name}' environment validation failed"
                )
            
            logger.info(f"Executing tool '{tool_name}' on model '{model.name}'")
            
            # Execute tool
            result = await model.execute_tool(tool_name, parameters, execution_id)
            
            logger.info(f"Tool '{tool_name}' execution completed with status: {result.status}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return self._create_error_result(
                tool_name,
                execution_id,
                f"Execution error: {str(e)}"
            )
        
        finally:
            # Remove from active executions
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
            
            # Process queue
            await self._process_queue()
    
    async def _queue_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        execution_id: str,
        priority: int,
        model_name: str
    ) -> ModelResult:
        """Queue an execution for later processing."""
        execution_request = {
            "tool_name": tool_name,
            "parameters": parameters,
            "execution_id": execution_id,
            "priority": priority,
            "model_name": model_name,
            "future": asyncio.Future()
        }
        
        # Insert based on priority
        insert_index = 0
        for i, req in enumerate(self._execution_queue):
            if req["priority"] < priority:
                insert_index = i
                break
            insert_index = i + 1
        
        self._execution_queue.insert(insert_index, execution_request)
        
        logger.info(f"Queued execution '{execution_id}' (position: {insert_index})")
        
        # Return future result
        return await execution_request["future"]
    
    async def _process_queue(self):
        """Process queued executions if capacity is available."""
        while (
            self._execution_queue and 
            len(self._active_executions) < self._max_concurrent_executions
        ):
            # Get next execution
            execution_request = self._execution_queue.pop(0)
            
            model_name = execution_request["model_name"]
            if model_name not in self._models:
                # Model no longer available
                execution_request["future"].set_result(
                    self._create_error_result(
                        execution_request["tool_name"],
                        execution_request["execution_id"],
                        f"Model '{model_name}' no longer available"
                    )
                )
                continue
            
            # Execute asynchronously
            asyncio.create_task(self._execute_queued_request(execution_request))
    
    async def _execute_queued_request(self, execution_request: Dict[str, Any]):
        """Execute a queued request."""
        model = self._models[execution_request["model_name"]]
        
        try:
            result = await self._execute_directly(
                model,
                execution_request["tool_name"],
                execution_request["parameters"],
                execution_request["execution_id"]
            )
            execution_request["future"].set_result(result)
        except Exception as e:
            error_result = self._create_error_result(
                execution_request["tool_name"],
                execution_request["execution_id"],
                f"Queued execution error: {str(e)}"
            )
            execution_request["future"].set_result(error_result)
    
    def _create_error_result(
        self, 
        tool_name: str, 
        execution_id: str, 
        error_message: str
    ) -> ModelResult:
        """Create a standardized error result."""
        from datetime import datetime
        
        return ModelResult(
            model_name="router",
            tool_name=tool_name,
            status=ModelStatus.FAILED,
            execution_id=execution_id,
            start_time=datetime.now(),
            end_time=datetime.now(),
            error=error_message
        )
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific execution."""
        # Check active executions
        if execution_id in self._active_executions:
            return {
                "execution_id": execution_id,
                "status": "running",
                "model_name": self._active_executions[execution_id]
            }
        
        # Check queue
        for i, req in enumerate(self._execution_queue):
            if req["execution_id"] == execution_id:
                return {
                    "execution_id": execution_id,
                    "status": "queued",
                    "position": i,
                    "model_name": req["model_name"]
                }
        
        return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a queued or running execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancelled, False if not found or cannot be cancelled
        """
        # Check queue first
        for i, req in enumerate(self._execution_queue):
            if req["execution_id"] == execution_id:
                # Remove from queue
                cancelled_req = self._execution_queue.pop(i)
                cancelled_req["future"].set_result(
                    self._create_error_result(
                        cancelled_req["tool_name"],
                        execution_id,
                        "Execution cancelled by user"
                    )
                )
                logger.info(f"Cancelled queued execution '{execution_id}'")
                return True
        
        # Cannot cancel running executions directly
        # (would require model-specific cancellation logic)
        return False
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "registered_models": len(self._models),
            "active_executions": len(self._active_executions),
            "queued_executions": len(self._execution_queue),
            "max_concurrent_executions": self._max_concurrent_executions,
            "model_names": list(self._models.keys())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered models."""
        health_results = {}
        
        for model_name, model in self._models.items():
            try:
                is_healthy = await model.validate_environment()
                health_results[model_name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "environment": model.conda_environment,
                    "available_tools": len(model.available_tools)
                }
            except Exception as e:
                health_results[model_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "router_status": "healthy",
            "models": health_results,
            "stats": self.get_router_stats()
        }


# Global router instance
mcp_router = MCPRouter()