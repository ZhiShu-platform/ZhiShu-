#!/usr/bin/env python3
"""
MCP服务管理器 - 统一管理所有模型服务
"""

import asyncio
import logging
import os
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
from mcp.server.models import InitializationOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class ModelService:
    """模型服务配置"""
    name: str
    display_name: str
    server_class: str
    module_path: str
    conda_env: str
    host_path: str
    port: Optional[int] = None
    status: ServiceStatus = ServiceStatus.STOPPED
    process: Optional[subprocess.Popen] = None
    error_message: Optional[str] = None


class MCPServiceManager:
    """MCP服务管理器"""
    
    def __init__(self):
        self.server = Server("mcp-service-manager")
        self.services: Dict[str, ModelService] = {}
        self.shared_dir = "/data/Tiaozhanbei/shared"
        self.base_dir = Path(__file__).parent.parent.parent
        
        # 确保共享目录存在
        Path(self.shared_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化所有模型服务
        self._initialize_services()
        self._setup_tools()
        self._setup_resources()
    
    def _initialize_services(self):
        """初始化所有模型服务配置"""
        self.services = {
            "nfdrs4": ModelService(
                name="nfdrs4",
                display_name="NFDRS4火灾风险评估服务",
                server_class="NFDRS4Server",
                module_path="MCP.servers.nfdrs4_server",
                conda_env="NFDRS4",
                host_path="/data/Tiaozhanbei/NFDRS4",
                port=8001
            ),
            "lisflood": ModelService(
                name="lisflood",
                display_name="LISFLOOD洪水建模服务",
                server_class="LisfloodServer",
                module_path="MCP.servers.lisflood_server",
                conda_env="lisflood",
                host_path="/data/Tiaozhanbei/Lisflood",
                port=8002
            ),
            "climada": ModelService(
                name="climada",
                display_name="CLIMADA气候风险评估服务",
                server_class="CliMadaService",
                module_path="MCP.servers.climada_server",
                conda_env="climada",
                host_path="/data/Tiaozhanbei/CLIMADA",
                port=8003
            ),
            "aurora": ModelService(
                name="aurora",
                display_name="Aurora天气预测服务",
                server_class="AuroraServer",
                module_path="MCP.servers.aurora_server",
                conda_env="aurora",
                host_path="/data/Tiaozhanbei/Aurora",
                port=8004
            ),
            "postgis": ModelService(
                name="postgis",
                display_name="PostGIS空间数据服务",
                server_class="PostGISDataServer",
                module_path="MCP.servers.postgis_data_server",
                conda_env="postgis",
                host_path="/data/Tiaozhanbei/PostGIS",
                port=8005
            ),
            "cell2fire": ModelService(
                name="cell2fire",
                display_name="Cell2Fire火灾蔓延模拟服务",
                server_class="Cell2FireServer",
                module_path="MCP.servers.cell2fire_server",
                conda_env="cell2fire",
                host_path="/data/Tiaozhanbei/Cell2Fire",
                port=8006
            ),
            "filesystem": ModelService(
                name="filesystem",
                display_name="文件系统管理服务",
                server_class="FilesystemServer",
                module_path="MCP.servers.filesystem_server",
                conda_env="base",
                host_path="/data/Tiaozhanbei",
                port=8007
            )
        }
    
    def _setup_tools(self):
        """设置MCP服务管理工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """列出可用的MCP服务管理工具"""
            return [
                Tool(
                    name="start_all_services",
                    description="启动所有MCP模型服务",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parallel": {
                                "type": "boolean",
                                "description": "是否并行启动所有服务",
                                "default": True
                            }
                        }
                    }
                ),
                
                Tool(
                    name="stop_all_services",
                    description="停止所有MCP模型服务"
                ),
                
                Tool(
                    name="start_service",
                    description="启动指定的MCP模型服务",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "enum": list(self.services.keys()),
                                "description": "服务名称"
                            }
                        },
                        "required": ["service_name"]
                    }
                ),
                
                Tool(
                    name="stop_service",
                    description="停止指定的MCP模型服务",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "enum": list(self.services.keys()),
                                "description": "服务名称"
                            }
                        },
                        "required": ["service_name"]
                    }
                ),
                
                Tool(
                    name="get_service_status",
                    description="获取指定服务的状态信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "enum": list(self.services.keys()),
                                "description": "服务名称"
                            }
                        },
                        "required": ["service_name"]
                    }
                ),
                
                Tool(
                    name="get_all_services_status",
                    description="获取所有服务的状态信息"
                ),
                
                Tool(
                    name="ping",
                    description="测试MCP服务管理器连接"
                )
            ]
        
        # 注册工具调用处理器
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            try:
                if name == "start_all_services":
                    return await self._start_all_services(**arguments)
                elif name == "stop_all_services":
                    return await self._stop_all_services()
                elif name == "start_service":
                    return await self._start_service(**arguments)
                elif name == "stop_service":
                    return await self._stop_service(**arguments)
                elif name == "get_service_status":
                    return await self._get_service_status(**arguments)
                elif name == "get_all_services_status":
                    return await self._get_all_services_status()
                elif name == "ping":
                    return [TextContent(type="text", text="pong")]
                else:
                    raise ValueError(f"未知的工具: {name}")
            except Exception as e:
                logger.error(f"工具调用失败: {e}")
                return [TextContent(type="text", text=f"错误: {str(e)}")]
    
    def _setup_resources(self):
        """设置MCP资源"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """列出可用的资源"""
            return [
                Resource(
                    uri="mcp://service-manager/status",
                    name="服务状态",
                    description="所有MCP模型服务的状态信息",
                    mimeType="application/json"
                )
            ]
    
    async def _start_all_services(self, parallel: bool = True) -> List[TextContent]:
        """启动所有MCP模型服务"""
        logger.info("🚀 启动所有MCP模型服务...")
        
        if parallel:
            # 并行启动所有服务
            tasks = []
            for service_name in self.services:
                tasks.append(self._start_service(service_name=service_name))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [TextContent(type="text", text=f"并行启动完成，结果: {results}")]
        else:
            # 串行启动所有服务
            results = []
            for service_name in self.services:
                result = await self._start_service(service_name=service_name)
                results.append(result)
            
            return [TextContent(type="text", text=f"串行启动完成，结果: {results}")]
    
    async def _stop_all_services(self) -> List[TextContent]:
        """停止所有MCP模型服务"""
        logger.info("🛑 停止所有MCP模型服务...")
        
        results = []
        for service_name in self.services:
            result = await self._stop_service(service_name=service_name)
            results.append(result)
        
        return [TextContent(type="text", text=f"停止完成，结果: {results}")]
    
    async def _start_service(self, service_name: str) -> List[TextContent]:
        """启动指定的MCP模型服务"""
        if service_name not in self.services:
            return [TextContent(type="text", text=f"错误: 未知的服务 {service_name}")]
        
        service = self.services[service_name]
        
        if service.status == ServiceStatus.RUNNING:
            return [TextContent(type="text", text=f"服务 {service_name} 已经在运行")]
        
        try:
            logger.info(f"🚀 启动服务: {service_name}")
            service.status = ServiceStatus.STARTING
            
            # 构建启动命令
            cmd = self._build_service_start_command(service)
            
            # 启动服务进程
            service.process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                env=self._get_service_environment(service),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待进程启动
            time.sleep(2)
            if service.process.poll() is None:
                service.status = ServiceStatus.RUNNING
                service.error_message = None
                return [TextContent(type="text", text=f"服务 {service_name} 启动成功")]
            else:
                service.status = ServiceStatus.ERROR
                service.error_message = "进程启动失败"
                return [TextContent(type="text", text=f"服务 {service_name} 启动失败: 进程启动失败")]
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.error_message = str(e)
            logger.error(f"启动服务 {service_name} 失败: {e}")
            return [TextContent(type="text", text=f"启动服务 {service_name} 失败: {e}")]
    
    async def _stop_service(self, service_name: str) -> List[TextContent]:
        """停止指定的MCP模型服务"""
        if service_name not in self.services:
            return [TextContent(type="text", text=f"错误: 未知的服务 {service_name}")]
        
        service = self.services[service_name]
        
        if service.status == ServiceStatus.STOPPED:
            return [TextContent(type="text", text=f"服务 {service_name} 已经停止")]
        
        try:
            logger.info(f"🛑 停止服务: {service_name}")
            service.status = ServiceStatus.STOPPING
            
            if service.process and service.process.poll() is None:
                service.process.terminate()
                service.process.wait(timeout=10)
                service.process = None
            
            service.status = ServiceStatus.STOPPED
            service.error_message = None
            
            return [TextContent(type="text", text=f"服务 {service_name} 停止成功")]
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.error_message = str(e)
            logger.error(f"停止服务 {service_name} 失败: {e}")
            return [TextContent(type="text", text=f"停止服务 {service_name} 失败: {e}")]
    
    async def _get_service_status(self, service_name: str) -> List[TextContent]:
        """获取指定服务的状态信息"""
        if service_name not in self.services:
            return [TextContent(type="text", text=f"错误: 未知的服务 {service_name}")]
        
        service = self.services[service_name]
        status_info = {
            "name": service.name,
            "display_name": service.display_name,
            "status": service.status.value,
            "conda_env": service.conda_env,
            "host_path": service.host_path,
            "port": service.port,
            "error_message": service.error_message,
            "pid": service.process.pid if service.process else None
        }
        
        return [TextContent(type="text", text=json.dumps(status_info, indent=2, ensure_ascii=False))]
    
    async def _get_all_services_status(self) -> List[TextContent]:
        """获取所有服务的状态信息"""
        status_info = {}
        for service_name, service in self.services.items():
            status_info[service_name] = {
                "name": service.name,
                "display_name": service.display_name,
                "status": service.status.value,
                "conda_env": service.conda_env,
                "host_path": service.host_path,
                "port": service.port,
                "error_message": service.error_message,
                "pid": service.process.pid if service.process else None
            }
        
        return [TextContent(type="text", text=json.dumps(status_info, indent=2, ensure_ascii=False))]
    
    def _build_service_start_command(self, service: ModelService) -> List[str]:
        """构建服务启动命令"""
        return ["python3", f"src/MCP/servers/{service.name}_server.py"]
    
    def _get_service_environment(self, service: ModelService) -> Dict[str, str]:
        """获取服务环境变量"""
        env = os.environ.copy()
        
        # 设置服务特定的环境变量
        env[f"{service.name.upper()}_HOST"] = service.host_path
        env[f"{service.name.upper()}_ENV"] = service.conda_env
        
        # 设置Python路径
        env["PYTHONPATH"] = f"{self.base_dir}/src:{env.get('PYTHONPATH', '')}"
        
        return env
    
    async def run(self):
        """运行MCP服务管理器"""
        logger.info("🚀 启动MCP服务管理器...")
        
        # 启动stdio服务器
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-service-manager",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )


async def main():
    """主函数"""
    manager = MCPServiceManager()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())
