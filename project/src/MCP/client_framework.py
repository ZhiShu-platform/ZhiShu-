"""
MCP客户端框架

为智能体提供统一的MCP服务调用接口，包括服务发现、路由、错误处理等。
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import backoff
from pathlib import Path

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceEndpoint:
    """服务端点信息"""
    name: str
    url: str
    health_check_url: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: float = 0
    response_time: float = 0
    error_count: int = 0
    max_errors: int = 3
    timeout: int = 30


@dataclass
class MCPCallResult:
    """MCP调用结果"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_id: Optional[str] = None
    service_name: Optional[str] = None
    tool_name: Optional[str] = None
    duration: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPClientFramework:
    """MCP客户端框架"""
    
    def __init__(self, config_file: str = "backend/mcp_services.yaml"):
        self.config_file = Path(config_file)
        self.services: Dict[str, ServiceEndpoint] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_check_interval = 60  # 秒
        self._load_config()
        self._start_health_checker()
    
    def _load_config(self):
        """加载MCP服务配置"""
        try:
            import yaml
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            services = config.get('services', {})
            for service_name, service_config in services.items():
                if service_config.get('enabled', True):
                    endpoint = ServiceEndpoint(
                        name=service_name,
                        url=f"http://{service_config['host']}:{service_config['port']}",
                        health_check_url=f"http://{service_config['host']}:{service_config['port']}/health",
                        timeout=service_config.get('timeout', 30)
                    )
                    self.services[service_name] = endpoint
            
            logger.info(f"Loaded {len(self.services)} MCP services")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            # 使用默认配置
            self._create_default_services()
    
    def _create_default_services(self):
        """创建默认服务配置"""
        default_services = {
            'postgis': ServiceEndpoint(
                name='postgis',
                url='http://localhost:8007',
                health_check_url='http://localhost:8007/health'
            ),
            'filesystem': ServiceEndpoint(
                name='filesystem',
                url='http://localhost:8008',
                health_check_url='http://localhost:8008/health'
            ),
            'climada': ServiceEndpoint(
                name='climada',
                url='http://localhost:8001',
                health_check_url='http://localhost:8001/health'
            ),
            'lisflood': ServiceEndpoint(
                name='lisflood',
                url='http://localhost:8002',
                health_check_url='http://localhost:8002/health'
            )
        }
        self.services.update(default_services)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def call_service(
        self,
        service_name: str,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> MCPCallResult:
        """
        调用MCP服务
        
        Args:
            service_name: 服务名称
            tool_name: 工具名称
            parameters: 工具参数
            timeout: 超时时间
            
        Returns:
            MCPCallResult: 调用结果
        """
        if service_name not in self.services:
            return MCPCallResult(
                success=False,
                error=f"Service '{service_name}' not found"
            )
        
        service = self.services[service_name]
        if service.status == ServiceStatus.UNHEALTHY:
            return MCPCallResult(
                success=False,
                error=f"Service '{service_name}' is unhealthy"
            )
        
        start_time = time.time()
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # 构建请求数据
            request_data = {
                "tool_name": tool_name,
                "parameters": parameters,
                "priority": 0
            }
            
            # 发送请求
            timeout_val = timeout or service.timeout
            async with self.session.post(
                f"{service.url}/execute",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=timeout_val)
            ) as response:
                
                if response.status == 200:
                    result_data = await response.json()
                    
                    # 等待执行完成
                    if result_data.get('status') == 'running':
                        execution_id = result_data.get('execution_id')
                        if execution_id:
                            result = await self._wait_for_completion(
                                service, execution_id, timeout_val
                            )
                        else:
                            result = MCPCallResult(
                                success=False,
                                error="No execution ID returned"
                            )
                    else:
                        result = MCPCallResult(
                            success=True,
                            data=result_data,
                            execution_id=result_data.get('execution_id')
                        )
                else:
                    error_text = await response.text()
                    result = MCPCallResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}"
                    )
                
                # 更新服务状态
                service.response_time = time.time() - start_time
                service.error_count = 0
                service.status = ServiceStatus.HEALTHY
                
                result.duration = time.time() - start_time
                result.service_name = service_name
                result.tool_name = tool_name
                
                return result
                
        except asyncio.TimeoutError:
            service.error_count += 1
            return MCPCallResult(
                success=False,
                error=f"Request to '{service_name}' timed out",
                service_name=service_name,
                tool_name=tool_name,
                duration=time.time() - start_time
            )
        except Exception as e:
            service.error_count += 1
            if service.error_count >= service.max_errors:
                service.status = ServiceStatus.UNHEALTHY
            
            return MCPCallResult(
                success=False,
                error=f"Request to '{service_name}' failed: {str(e)}",
                service_name=service_name,
                tool_name=tool_name,
                duration=time.time() - start_time
            )
    
    async def _wait_for_completion(
        self,
        service: ServiceEndpoint,
        execution_id: str,
        timeout: int
    ) -> MCPCallResult:
        """等待执行完成"""
        start_time = time.time()
        poll_interval = 2.0
        
        while True:
            if time.time() - start_time > timeout:
                return MCPCallResult(
                    success=False,
                    error=f"Execution {execution_id} timed out",
                    execution_id=execution_id
                )
            
            try:
                async with self.session.get(
                    f"{service.url}/status/{execution_id}"
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        status = status_data.get('status')
                        
                        if status == 'completed':
                            return MCPCallResult(
                                success=True,
                                data=status_data.get('result'),
                                execution_id=execution_id
                            )
                        elif status == 'failed':
                            return MCPCallResult(
                                success=False,
                                error=status_data.get('error', 'Execution failed'),
                                execution_id=execution_id
                            )
                        elif status == 'cancelled':
                            return MCPCallResult(
                                success=False,
                                error="Execution cancelled",
                                execution_id=execution_id
                            )
                        
                        # 继续等待
                        await asyncio.sleep(poll_interval)
                    else:
                        return MCPCallResult(
                            success=False,
                            error=f"Failed to get status: HTTP {response.status}"
                        )
                        
            except Exception as e:
                return MCPCallResult(
                    success=False,
                    error=f"Status check failed: {str(e)}"
                )
    
    async def health_check(self, service_name: str) -> bool:
        """检查服务健康状态"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                service.health_check_url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                is_healthy = response.status == 200
                service.status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
                service.last_check = time.time()
                return is_healthy
                
        except Exception as e:
            service.status = ServiceStatus.UNHEALTHY
            service.last_check = time.time()
            logger.warning(f"Health check failed for {service_name}: {e}")
            return False
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取服务状态信息"""
        if service_name not in self.services:
            return {"error": "Service not found"}
        
        service = self.services[service_name]
        return {
            "name": service.name,
            "url": service.url,
            "status": service.status.value,
            "last_check": service.last_check,
            "response_time": service.response_time,
            "error_count": service.error_count
        }
    
    async def list_services(self) -> List[Dict[str, Any]]:
        """列出所有服务状态"""
        return [await self.get_service_status(name) for name in self.services.keys()]
    
    def _start_health_checker(self):
        """启动健康检查器"""
        async def health_checker():
            while True:
                try:
                    for service_name in self.services.keys():
                        await self.health_check(service_name)
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health checker error: {e}")
                    await asyncio.sleep(self.health_check_interval)
        
        # 启动后台任务
        asyncio.create_task(health_checker())


# 便捷函数
async def quick_call(
    service_name: str,
    tool_name: str,
    parameters: Dict[str, Any],
    config_file: str = "backend/mcp_services.yaml"
) -> MCPCallResult:
    """快速调用MCP服务"""
    async with MCPClientFramework(config_file) as client:
        return await client.call_service(service_name, tool_name, parameters)


async def get_service_health(
    service_name: str,
    config_file: str = "backend/mcp_services.yaml"
) -> bool:
    """快速检查服务健康状态"""
    async with MCPClientFramework(config_file) as client:
        return await client.health_check(service_name)
