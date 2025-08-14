"""
MCP客户端 - 为智能体提供统一的模型调用接口

包含所有灾害模型的方法调用，如CLIMADA、LISFLOOD、Cell2Fire等。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)


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
    """MCP客户端 - 统一调用各种灾害模型"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=300)
        
        # 服务配置
        self.services = {
            'climada': {'host': 'localhost', 'port': 8001},
            'lisflood': {'host': 'localhost', 'port': 8002},
            'pangu_weather': {'host': 'localhost', 'port': 8003},
            'nfdrs4': {'host': 'localhost', 'port': 8004},
            'cell2fire': {'host': 'localhost', 'port': 8005},
            'aurora': {'host': 'localhost', 'port': 8006},
            'postgis': {'host': 'localhost', 'port': 8007},
            'filesystem': {'host': 'localhost', 'port': 8008}
        }
    
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
        service_name: str,
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        method: str = 'POST'
    ) -> MCPResponse:
        """发送HTTP请求到指定服务"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        if service_name not in self.services:
            return MCPResponse(
                success=False,
                error=f"Service '{service_name}' not found"
            )
        
        service = self.services[service_name]
        url = f"http://{service['host']}:{service['port']}{endpoint}"
        
        try:
            async with self.session.request(
                method, url, json=data
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return MCPResponse(
                        success=True,
                        data=response_data,
                        execution_id=response_data.get('execution_id'),
                        metadata=response_data.get('metadata')
                    )
                else:
                    error_text = await response.text()
                    return MCPResponse(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}"
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
    
    async def health_check(self) -> Dict[str, Any]:
        """检查所有MCP服务健康状态"""
        health_status = {}
        
        for service_name, service_config in self.services.items():
            try:
                response = await self._make_request(
                    service_name, '/health', method='GET'
                )
                health_status[service_name] = {
                    'status': 'healthy' if response.success else 'unhealthy',
                    'error': response.error if not response.success else None
                }
            except Exception as e:
                health_status[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status
    
    # ==================== CLIMADA 模型调用 ====================
    
    async def call_climada_model(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用CLIMADA模型"""
        return await self._make_request(
            'climada',
            '/execute',
            {
                'tool_name': f'climada_{operation}',
                'parameters': parameters
            }
        )
    
    # 基础工具
    async def call_climada_ping(self) -> MCPResponse:
        """检查CLIMADA服务状态"""
        return await self.call_climada_model('ping', {})
    
    async def call_climada_get_environment_info(self) -> MCPResponse:
        """获取CLIMADA环境信息"""
        return await self.call_climada_model('get_environment_info', {})
    
    # 预警功能
    async def call_climada_hazard_detection(
        self,
        hazard_type: str,
        intensity_threshold: float,
        spatial_resolution: str = "10arcsec"
    ) -> MCPResponse:
        """调用CLIMADA灾害检测"""
        parameters = {
            'hazard_type': hazard_type,
            'intensity_threshold': intensity_threshold,
            'spatial_resolution': spatial_resolution
        }
        return await self.call_climada_model('hazard_detection', parameters)
    
    async def call_climada_early_warning(
        self,
        warning_type: str,
        confidence_level: float = 0.8
    ) -> MCPResponse:
        """调用CLIMADA早期预警"""
        parameters = {
            'warning_type': warning_type,
            'confidence_level': confidence_level
        }
        return await self.call_climada_model('early_warning', parameters)
    
    # 评估功能
    async def call_climada_exposure_analysis(
        self,
        exposure_type: str,
        spatial_unit: str = "admin",
        temporal_resolution: str = "annual"
    ) -> MCPResponse:
        """调用CLIMADA暴露度分析"""
        parameters = {
            'exposure_type': exposure_type,
            'spatial_unit': spatial_unit,
            'temporal_resolution': temporal_resolution
        }
        return await self.call_climada_model('exposure_analysis', parameters)
    
    async def call_climada_vulnerability_assessment(
        self,
        vulnerability_factors: List[str],
        weighting_scheme: str = "equal"
    ) -> MCPResponse:
        """调用CLIMADA脆弱性评估"""
        parameters = {
            'vulnerability_factors': vulnerability_factors,
            'weighting_scheme': weighting_scheme
        }
        return await self.call_climada_model('vulnerability_assessment', parameters)
    
    async def call_climada_risk_quantification(
        self,
        risk_metric: str,
        time_horizon: int = 50,
        return_periods: List[int] = None
    ) -> MCPResponse:
        """调用CLIMADA风险量化"""
        if return_periods is None:
            return_periods = [5, 10, 25, 50, 100]
        parameters = {
            'risk_metric': risk_metric,
            'time_horizon': time_horizon,
            'return_periods': return_periods
        }
        return await self.call_climada_model('risk_quantification', parameters)
    
    # 核心功能
    async def call_climada_impact_assessment(
        self,
        hazard_type: str,
        location: Dict[str, float],
        intensity: float,
        exposure_data: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """调用CLIMADA影响评估"""
        parameters = {
            'hazard_type': hazard_type,
            'location': location,
            'intensity': intensity
        }
        if exposure_data:
            parameters['exposure_data'] = exposure_data
        
        return await self.call_climada_model('impact_assessment', parameters)
    
    async def call_climada_hazard_modeling(
        self,
        hazard_type: str,
        scenario_params: Dict[str, Any],
        time_horizon: int = 50
    ) -> MCPResponse:
        """调用CLIMADA灾害建模"""
        parameters = {
            'hazard_type': hazard_type,
            'scenario_params': scenario_params,
            'time_horizon': time_horizon
        }
        return await self.call_climada_model('hazard_modeling', parameters)
    
    # 响应功能
    async def call_climada_adaptation_planning(
        self,
        adaptation_type: str,
        cost_effectiveness: bool = True
    ) -> MCPResponse:
        """调用CLIMADA适应规划"""
        parameters = {
            'adaptation_type': adaptation_type,
            'cost_effectiveness': cost_effectiveness
        }
        return await self.call_climada_model('adaptation_planning', parameters)
    
    async def call_climada_mitigation_strategy(
        self,
        strategy_type: str,
        target_year: int = 2050
    ) -> MCPResponse:
        """调用CLIMADA减缓策略"""
        parameters = {
            'strategy_type': strategy_type,
            'target_year': target_year
        }
        return await self.call_climada_model('mitigation_strategy', parameters)
    
    async def call_climada_cost_benefit(
        self,
        measures: List[str],
        time_horizon: int = 30,
        discount_rate: float = 0.03
    ) -> MCPResponse:
        """调用CLIMADA成本效益分析"""
        parameters = {
            'measures': measures,
            'time_horizon': time_horizon,
            'discount_rate': discount_rate
        }
        return await self.call_climada_model('cost_benefit', parameters)
    
    # ==================== LISFLOOD 模型调用 ====================
    
    async def call_lisflood_model(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用LISFLOOD模型"""
        return await self._make_request(
            'lisflood',
            '/execute',
            {
                'tool_name': f'lisflood_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_lisflood_simulation(
        self,
        start_date: str,
        end_date: str,
        settings_file: str,
        output_dir: str,
        **kwargs
    ) -> MCPResponse:
        """调用LISFLOOD洪水模拟"""
        parameters = {
            'start_date': start_date,
            'end_date': end_date,
            'settings_file': settings_file,
            'output_dir': output_dir,
            **kwargs
        }
        return await self.call_lisflood_model('simulation', parameters)
    
    async def call_lisflood_forecast(
        self,
        forecast_start: str,
        forecast_horizon: int,
        settings_file: str,
        meteorological_forecast: str,
        **kwargs
    ) -> MCPResponse:
        """调用LISFLOOD洪水预测"""
        parameters = {
            'forecast_start': forecast_start,
            'forecast_horizon': forecast_horizon,
            'settings_file': settings_file,
            'meteorological_forecast': meteorological_forecast,
            **kwargs
        }
        return await self.call_lisflood_model('forecast', parameters)
    
    # ==================== Cell2Fire 模型调用 ====================
    
    async def call_cell2fire_model(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用Cell2Fire模型"""
        return await self._make_request(
            'cell2fire',
            '/execute',
            {
                'tool_name': f'cell2fire_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_cell2fire_simulation(
        self,
        ignition_points: List[Dict[str, Any]],
        weather_scenario: Dict[str, float],
        fuel_model: str = "standard",
        simulation_time: int = 1440,
        **kwargs
    ) -> MCPResponse:
        """调用Cell2Fire火灾蔓延模拟"""
        parameters = {
            'ignition_points': ignition_points,
            'weather_scenario': weather_scenario,
            'fuel_model': fuel_model,
            'simulation_time': simulation_time,
            **kwargs
        }
        return await self.call_cell2fire_model('simulate', parameters)
    
    # ==================== Pangu-Weather 模型调用 ====================
    
    async def call_pangu_weather_model(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用Pangu-Weather模型"""
        return await self._make_request(
            'pangu_weather',
            '/execute',
            {
                'tool_name': f'pangu_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_pangu_forecast(
        self,
        region: Dict[str, float],
        forecast_steps: int = 40,
        resolution: str = "0.1deg",
        **kwargs
    ) -> MCPResponse:
        """调用Pangu-Weather预测"""
        parameters = {
            'region': region,
            'forecast_steps': forecast_steps,
            'resolution': resolution,
            **kwargs
        }
        return await self.call_pangu_weather_model('forecast', parameters)
    
    # ==================== NFDRS4 模型调用 ====================
    
    async def call_nfdrs4_model(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用NFDRS4模型"""
        return await self._make_request(
            'nfdrs4',
            '/execute',
            {
                'tool_name': f'nfdrs4_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_nfdrs4_fire_danger(
        self,
        weather_data: Dict[str, float],
        fuel_moisture: Dict[str, float],
        **kwargs
    ) -> MCPResponse:
        """调用NFDRS4火灾危险度计算"""
        parameters = {
            'weather_data': weather_data,
            'fuel_moisture': fuel_moisture,
            **kwargs
        }
        return await self.call_nfdrs4_model('fire_danger', parameters)
    
    # ==================== Aurora 模型调用 ====================
    
    async def call_aurora_model(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用Aurora模型"""
        return await self._make_request(
            'aurora',
            '/execute',
            {
                'tool_name': f'aurora_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_aurora_forecast(
        self,
        region: Dict[str, float],
        forecast_steps: int = 40,
        resolution: str = "0.1deg",
        **kwargs
    ) -> MCPResponse:
        """调用Aurora大气预测"""
        parameters = {
            'region': region,
            'forecast_steps': forecast_steps,
            'resolution': resolution,
            **kwargs
        }
        return await self.call_aurora_model('forecast', parameters)
    
    # ==================== PostGIS 服务调用 ====================
    
    async def call_postgis_service(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用PostGIS服务"""
        return await self._make_request(
            'postgis',
            '/execute',
            {
                'tool_name': f'postgis_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_postgis_spatial_query(
        self,
        query_type: str,
        table_name: str,
        geometry: Dict[str, Any],
        fields: Optional[List[str]] = None,
        spatial_relation: str = "intersects"
    ) -> MCPResponse:
        """调用PostGIS空间查询"""
        parameters = {
            'query_type': query_type,
            'table_name': table_name,
            'geometry': geometry,
            'spatial_relation': spatial_relation
        }
        if fields:
            parameters['fields'] = fields
        
        return await self.call_postgis_service('spatial_query', parameters)
    
    async def call_postgis_data_import(
        self,
        file_path: str,
        file_format: str,
        table_name: str,
        srid: int = 4326
    ) -> MCPResponse:
        """调用PostGIS数据导入"""
        parameters = {
            'file_path': file_path,
            'file_format': file_format,
            'table_name': table_name,
            'srid': srid
        }
        return await self.call_postgis_service('data_import', parameters)
    
    # ==================== 文件系统服务调用 ====================
    
    async def call_filesystem_service(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> MCPResponse:
        """调用文件系统服务"""
        return await self._make_request(
            'filesystem',
            '/execute',
            {
                'tool_name': f'filesystem_{operation}',
                'parameters': parameters
            }
        )
    
    async def call_filesystem_cache_file(
        self,
        file_path: str,
        target_dir: str = "temp",
        tags: Optional[List[str]] = None,
        expires_in_hours: Optional[int] = None
    ) -> MCPResponse:
        """调用文件系统缓存文件"""
        parameters = {
            'file_path': file_path,
            'target_dir': target_dir
        }
        if tags:
            parameters['tags'] = tags
        if expires_in_hours:
            parameters['expires_in_hours'] = expires_in_hours
        
        return await self.call_filesystem_service('cache_file', parameters)
    
    async def call_filesystem_get_cached_file(
        self,
        file_id: str
    ) -> MCPResponse:
        """调用文件系统获取缓存文件"""
        parameters = {'file_id': file_id}
        return await self.call_filesystem_service('get_cached_file', parameters)
    
    # ==================== 工具发现 ====================
    
    async def list_available_tools(
        self,
        service_name: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """列出可用工具"""
        if service_name and service_name in self.services:
            response = await self._make_request(
                service_name, '/tools', method='GET'
            )
            return response.data if response.success else {}
        
        # 列出所有服务的工具
        all_tools = {}
        for service in self.services.keys():
            try:
                response = await self._make_request(
                    service, '/tools', method='GET'
                )
                if response.success:
                    all_tools[service] = response.data
            except Exception as e:
                logger.warning(f"Failed to get tools from {service}: {e}")
        
        return all_tools
    
    async def get_tool_info(
        self,
        service_name: str,
        tool_name: str
    ) -> Dict[str, Any]:
        """获取工具详细信息"""
        response = await self._make_request(
            service_name, f'/tools/{tool_name}', method='GET'
        )
        return response.data if response.success else {}


# 全局MCP客户端实例
mcp_client = MCPClient()


# 便捷函数
async def quick_climada_assessment(
    hazard_type: str,
    location: Dict[str, float],
    intensity: float
) -> Dict[str, Any]:
    """快速CLIMADA影响评估"""
    async with MCPClient() as client:
        response = await client.call_climada_impact_assessment(
            hazard_type, location, intensity
        )
        return response.data if response.success else {'error': response.error}


async def quick_lisflood_simulation(
    start_date: str,
    end_date: str,
    settings_file: str
) -> Dict[str, Any]:
    """快速LISFLOOD模拟"""
    async with MCPClient() as client:
        response = await client.call_lisflood_simulation(
            start_date, end_date, settings_file, "./output"
        )
        return response.data if response.success else {'error': response.error}


async def quick_cell2fire_simulation(
    ignition_points: List[Dict[str, Any]],
    weather_scenario: Dict[str, float]
) -> Dict[str, Any]:
    """快速Cell2Fire模拟"""
    async with MCPClient() as client:
        response = await client.call_cell2fire_simulation(
            ignition_points, weather_scenario
        )
        return response.data if response.success else {'error': response.error}
