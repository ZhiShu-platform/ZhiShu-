#!/usr/bin/env python3
"""
Filesystem MCP Server with configurable access control.

This server provides secure file operations with configurable access control
for the emergency management system.
"""

import asyncio
import logging
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

# from ..core.base_model import BaseMCPModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilesystemServer:
    """Secure Filesystem MCP Server with access control."""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None):
        self.server = Server("filesystem-server")
        
        # Configure allowed paths for security
        if allowed_paths is None:
            allowed_paths = [
                "/data/Tiaozhanbei",  # Model data directory
                "/tmp/emergency_management",  # Temporary files
                "/var/log/emergency_management",  # Log files
                os.path.expanduser("~/emergency_data")  # User data
            ]
        
        self.allowed_paths: Set[Path] = {Path(p).resolve() for p in allowed_paths}
        self.readonly_paths: Set[Path] = {
            Path("/data/Tiaozhanbei").resolve()  # Model data is read-only
        }
        
        # Ensure temp directory exists
        temp_path = Path("/tmp/emergency_management")
        temp_path.mkdir(parents=True, exist_ok=True)
        
        self._setup_tools()
        self._setup_resources()
    
    def _is_path_allowed(self, path: Path, write_access: bool = False) -> bool:
        """Check if path access is allowed."""
        try:
            resolved_path = path.resolve()
            
            # Check if path is within allowed directories
            for allowed_path in self.allowed_paths:
                try:
                    resolved_path.relative_to(allowed_path)
                    # Path is allowed, check write permissions
                    if write_access:
                        for readonly_path in self.readonly_paths:
                            try:
                                resolved_path.relative_to(readonly_path)
                                return False  # Write not allowed in readonly path
                            except ValueError:
                                continue
                    return True
                except ValueError:
                    continue
            
            return False
        except (OSError, ValueError):
            return False
    
    def _setup_tools(self):
        """Setup filesystem tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="read_file",
                    description="Read contents of a file (with access control)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to read"
                            },
                            "encoding": {
                                "type": "string",
                                "default": "utf-8",
                                "description": "File encoding"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_file",
                    description="Write content to a file (with access control)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            },
                            "encoding": {
                                "type": "string",
                                "default": "utf-8",
                                "description": "File encoding"
                            }
                        },
                        "required": ["path", "content"]
                    }
                ),
                Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the directory to list"
                            },
                            "recursive": {
                                "type": "boolean",
                                "default": False,
                                "description": "Whether to list recursively"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="create_directory",
                    description="Create a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the directory to create"
                            },
                            "parents": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to create parent directories"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="delete_file",
                    description="Delete a file (with access control)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to delete"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="file_info",
                    description="Get information about a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to get information about"
                            }
                        },
                        "required": ["path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "read_file":
                    result = await self._read_file(arguments)
                elif name == "write_file":
                    result = await self._write_file(arguments)
                elif name == "list_directory":
                    result = await self._list_directory(arguments)
                elif name == "create_directory":
                    result = await self._create_directory(arguments)
                elif name == "delete_file":
                    result = await self._delete_file(arguments)
                elif name == "file_info":
                    result = await self._file_info(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _setup_resources(self):
        """Setup filesystem resources."""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            resources = []
            
            for allowed_path in self.allowed_paths:
                if allowed_path.exists():
                    resources.append(Resource(
                        uri=f"file://{allowed_path}",
                        name=f"Directory: {allowed_path.name}",
                        description=f"Accessible directory: {allowed_path}",
                        mimeType="inode/directory"
                    ))
            
            return resources
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file with access control."""
        path = Path(params["path"])
        encoding = params.get("encoding", "utf-8")
        
        if not self._is_path_allowed(path, write_access=False):
            raise PermissionError(f"Access denied to path: {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise IsADirectoryError(f"Path is not a file: {path}")
        
        try:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            
            return {
                "path": str(path),
                "content": content,
                "size": path.stat().st_size,
                "encoding": encoding,
                "status": "success"
            }
        except UnicodeDecodeError:
            # Try binary read for non-text files
            with open(path, "rb") as f:
                content = f.read()
            
            return {
                "path": str(path),
                "content": f"<binary file, {len(content)} bytes>",
                "size": len(content),
                "encoding": "binary",
                "status": "binary_file"
            }
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file with access control."""
        path = Path(params["path"])
        content = params["content"]
        encoding = params.get("encoding", "utf-8")
        
        if not self._is_path_allowed(path, write_access=True):
            raise PermissionError(f"Write access denied to path: {path}")
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        
        return {
            "path": str(path),
            "bytes_written": len(content.encode(encoding)),
            "encoding": encoding,
            "status": "success"
        }
    
    async def _list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        path = Path(params["path"])
        recursive = params.get("recursive", False)
        
        if not self._is_path_allowed(path, write_access=False):
            raise PermissionError(f"Access denied to path: {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")
        
        items = []
        
        if recursive:
            for item in path.rglob("*"):
                if self._is_path_allowed(item, write_access=False):
                    items.append(self._get_file_info(item))
        else:
            for item in path.iterdir():
                if self._is_path_allowed(item, write_access=False):
                    items.append(self._get_file_info(item))
        
        return {
            "path": str(path),
            "items": items,
            "count": len(items),
            "recursive": recursive,
            "status": "success"
        }
    
    async def _create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a directory."""
        path = Path(params["path"])
        parents = params.get("parents", True)
        
        if not self._is_path_allowed(path, write_access=True):
            raise PermissionError(f"Write access denied to path: {path}")
        
        path.mkdir(parents=parents, exist_ok=True)
        
        return {
            "path": str(path),
            "created": True,
            "status": "success"
        }
    
    async def _delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file."""
        path = Path(params["path"])
        
        if not self._is_path_allowed(path, write_access=True):
            raise PermissionError(f"Delete access denied to path: {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()  # Only removes empty directories
        else:
            raise OSError(f"Cannot delete: {path}")
        
        return {
            "path": str(path),
            "deleted": True,
            "status": "success"
        }
    
    async def _file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file information."""
        path = Path(params["path"])
        
        if not self._is_path_allowed(path, write_access=False):
            raise PermissionError(f"Access denied to path: {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        return self._get_file_info(path)
    
    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get detailed information about a file or directory."""
        try:
            stat_info = path.stat()
            
            return {
                "path": str(path),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size": stat_info.st_size,
                "modified": stat_info.st_mtime,
                "permissions": stat.filemode(stat_info.st_mode),
                "owner_uid": stat_info.st_uid,
                "group_gid": stat_info.st_gid,
                "readable": os.access(path, os.R_OK),
                "writable": os.access(path, os.W_OK) and self._is_path_allowed(path, write_access=True),
                "executable": os.access(path, os.X_OK)
            }
        except OSError as e:
            return {
                "path": str(path),
                "error": str(e),
                "accessible": False
            }


async def main():
    """Run the Filesystem MCP server."""
    # Configure allowed paths from environment or use defaults
    allowed_paths = os.getenv("FILESYSTEM_ALLOWED_PATHS", "").split(",")
    if not allowed_paths or allowed_paths == [""]:
        allowed_paths = None
    
    server_instance = FilesystemServer(allowed_paths)
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="filesystem-server",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())