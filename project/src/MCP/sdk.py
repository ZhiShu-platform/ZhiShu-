"""
MCP SDK

Software Development Kit for interacting with the Model Control Plane.
Provides convenient classes and functions for developers.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

import aiohttp

from .core.base_model import ModelResult, ModelStatus
from .core.tool_registry import ToolMetadata

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for interacting with MCP server.
    
    Provides high-level interface for:
    - Tool discovery and execution
    - Result retrieval
    - Status monitoring
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to MCP server."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"Request failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health."""
        return await self._request("GET", "/health")
    
    async def list_tools(
        self, 
        model_name: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available tools."""
        params = {}
        if model_name:
            params["model_name"] = model_name
        if category:
            params["category"] = category
        
        response = await self._request("GET", "/tools", params=params)
        return response["tools"]
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a tool."""
        return await self._request("GET", f"/tools/{tool_name}")
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        priority: int = 0,
        wait_for_completion: bool = False,
        poll_interval: float = 2.0
    ) -> Union[str, Dict[str, Any]]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            priority: Execution priority
            wait_for_completion: If True, wait for execution to complete
            poll_interval: Polling interval in seconds
            
        Returns:
            Execution ID if wait_for_completion=False, otherwise execution result
        """
        # Start execution
        request_data = {
            "tool_name": tool_name,
            "parameters": parameters,
            "priority": priority
        }
        
        response = await self._request(
            "POST", 
            "/execute", 
            json=request_data
        )
        
        execution_id = response["execution_id"]
        
        if not wait_for_completion:
            return execution_id
        
        # Wait for completion
        return await self.wait_for_completion(execution_id, poll_interval)
    
    async def wait_for_completion(
        self, 
        execution_id: str, 
        poll_interval: float = 2.0,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Wait for execution to complete.
        
        Args:
            execution_id: Execution ID to monitor
            poll_interval: Polling interval in seconds
            timeout: Maximum wait time in seconds
            
        Returns:
            Final execution result
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status = await self.get_execution_status(execution_id)
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                return status
            
            # Check timeout
            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                raise TimeoutError(f"Execution {execution_id} timed out after {timeout} seconds")
            
            await asyncio.sleep(poll_interval)
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        return await self._request("GET", f"/status/{execution_id}")
    
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel an execution."""
        return await self._request("DELETE", f"/executions/{execution_id}")
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        return await self._request("GET", "/models")
    
    async def list_categories(self) -> Dict[str, Any]:
        """List tool categories."""
        return await self._request("GET", "/categories")
    
    async def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return await self._request("GET", "/stats")


