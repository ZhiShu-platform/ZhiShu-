import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml
from contextlib import asynccontextmanager

from .base_model import BaseModel
from .environment_manager import EnvironmentManager

@dataclass
class ServiceConfig:
    """MCP服务配置"""
    name: str
    type: str  # "conda", "docker", "external"
    host: str
    port: int
    environment: Optional[str] = None
    health_check_url: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class MCPServiceManager:
    """MCP服务管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file or "mcp_services.yaml"
        self.services: Dict[str, ServiceConfig] = {}
        self.active_services: Dict[str, Any] = {}
        
        self._load_config()
    
    def _load_config(self):
        """加载服务配置"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    self._parse_config(config_data)
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _parse_config(self, config_data: Dict[str, Any]):
        """解析配置文件"""
        services = config_data.get('services', {})
        
        for service_name, service_data in services.items():
            try:
                config = ServiceConfig(
                    name=service_name,
                    type=service_data.get('type', 'conda'),
                    host=service_data.get('host', 'localhost'),
                    port=service_data.get('port', 8000),
                    environment=service_data.get('environment'),
                    health_check_url=service_data.get('health_check_url'),
                    timeout=service_data.get('timeout', 30),
                    retry_count=service_data.get('retry_count', 3),
                    enabled=service_data.get('enabled', True),
                    metadata=service_data.get('metadata', {})
                )
                self.services[service_name] = config
            except Exception as e:
                self.logger.error(f"Failed to parse service {service_name}: {e}")
    
    def _create_default_config(self):
        """创建默认配置"""
        default_services = {
            'climada': {
                'type': 'conda',
                'host': os.getenv('CLIMADA_HOST', '/data/Tiaozhanbei/Climada'),
                'port': 8001,
                'environment': os.getenv('CLIMADA_ENV', 'Climada'),
                'enabled': True
            },
            'lisflood': {
                'type': 'conda',
                'host': os.getenv('LISFLOOD_HOST', '/data/Tiaozhanbei/Lisflood'),
                'port': 8002,
                'environment': os.getenv('LISFLOOD_ENV', 'Lisflood'),
                'enabled': True
            },
            'pangu_weather': {
                'type': 'docker',
                'host': os.getenv('PANGU_HOST', '/data/Tiaozhanbei/Pangu_weather'),
                'port': 8003,
                'enabled': True
            },
            'nfdrs4': {
                'type': 'docker',
                'host': os.getenv('NFDRS4_HOST', '/data/Tiaozhanbei/NFDRS4'),
                'port': 8004,
                'enabled': True
            },
            'cell2fire': {
                'type': 'docker',
                'host': os.getenv('CELL2FIRE_HOST', '/data/Tiaozhanbei/Cell2Fire'),
                'port': 8005,
                'enabled': True
            },
            'aurora': {
                'type': 'conda',
                'host': os.getenv('AURORA_HOST', '/data/Tiaozhanbei/aurora-main'),
                'port': 8006,
                'environment': os.getenv('AURORA_ENV', 'aurora'),
                'enabled': True
            }
        }
        
        config_data = {
            'services': default_services,
            'shared_directories': {
                'host_base': '/data/Tiaozhanbei/shared',
                'container_base': '/shared'
            },
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'name': os.getenv('DB_NAME', 'zs_data'),
                'user': os.getenv('DB_USER', 'zs_zzr'),
                'password': os.getenv('DB_PASSWORD', '373291Moon')
            }
        }
        
        # 保存默认配置
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        self._parse_config(config_data)
    
    async def start_service(self, service_name: str) -> bool:
        """启动MCP服务"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        config = self.services[service_name]
        if not config.enabled:
            self.logger.warning(f"Service {service_name} is disabled")
            return False
        
        try:
            if config.type == 'conda':
                success = await self._start_conda_service(service_name, config)
            elif config.type == 'docker':
                success = await self._start_docker_service(service_name, config)
            else:
                success = await self._start_external_service(service_name, config)
            
            if success:
                self.logger.info(f"Service {service_name} started successfully")
                return True
            else:
                self.logger.error(f"Failed to start service {service_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting service {service_name}: {e}")
            return False
    
    async def _start_conda_service(self, service_name: str, config: ServiceConfig) -> bool:
        """启动conda环境服务"""
        try:
            # 检查conda环境是否存在
            # 这里简化实现，实际应该调用environment_manager
            return True
        except Exception as e:
            self.logger.error(f"Error starting conda service {service_name}: {e}")
            return False
    
    async def _start_docker_service(self, service_name: str, config: ServiceConfig) -> bool:
        """启动Docker容器服务"""
        try:
            # 简化实现
            return True
        except Exception as e:
            self.logger.error(f"Error starting docker service {service_name}: {e}")
            return False
    
    async def _start_external_service(self, service_name: str, config: ServiceConfig) -> bool:
        """启动外部服务"""
        try:
            return True
        except Exception as e:
            self.logger.error(f"Error starting external service {service_name}: {e}")
            return False
    
    async def start_all_services(self) -> Dict[str, bool]:
        """启动所有服务"""
        results = {}
        
        for service_name in self.services:
            if self.services[service_name].enabled:
                results[service_name] = await self.start_service(service_name)
            else:
                results[service_name] = False
        
        return results
    
    async def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        try:
            if service_name in self.active_services:
                process = self.active_services[service_name]
                process.terminate()
                await process.wait()
                del self.active_services[service_name]
                self.logger.info(f"Service {service_name} stopped")
                return True
            else:
                self.logger.warning(f"Service {service_name} not running")
                return True
        except Exception as e:
            self.logger.error(f"Error stopping service {service_name}: {e}")
            return False
    
    async def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服务"""
        results = {}
        
        for service_name in list(self.active_services.keys()):
            results[service_name] = await self.stop_service(service_name)
        
        return results
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取服务状态"""
        if service_name not in self.services:
            return {"error": "Service not found"}
        
        config = self.services[service_name]
        is_running = service_name in self.active_services
        
        status = {
            "name": service_name,
            "type": config.type,
            "host": config.host,
            "port": config.port,
            "enabled": config.enabled,
            "running": is_running,
            "health": True  # 简化实现
        }
        
        if config.environment:
            status["environment"] = config.environment
        
        return status
    
    async def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务状态"""
        status = {}
        
        for service_name in self.services:
            status[service_name] = await self.get_service_status(service_name)
        
        return status
    
    @asynccontextmanager
    async def managed_services(self):
        """管理服务生命周期的上下文管理器"""
        try:
            await self.start_all_services()
            yield self
        finally:
            await self.stop_all_services()
