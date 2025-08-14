"""
Configuration settings for the emergency management platform.
This file centralizes all application-wide settings.
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field # 导入 field
from dotenv import load_dotenv

load_dotenv(override=True)

@dataclass
class APIConfig:
    """API configuration."""
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "sk-72a96dafa8ac4447a7fd65db34cba05d")
    deepseek_base_url: str = "https://api.deepseek.com"
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-69f454a5-20da-4a28-ba1f-9e3b7e23834c")
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-8d67ca20-2186-4324-94ea-a5ae5048eb03")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

@dataclass
class MCPConfig:
    """MCP server configuration."""
    # Model installation paths - update these to match your deployment
    cell2fire_host: str = os.getenv("CELL2FIRE_HOST", "/data/Tiaozhanbei/Cell2Fire")
    climada_host: str = os.getenv("CLIMADA_HOST", "/data/Tiaozhanbei/Climada")
    lisflood_host: str = os.getenv("LISFLOOD_HOST", "/data/Tiaozhanbei/Lisflood")
    nfdrs4_host: str = os.getenv("NFDRS4_HOST", "/data/Tiaozhanbei/NFDRS4")
    pangu_host: str = os.getenv("PANGU_HOST", "/data/Tiaozhanbei/Pangu_weather")
    aurora_host: str = os.getenv("AURORA_HOST", "/data/Tiaozhanbei/aurora-main")
    geoserver_host: str = os.getenv("GEOSERVER_HOST", "/data/Tiaozhanbei/geoserver")
    openswpc_host: str = os.getenv("OPENSWPC_HOST", "/data/Tiaozhanbei/OpenSWPC")
    
    # MCP server ports
    base_port: int = int(os.getenv("MCP_BASE_PORT", "8000"))
    
    # Environment settings
    conda_base_path: str = os.getenv("CONDA_BASE_PATH", "/home/lenovo/anaconda3")
    python_env_name: str = os.getenv("PYTHON_ENV_NAME", "base")

@dataclass
class DisasterConfig:
    """Disaster-specific configuration."""
    # 对于 List 和 Dict 这种可变类型，默认值也需要使用 default_factory
    disaster_types: List[str] = field(default_factory=list)
    warning_thresholds: Dict[str, float] = field(default_factory=dict)
    response_protocols: Dict[str, List[str]] = field(default_factory=dict)
    
    # 移除 __post_init__ 中的默认值设置，因为 field(default_factory=...) 已经处理了

@dataclass
class Config:
    """Main configuration class."""
    # Add application metadata here to be used by FastAPI
    app_title: str = "Emergency Management System"
    app_description: str = "Multi-agent platform for disaster response."
    app_version: str = "1.0.0"

    # *** 关键修改：使用 field(default_factory=...) 来处理可变默认值 ***
    api: APIConfig = field(default_factory=APIConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    disaster: DisasterConfig = field(default_factory=DisasterConfig)
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.api.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")
        return True

# Global config instance
config = Config()