class ToolExecutor:
    """
    High-level tool executor with convenient methods.
    """
    
    def __init__(self, client: MCPClient):
        self.client = client
    
    async def run_climada_impact_assessment(
        self,
        hazard_type: str,
        region: str,
        year_range: Optional[List[int]] = None,
        return_period: Optional[List[int]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Run Climada impact assessment."""
        parameters = {
            "hazard_type": hazard_type,
            "region": region,
            "year_range": year_range or [2000, 2020],
            "return_period": return_period or [10, 50, 100, 250],
            **kwargs
        }
        
        return await self.client.execute_tool(
            "climada_impact_assessment",
            parameters,
            wait_for_completion=True
        )
    
    async def run_climada_exposure_analysis(
        self,
        country_iso: str,
        exposure_type: str = "litpop",
        reference_year: int = 2020,
        **kwargs
    ) -> Dict[str, Any]:
        """Run Climada exposure analysis."""
        parameters = {
            "country_iso": country_iso,
            "exposure_type": exposure_type,
            "reference_year": reference_year,
            **kwargs
        }
        
        return await self.client.execute_tool(
            "climada_exposure_analysis",
            parameters,
            wait_for_completion=True
        )
    
    async def run_lisflood_simulation(
        self,
        start_date: str,
        end_date: str,
        settings_file: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Run Lisflood flood simulation."""
        parameters = {
            "start_date": start_date,
            "end_date": end_date,
            "settings_file": settings_file,
            "output_dir": output_dir,
            **kwargs
        }
        
        return await self.client.execute_tool(
            "lisflood_simulation",
            parameters,
            wait_for_completion=True
        )
    
    async def run_lisflood_forecast(
        self,
        forecast_start: str,
        forecast_horizon: int,
        settings_file: str,
        meteorological_forecast: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Run Lisflood flood forecast."""
        parameters = {
            "forecast_start": forecast_start,
            "forecast_horizon": forecast_horizon,
            "settings_file": settings_file,
            "meteorological_forecast": meteorological_forecast,
            **kwargs
        }
        
        return await self.client.execute_tool(
            "lisflood_forecast",
            parameters,
            wait_for_completion=True
        )


class BatchExecutor:
    """
    Execute multiple tools in batch with dependency management.
    """
    
    def __init__(self, client: MCPClient):
        self.client = client
        self.executions: Dict[str, Dict[str, Any]] = {}
    
    def add_execution(
        self,
        name: str,
        tool_name: str,
        parameters: Dict[str, Any],
        depends_on: Optional[List[str]] = None,
        priority: int = 0
    ):
        """Add an execution to the batch."""
        self.executions[name] = {
            "tool_name": tool_name,
            "parameters": parameters,
            "depends_on": depends_on or [],
            "priority": priority,
            "status": "pending",
            "execution_id": None,
            "result": None
        }
    
    async def execute_batch(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """Execute the batch with dependency resolution."""
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def execute_single(name: str):
            async with semaphore:
                execution = self.executions[name]
                
                # Wait for dependencies
                for dep_name in execution["depends_on"]:
                    if dep_name in self.executions:
                        while self.executions[dep_name]["status"] != "completed":
                            await asyncio.sleep(0.5)
                
                # Execute tool
                try:
                    execution["status"] = "running"
                    result = await self.client.execute_tool(
                        execution["tool_name"],
                        execution["parameters"],
                        execution["priority"],
                        wait_for_completion=True
                    )
                    
                    execution["status"] = "completed"
                    execution["result"] = result
                    results[name] = result
                    
                except Exception as e:
                    execution["status"] = "failed"
                    execution["result"] = {"error": str(e)}
                    results[name] = execution["result"]
        
        # Execute all tasks
        tasks = [execute_single(name) for name in self.executions.keys()]
        await asyncio.gather(*tasks)
        
        return results


# Utility functions
async def quick_execute(
    tool_name: str,
    parameters: Dict[str, Any],
    server_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """Quick tool execution with automatic client management."""
    async with MCPClient(server_url) as client:
        return await client.execute_tool(
            tool_name, 
            parameters, 
            wait_for_completion=True
        )


async def list_available_tools(
    server_url: str = "http://localhost:8000"
) -> List[Dict[str, Any]]:
    """List all available tools."""
    async with MCPClient(server_url) as client:
        return await client.list_tools()


# Example usage functions
async def example_climada_workflow():
    """Example Climada workflow."""
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        
        # Run exposure analysis
        exposure_result = await executor.run_climada_exposure_analysis(
            country_iso="CHE",
            exposure_type="litpop"
        )
        
        # Run impact assessment
        impact_result = await executor.run_climada_impact_assessment(
            hazard_type="tropical_cyclone",
            region="Switzerland"
        )
        
        return {
            "exposure": exposure_result,
            "impact": impact_result
        }


async def example_lisflood_workflow():
    """Example Lisflood workflow."""
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        
        # Run simulation
        simulation_result = await executor.run_lisflood_simulation(
            start_date="2020-01-01",
            end_date="2020-12-31",
            settings_file="settings.xml",
            output_dir="./output"
        )
        
        # Run forecast
        forecast_result = await executor.run_lisflood_forecast(
            forecast_start="2024-03-15",
            forecast_horizon=7,
            settings_file="settings.xml",
            meteorological_forecast="forecast_data.nc"
        )
        
        return {
            "simulation": simulation_result,
            "forecast": forecast_result
        }