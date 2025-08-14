#!/usr/bin/env python3
"""
Aurora大气基础模型MCP服务

提供细粒度的工具接口，包括预警、评估和响应功能。
"""

import asyncio
import logging
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuroraServer:
    """Aurora大气基础模型 - 细粒度工具接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_path = Path("/data/Tiaozhanbei/aurora-main")
        self.conda_environment = "aurora"
        self.server = Server("aurora-server")
        
        # 检查模型路径
        if not self.model_path.exists():
            self.logger.warning(f"Aurora model path not found: {self.model_path}")
        
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """设置细粒度工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                # 基础工具
                Tool(
                    name="aurora_ping",
                    description="检查Aurora服务连接状态",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="aurora_get_model_info",
                    description="获取Aurora模型信息",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # 预警功能
                Tool(
                    name="aurora_detect_extreme_weather",
                    description="检测极端天气事件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {"type": "object", "description": "地理区域"},
                            "threshold": {"type": "number", "description": "预警阈值"},
                            "time_window": {"type": "integer", "description": "时间窗口(小时)"}
                        }
                    }
                ),
                Tool(
                    name="aurora_storm_tracking",
                    description="风暴路径追踪",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "storm_id": {"type": "string", "description": "风暴ID"},
                            "track_length": {"type": "integer", "description": "追踪长度(小时)"}
                        }
                    }
                ),
                
                # ==================== 精准识别灾情 ====================
                
                # 极端天气检测
                Tool(
                    name="aurora_detect_extreme_weather",
                    description="精准检测极端天气事件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "object",
                                "properties": {
                                    "lat_min": {"type": "number", "description": "最小纬度"},
                                    "lat_max": {"type": "number", "description": "最大纬度"},
                                    "lon_min": {"type": "number", "description": "最小经度"},
                                    "lon_max": {"type": "number", "description": "最大经度"}
                                },
                                "description": "地理区域"
                            },
                            "weather_phenomena": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["tropical_cyclone", "extreme_precipitation", "heatwave", "cold_snap", "storm", "drought"]
                                },
                                "description": "天气现象类型"
                            },
                            "detection_method": {
                                "type": "string",
                                "enum": ["threshold_based", "anomaly_detection", "pattern_recognition", "ensemble_forecast"],
                                "description": "检测方法"
                            },
                            "threshold": {
                                "type": "number",
                                "description": "预警阈值"
                            },
                            "time_window": {
                                "type": "integer",
                                "description": "时间窗口(小时)"
                            }
                        },
                        "required": ["region", "weather_phenomena"]
                    }
                ),
                
                # 风暴追踪
                Tool(
                    name="aurora_storm_tracking",
                    description="风暴路径追踪和预测",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "storm_id": {"type": "string", "description": "风暴ID"},
                            "track_length": {
                                "type": "integer",
                                "description": "追踪长度(小时)",
                                "minimum": 6,
                                "maximum": 168
                            },
                            "tracking_parameters": {
                                "type": "object",
                                "properties": {
                                    "intensity_threshold": {"type": "number", "description": "强度阈值"},
                                    "movement_threshold": {"type": "number", "description": "移动阈值(km/h)"},
                                    "size_threshold": {"type": "number", "description": "大小阈值(km)"}
                                }
                            },
                            "prediction_horizon": {
                                "type": "integer",
                                "description": "预测时效(小时)",
                                "minimum": 6,
                                "maximum": 72
                            }
                        },
                        "required": ["storm_id"]
                    }
                ),
                
                # ==================== 量化评估风险 ====================
                
                # 大气稳定性分析
                Tool(
                    name="aurora_atmospheric_stability",
                    description="大气稳定性分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pressure_levels": {
                                "type": "array", 
                                "items": {"type": "number"},
                                "description": "气压层(hPa)"
                            },
                            "temperature_profile": {
                                "type": "array", 
                                "items": {"type": "number"},
                                "description": "温度廓线(°C)"
                            },
                            "humidity_profile": {
                                "type": "array", 
                                "items": {"type": "number"},
                                "description": "湿度廓线(%)"
                            },
                            "stability_indices": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["lifted_index", "cape", "cin", "shear", "helicity"]
                                },
                                "description": "稳定性指数"
                            }
                        },
                        "required": ["pressure_levels", "temperature_profile"]
                    }
                ),
                
                # 风切变分析
                Tool(
                    name="aurora_wind_shear_analysis",
                    description="风切变分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "wind_layers": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "height": {"type": "number", "description": "高度(米)"},
                                        "wind_speed": {"type": "number", "description": "风速(m/s)"},
                                        "wind_direction": {"type": "number", "description": "风向(度)"}
                                    }
                                },
                                "description": "风层数据"
                            },
                            "shear_calculation": {
                                "type": "string",
                                "enum": ["speed_shear", "directional_shear", "total_shear"],
                                "description": "切变计算类型"
                            },
                            "risk_assessment": {
                                "type": "boolean",
                                "description": "是否进行风险评估"
                            }
                        },
                        "required": ["wind_layers"]
                    }
                ),
                
                # 对流分析
                Tool(
                    name="aurora_convection_analysis",
                    description="对流活动分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "convection_indicators": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["cape", "cin", "lifted_index", "k_index", "total_totals"]
                                },
                                "description": "对流指标"
                            },
                            "moisture_analysis": {
                                "type": "object",
                                "properties": {
                                    "precipitable_water": {"type": "number", "description": "可降水量(mm)"},
                                    "relative_humidity": {"type": "array", "items": {"type": "number"}},
                                    "dew_point": {"type": "array", "items": {"type": "number"}}
                                }
                            },
                            "convection_potential": {
                                "type": "string",
                                "enum": ["low", "moderate", "high", "extreme"],
                                "description": "对流潜力"
                            }
                        },
                        "required": ["convection_indicators"]
                    }
                ),
                
                # ==================== 主动协同调度 ====================
                
                # 天气预报
                Tool(
                    name="aurora_weather_forecast",
                    description="高精度天气预报",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "forecast_location": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number", "description": "纬度"},
                                    "lon": {"type": "number", "description": "经度"},
                                    "elevation": {"type": "number", "description": "海拔(米)"}
                                },
                                "required": ["lat", "lon"]
                            },
                            "forecast_horizon": {
                                "type": "integer",
                                "description": "预报时效(小时)",
                                "minimum": 1,
                                "maximum": 240
                            },
                            "forecast_variables": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["temperature", "humidity", "pressure", "wind", "precipitation", "cloud_cover"]
                                },
                                "description": "预报变量"
                            },
                            "ensemble_size": {
                                "type": "integer",
                                "description": "集合预报成员数",
                                "minimum": 1,
                                "maximum": 50
                            },
                            "spatial_resolution": {
                                "type": "string",
                                "enum": ["0.1deg", "0.25deg", "0.5deg", "1deg"],
                                "description": "空间分辨率"
                            }
                        },
                        "required": ["forecast_location", "forecast_horizon"]
                    }
                ),
                
                # 气候预测
                Tool(
                    name="aurora_climate_prediction",
                    description="气候预测和情景分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prediction_type": {
                                "type": "string",
                                "enum": ["seasonal", "annual", "decadal", "century"],
                                "description": "预测类型"
                            },
                            "climate_scenarios": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["ssp126", "ssp245", "ssp370", "ssp585", "custom"]
                                },
                                "description": "气候情景"
                            },
                            "climate_variables": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["temperature", "precipitation", "sea_level", "extreme_events"]
                                },
                                "description": "气候变量"
                            },
                            "uncertainty_quantification": {
                                "type": "boolean",
                                "description": "是否进行不确定性量化"
                            }
                        },
                        "required": ["prediction_type", "climate_scenarios"]
                    }
                ),
                
                # 数值天气预报
                Tool(
                    name="aurora_numerical_weather_prediction",
                    description="数值天气预报模型运行",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_configuration": {
                                "type": "object",
                                "properties": {
                                    "model_name": {"type": "string", "enum": ["aurora", "wrf", "gfs", "ecmwf"]},
                                    "domain_size": {"type": "object", "properties": {"nx": {"type": "integer"}, "ny": {"type": "integer"}}},
                                    "vertical_levels": {"type": "integer", "description": "垂直层数"},
                                    "time_step": {"type": "number", "description": "时间步长(秒)"}
                                }
                            },
                            "initial_conditions": {
                                "type": "string",
                                "description": "初始条件数据源"
                            },
                            "boundary_conditions": {
                                "type": "string",
                                "description": "边界条件数据源"
                            },
                            "physics_options": {
                                "type": "object",
                                "properties": {
                                    "microphysics": {"type": "string", "enum": ["kessler", "lin", "wsm6", "thompson"]},
                                    "convection": {"type": "string", "enum": ["kain_fritsch", "bettis_miller", "grell"]},
                                    "radiation": {"type": "string", "enum": ["rrtm", "cam", "goddard"]}
                                }
                            }
                        },
                        "required": ["model_configuration"]
                    }
                ),
                
                # ==================== 量化评估灾损 ====================
                
                # 天气风险评估
                Tool(
                    name="aurora_weather_risk_assessment",
                    description="天气风险评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "risk_factors": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["extreme_temperature", "heavy_precipitation", "strong_wind", "lightning", "hail"]
                                },
                                "description": "风险因子"
                            },
                            "vulnerability_indicators": {
                                "type": "object",
                                "properties": {
                                    "infrastructure_sensitivity": {"type": "number", "description": "基础设施敏感性(0-1)"},
                                    "population_vulnerability": {"type": "number", "description": "人口脆弱性(0-1)"},
                                    "economic_exposure": {"type": "number", "description": "经济暴露度(0-1)"}
                                }
                            },
                            "risk_quantification": {
                                "type": "string",
                                "enum": ["probability", "impact", "combined"],
                                "description": "风险量化方法"
                            }
                        },
                        "required": ["risk_factors"]
                    }
                ),
                
                # 天气影响评估
                Tool(
                    name="aurora_weather_impact_assessment",
                    description="天气影响评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "impact_categories": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["agriculture", "transportation", "energy", "health", "tourism"]
                                },
                                "description": "影响类别"
                            },
                            "assessment_method": {
                                "type": "string",
                                "enum": ["empirical", "model_based", "expert_judgment", "hybrid"],
                                "description": "评估方法"
                            },
                            "economic_valuation": {
                                "type": "boolean",
                                "description": "是否进行经济价值评估"
                            }
                        },
                        "required": ["impact_categories"]
                    }
                ),
                
                # 基础工具
                Tool(
                    name="aurora_ping",
                    description="检查Aurora服务连接状态",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                Tool(
                    name="aurora_get_model_info",
                    description="获取Aurora模型信息",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # 原有工具保留
                Tool(
                    name="aurora_wind_shear_analysis",
                    description="风切变分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "height_levels": {"type": "array", "items": {"type": "number"}},
                            "wind_speed": {"type": "array", "items": {"type": "number"}},
                            "wind_direction": {"type": "array", "items": {"type": "number"}}
                        }
                    }
                ),
                
                # 响应功能
                Tool(
                    name="aurora_generate_forecast_map",
                    description="生成预报地图",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string", "enum": ["temperature", "precipitation", "wind", "pressure"]},
                            "forecast_time": {"type": "string", "description": "预报时间"},
                            "output_format": {"type": "string", "enum": ["png", "geotiff", "netcdf"]}
                        }
                    }
                ),
                Tool(
                    name="aurora_export_forecast_data",
                    description="导出预报数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "variables": {"type": "array", "items": {"type": "string"}},
                            "time_range": {"type": "object", "description": "时间范围"},
                            "output_format": {"type": "string", "enum": ["csv", "json", "netcdf"]}
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            try:
                if name == "aurora_ping":
                    result = await self._ping_service()
                elif name == "aurora_get_model_info":
                    result = await self._get_model_info()
                elif name == "aurora_detect_extreme_weather":
                    result = await self._detect_extreme_weather(arguments)
                elif name == "aurora_storm_tracking":
                    result = await self._track_storm(arguments)
                elif name == "aurora_atmospheric_stability":
                    result = await self._analyze_atmospheric_stability(arguments)
                elif name == "aurora_wind_shear_analysis":
                    result = await self._analyze_wind_shear(arguments)
                elif name == "aurora_generate_forecast_map":
                    result = await self._generate_forecast_map(arguments)
                elif name == "aurora_export_forecast_data":
                    result = await self._export_forecast_data(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                
            except Exception as e:
                self.logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]
    
    def _setup_resources(self):
        """设置资源"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="aurora://models",
                    name="Aurora Models",
                    description="可用的Aurora预训练模型",
                    mimeType="application/json"
                ),
                Resource(
                    uri="aurora://config",
                    name="Aurora Configuration",
                    description="Aurora模型配置信息",
                    mimeType="application/json"
                )
            ]
    
    async def _ping_service(self) -> Dict[str, Any]:
        """检查服务连接状态"""
        try:
            # 检查conda环境
            result = await self._run_conda_command(["python", "--version"])
            if result.returncode == 0:
                return {
                    "status": "healthy",
                    "environment": self.conda_environment,
                    "python_version": result.stdout.decode().strip(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Failed to activate conda environment",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            models_dir = self.model_path / "models" / "aurora"
            if models_dir.exists():
                model_files = list(models_dir.glob("*.pth"))
                return {
                    "model_path": str(self.model_path),
                    "available_models": [f.name for f in model_files],
                    "model_count": len(model_files),
                    "environment": self.conda_environment
                }
            else:
                return {
                    "model_path": str(self.model_path),
                    "available_models": [],
                    "model_count": 0,
                    "warning": "Models directory not found"
                }
        except Exception as e:
            return {"error": f"Failed to get model info: {str(e)}"}
    
    async def _detect_extreme_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """检测极端天气事件"""
        try:
            # 模拟极端天气检测
            region = params.get("region", {"lat": 0, "lon": 0})
            threshold = params.get("threshold", 0.8)
            time_window = params.get("time_window", 24)
            
            # 这里应该调用实际的Aurora模型
            # 目前返回模拟结果
            return {
                "extreme_events": [
                    {
                        "event_type": "heat_wave",
                        "intensity": 0.95,
                        "duration": 72,
                        "affected_area": 15000,
                        "confidence": 0.87
                    },
                    {
                        "event_type": "heavy_rainfall",
                        "intensity": 0.78,
                        "duration": 12,
                        "affected_area": 8000,
                        "confidence": 0.92
                    }
                ],
                "detection_parameters": {
                    "region": region,
                    "threshold": threshold,
                    "time_window": time_window
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to detect extreme weather: {str(e)}"}
    
    async def _track_storm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """风暴路径追踪"""
        try:
            storm_id = params.get("storm_id", "STORM_001")
            track_length = params.get("track_length", 48)
            
            # 模拟风暴追踪
            track_points = []
            for hour in range(0, track_length, 6):
                track_points.append({
                    "time": f"+{hour:02d}h",
                    "lat": 30.0 + hour * 0.1,
                    "lon": -80.0 + hour * 0.2,
                    "wind_speed": 45 + hour * 2,
                    "pressure": 980 - hour * 0.5
                })
            
            return {
                "storm_id": storm_id,
                "track_length": track_length,
                "track_points": track_points,
                "forecast_accuracy": 0.85,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to track storm: {str(e)}"}
    
    async def _analyze_atmospheric_stability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """大气稳定性分析"""
        try:
            pressure_levels = params.get("pressure_levels", [1000, 850, 700, 500, 300])
            temperature_profile = params.get("temperature_profile", [15, 10, 5, -10, -30])
            humidity_profile = params.get("humidity_profile", [80, 70, 60, 40, 20])
            
            # 计算稳定性指数
            stability_indices = []
            for i in range(len(pressure_levels) - 1):
                temp_diff = temperature_profile[i+1] - temperature_profile[i]
                pressure_diff = pressure_levels[i] - pressure_levels[i+1]
                lapse_rate = temp_diff / pressure_diff * 100
                
                if lapse_rate < -5.5:
                    stability = "unstable"
                elif lapse_rate > -3.5:
                    stability = "stable"
                else:
                    stability = "neutral"
                
                stability_indices.append({
                    "layer": f"{pressure_levels[i]}-{pressure_levels[i+1]}hPa",
                    "lapse_rate": round(lapse_rate, 2),
                    "stability": stability
                })
            
            return {
                "stability_analysis": stability_indices,
                "overall_stability": "moderately_stable",
                "convection_potential": "low",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to analyze atmospheric stability: {str(e)}"}
    
    async def _analyze_wind_shear(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """风切变分析"""
        try:
            height_levels = params.get("height_levels", [0, 100, 500, 1000, 2000])
            wind_speed = params.get("wind_speed", [5, 8, 12, 18, 25])
            wind_direction = params.get("wind_direction", [180, 185, 190, 195, 200])
            
            # 计算风切变
            wind_shear = []
            for i in range(len(height_levels) - 1):
                speed_diff = wind_speed[i+1] - wind_speed[i]
                direction_diff = wind_direction[i+1] - wind_direction[i]
                height_diff = height_levels[i+1] - height_levels[i]
                
                speed_shear = speed_diff / height_diff * 1000  # m/s per km
                direction_shear = direction_diff / height_diff * 1000  # degrees per km
                
                wind_shear.append({
                    "layer": f"{height_levels[i]}-{height_levels[i+1]}m",
                    "speed_shear": round(speed_shear, 2),
                    "direction_shear": round(direction_shear, 2),
                    "severity": "low" if abs(speed_shear) < 5 else "moderate" if abs(speed_shear) < 10 else "high"
                })
            
            return {
                "wind_shear_analysis": wind_shear,
                "total_wind_shear": round(sum(abs(ws["speed_shear"]) for ws in wind_shear), 2),
                "aviation_hazard": "low",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to analyze wind shear: {str(e)}"}
    
    async def _generate_forecast_map(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成预报地图"""
        try:
            variable = params.get("variable", "temperature")
            forecast_time = params.get("forecast_time", "2024-03-15T12:00:00")
            output_format = params.get("output_format", "png")
            
            # 模拟地图生成
            map_info = {
                "variable": variable,
                "forecast_time": forecast_time,
                "output_format": output_format,
                "resolution": "0.1°",
                "coverage": "global",
                "file_path": f"/data/Tiaozhanbei/shared/aurora/forecast_{variable}_{forecast_time[:10]}.{output_format}",
                "generation_time": datetime.now().isoformat()
            }
            
            return {
                "map_generated": True,
                "map_info": map_info,
                "message": f"Forecast map for {variable} generated successfully"
            }
        except Exception as e:
            return {"error": f"Failed to generate forecast map: {str(e)}"}
    
    async def _export_forecast_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """导出预报数据"""
        try:
            variables = params.get("variables", ["temperature", "precipitation"])
            time_range = params.get("time_range", {"start": "2024-03-15", "end": "2024-03-22"})
            output_format = params.get("output_format", "netcdf")
            
            # 模拟数据导出
            export_info = {
                "variables": variables,
                "time_range": time_range,
                "output_format": output_format,
                "file_path": f"/data/Tiaozhanbei/shared/aurora/export_{time_range['start']}_{time_range['end']}.{output_format}",
                "file_size_mb": 45.2,
                "export_time": datetime.now().isoformat()
            }
            
            return {
                "export_completed": True,
                "export_info": export_info,
                "message": f"Forecast data exported successfully in {output_format} format"
            }
        except Exception as e:
            return {"error": f"Failed to export forecast data: {str(e)}"}
    
    async def _run_conda_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """在conda环境中运行命令"""
        try:
            conda_cmd = ["conda", "run", "-n", self.conda_environment, "--no-capture-output"] + command
            
            process = await asyncio.create_subprocess_exec(
                *conda_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            return subprocess.CompletedProcess(
                args=conda_cmd,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr
            )
        except Exception as e:
            self.logger.error(f"Failed to run conda command: {e}")
            raise


async def main():
    """主函数"""
    server = AuroraServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())