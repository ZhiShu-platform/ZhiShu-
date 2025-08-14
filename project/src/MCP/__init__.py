"""
Model Control Plane (MCP) for Emergency Management System.

This module provides a unified interface for managing and executing various
disaster modeling tools including Climada, Lisflood, and other scientific models.

Key Components:
- Core: Base classes and utilities
- Adapters: Model-specific adapters
- Tools: LangGraph-compatible tool definitions
- Router: Intelligent routing system
"""

from .core.base_model import BaseModel, ModelResult
from .core.environment_manager import EnvironmentManager
from .core.router import MCPRouter
from .core.tool_registry import ToolRegistry
from .client import MCPClient

__version__ = "1.0.0"
__author__ = "Emergency Management Team"

__all__ = [
    "BaseModel",
    "ModelResult", 
    "EnvironmentManager",
    "MCPRouter",
    "ToolRegistry",
    "MCPClient"
]