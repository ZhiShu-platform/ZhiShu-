import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import aiohttp
from pathlib import Path

@dataclass
class MCPRequest:
    """MCP请求结构"""
    tool_name: str
    parameters: Dict[str, Any]
    execution_id: Optional[str] = None
    priority: int = 0
    timeout: int = 300

@dataclass
class MCPResponse:
    """MCP响应结构"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MCPClient:
    """MCP客户端框架"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=300)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """发送HTTP请求"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method, url, json=data, params=params
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    return MCPResponse(
                        success=True,
                        data=response_data,
                        execution_id=response_data.get('execution_id'),
                        metadata=response_data.get('metadata')
                    )
                else:
                    return MCPResponse(
                        success=False,
                        error=response_data.get('message', f"HTTP {response.status}")
                    )
                    
        except asyncio.TimeoutError:
            return MCPResponse(
                success=False,
                error="Request timeout"
            )
        except Exception as e:
            return MCPResponse(
                success=False,
                error=f"Request failed: {str(e)}"
            )
    
    async def health_check(self) -> MCPResponse:
        """检查服务健康状态"""
        return await self._make_request('GET', '/health')
    
    async def list_tools(
        self, 
        model_name: Optional[str] = None,
        category: Optional[str] = None
    ) -> MCPResponse:
        """列出可用工具"""
        params = {}
        if model_name:
            params['model_name'] = model_name
        if category:
            params['category'] = category
        
        return await self._make_request('GET', '/tools', params=params)
    
    async def get_tool_info(self, tool_name: str) -> MCPResponse:
        """获取工具信息"""
        return await self._make_request('GET', f'/tools/{tool_name}')
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        priority: int = 0,
        wait_for_completion: bool = False,
        poll_interval: float = 2.0
    ) -> MCPResponse:
        """执行工具"""
        request_data = {
            'tool_name': tool_name,
            'parameters': parameters,
            'priority': priority
        }
        
        response = await self._make_request('POST', '/execute', data=request_data)
        
        if not response.success:
            return response
        
        if wait_for_completion:
            execution_id = response.execution_id
            if execution_id:
                return await self.wait_for_completion(execution_id, poll_interval)
        
        return response
    
    async def wait_for_completion(
        self, 
        execution_id: str, 
        poll_interval: float = 2.0,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """等待执行完成"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查超时
            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                return MCPResponse(
                    success=False,
                    error="Execution timeout"
                )
            
            # 获取执行状态
            status_response = await self.get_execution_status(execution_id)
            if not status_response.success:
                return status_response
            
            status_data = status_response.data
            if not status_data:
                return MCPResponse(
                    success=False,
                    error="Invalid status response"
                )
            
            status = status_data.get('status')
            if status == 'completed':
                return MCPResponse(
                    success=True,
                    data=status_data.get('result'),
                    execution_id=execution_id,
                    metadata=status_data.get('metadata')
                )
            elif status == 'failed':
                return MCPResponse(
                    success=False,
                    error=status_data.get('error', 'Execution failed'),
                    execution_id=execution_id
                )
            elif status == 'cancelled':
                return MCPResponse(
                    success=False,
                    error="Execution cancelled",
                    execution_id=execution_id
                )
            
            # 等待后继续轮询
            await asyncio.sleep(poll_interval)
    
    async def get_execution_status(self, execution_id: str) -> MCPResponse:
        """获取执行状态"""
        return await self._make_request('GET', f'/status/{execution_id}')
    
    async def cancel_execution(self, execution_id: str) -> MCPResponse:
        """取消执行"""
        return await self._make_request('DELETE', f'/executions/{execution_id}')
    
    async def list_models(self) -> MCPResponse:
        """列出可用模型"""
        return await self._make_request('GET', '/models')
    
    async def list_categories(self) -> MCPResponse:
        """列出工具类别"""
        return await self._make_request('GET', '/categories')
    
    async def get_server_stats(self) -> MCPResponse:
        """获取服务器统计信息"""
        return await self._make_request('GET', '/stats')

class MCPClientPool:
    """MCP客户端连接池"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.clients: List[MCPClient] = []
        self.available_clients: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, base_urls: List[str]):
        """初始化连接池"""
        for url in base_urls:
            client = MCPClient(url)
            await client.__aenter__()
            self.clients.append(client)
            await self.available_clients.put(client)
    
    async def get_client(self) -> MCPClient:
        """获取可用客户端"""
        return await self.available_clients.get()
    
    async def release_client(self, client: MCPClient):
        """释放客户端回连接池"""
        await self.available_clients.put(client)
    
    async def close(self):
        """关闭所有客户端"""
        for client in self.clients:
            await client.__aexit__(None, None, None)
        self.clients.clear()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# 便捷函数
async def quick_execute(
    tool_name: str,
    parameters: Dict[str, Any],
    server_url: str = "http://localhost:8000"
) -> MCPResponse:
    """快速执行工具"""
    async with MCPClient(server_url) as client:
        return await client.execute_tool(tool_name, parameters, wait_for_completion=True)

async def list_available_tools(
    server_url: str = "http://localhost:8000"
) -> List[Dict[str, Any]]:
    """快速列出可用工具"""
    async with MCPClient(server_url) as client:
        response = await client.list_tools()
        if response.success and response.data:
            return response.data.get('tools', [])
        return []
