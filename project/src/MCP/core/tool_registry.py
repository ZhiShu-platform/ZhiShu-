"""
Tool Registry for MCP

Manages registration, discovery, and metadata for all model tools.
Provides a centralized registry for tools from different models.
"""

import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""
    
    name: str
    description: str
    model_name: str
    category: str
    
    # Function/class information
    callable_obj: Union[Callable, Type[BaseTool]]
    parameters: Dict[str, Any]
    return_type: Optional[str] = None
    
    # Execution requirements
    requires_environment: bool = True
    estimated_runtime: Optional[int] = None  # seconds
    memory_requirements: Optional[str] = None
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "model_name": self.model_name,
            "category": self.category,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "requires_environment": self.requires_environment,
            "estimated_runtime": self.estimated_runtime,
            "memory_requirements": self.memory_requirements,
            "tags": self.tags,
            "examples": self.examples,
            "version": self.version
        }


class ToolRegistry:
    """
    Central registry for all MCP tools.
    
    Manages tool registration, discovery, and metadata across different models.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._categories: Dict[str, List[str]] = {}
        self._models: Dict[str, List[str]] = {}
    
    def register_tool(
        self,
        name: str,
        callable_obj: Union[Callable, Type[BaseTool]],
        model_name: str,
        category: str,
        description: str = "",
        **metadata_kwargs
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            name: Unique tool name
            callable_obj: Function or BaseTool class
            model_name: Name of the model providing this tool
            category: Tool category (e.g., "simulation", "analysis")
            description: Tool description
            **metadata_kwargs: Additional metadata
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")
        
        # Extract parameters from callable
        parameters = self._extract_parameters(callable_obj)
        
        # Create metadata
        metadata = ToolMetadata(
            name=name,
            description=description or self._extract_description(callable_obj),
            model_name=model_name,
            category=category,
            callable_obj=callable_obj,
            parameters=parameters,
            **metadata_kwargs
        )
        
        # Register tool
        self._tools[name] = metadata
        
        # Update category index
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        # Update model index
        if model_name not in self._models:
            self._models[model_name] = []
        if name not in self._models[model_name]:
            self._models[model_name].append(name)
        
        logger.info(f"Registered tool '{name}' from model '{model_name}'")
    
    def _extract_parameters(self, callable_obj: Union[Callable, Type[BaseTool]]) -> Dict[str, Any]:
        """Extract parameter information from a callable."""
        parameters = {}
        
        try:
            if isinstance(callable_obj, type) and issubclass(callable_obj, BaseTool):
                # BaseTool subclass - extract from args_schema if available
                if hasattr(callable_obj, 'args_schema') and callable_obj.args_schema:
                    schema = callable_obj.args_schema.schema()
                    parameters = schema.get('properties', {})
            else:
                # Regular function - use inspect
                sig = inspect.signature(callable_obj)
                for param_name, param in sig.parameters.items():
                    param_info = {
                        "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                        "required": param.default == inspect.Parameter.empty,
                        "default": param.default if param.default != inspect.Parameter.empty else None
                    }
                    parameters[param_name] = param_info
        
        except Exception as e:
            logger.warning(f"Could not extract parameters: {e}")
        
        return parameters
    
    def _extract_description(self, callable_obj: Union[Callable, Type[BaseTool]]) -> str:
        """Extract description from a callable."""
        try:
            if isinstance(callable_obj, type) and issubclass(callable_obj, BaseTool):
                return getattr(callable_obj, 'description', '')
            else:
                return inspect.getdoc(callable_obj) or ""
        except Exception:
            return ""
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        return self._tools.get(name)
    
    def list_tools(
        self,
        model_name: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ToolMetadata]:
        """
        List tools with optional filtering.
        
        Args:
            model_name: Filter by model name
            category: Filter by category
            tags: Filter by tags (tools must have ALL specified tags)
            
        Returns:
            List of matching tool metadata
        """
        tools = list(self._tools.values())
        
        # Filter by model
        if model_name:
            tools = [t for t in tools if t.model_name == model_name]
        
        # Filter by category
        if category:
            tools = [t for t in tools if t.category == category]
        
        # Filter by tags
        if tags:
            tools = [t for t in tools if all(tag in t.tags for tag in tags)]
        
        return tools
    
    def list_categories(self) -> List[str]:
        """List all available categories."""
        return list(self._categories.keys())
    
    def list_models(self) -> List[str]:
        """List all models that have registered tools."""
        return list(self._models.keys())
    
    def get_tools_by_category(self, category: str) -> List[ToolMetadata]:
        """Get all tools in a specific category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_tools_by_model(self, model_name: str) -> List[ToolMetadata]:
        """Get all tools from a specific model."""
        tool_names = self._models.get(model_name, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def search_tools(self, query: str) -> List[ToolMetadata]:
        """
        Search tools by name, description, or tags.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        matches = []
        
        for tool in self._tools.values():
            # Check name
            if query_lower in tool.name.lower():
                matches.append(tool)
                continue
            
            # Check description
            if query_lower in tool.description.lower():
                matches.append(tool)
                continue
            
            # Check tags
            if any(query_lower in tag.lower() for tag in tool.tags):
                matches.append(tool)
                continue
        
        return matches
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name not in self._tools:
            return False
        
        tool = self._tools[name]
        
        # Remove from main registry
        del self._tools[name]
        
        # Remove from category index
        if tool.category in self._categories:
            if name in self._categories[tool.category]:
                self._categories[tool.category].remove(name)
            if not self._categories[tool.category]:
                del self._categories[tool.category]
        
        # Remove from model index
        if tool.model_name in self._models:
            if name in self._models[tool.model_name]:
                self._models[tool.model_name].remove(name)
            if not self._models[tool.model_name]:
                del self._models[tool.model_name]
        
        logger.info(f"Unregistered tool '{name}'")
        return True
    
    def unregister_model(self, model_name: str) -> int:
        """
        Unregister all tools from a specific model.
        
        Args:
            model_name: Model name
            
        Returns:
            Number of tools unregistered
        """
        if model_name not in self._models:
            return 0
        
        tool_names = self._models[model_name].copy()
        count = 0
        
        for tool_name in tool_names:
            if self.unregister_tool(tool_name):
                count += 1
        
        logger.info(f"Unregistered {count} tools from model '{model_name}'")
        return count
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry."""
        return {
            "total_tools": len(self._tools),
            "total_categories": len(self._categories),
            "total_models": len(self._models),
            "tools_by_category": {cat: len(tools) for cat, tools in self._categories.items()},
            "tools_by_model": {model: len(tools) for model, tools in self._models.items()}
        }
    
    def export_registry(self) -> Dict[str, Any]:
        """Export the entire registry as a dictionary."""
        return {
            "tools": {name: tool.to_dict() for name, tool in self._tools.items()},
            "categories": self._categories,
            "models": self._models,
            "stats": self.get_registry_stats()
        }
    
    def clear(self):
        """Clear the entire registry."""
        self._tools.clear()
        self._categories.clear()
        self._models.clear()
        logger.info("Cleared tool registry")


# Global tool registry instance
tool_registry = ToolRegistry()