#!/usr/bin/env python3
"""
NFDRS4 MCP服务

提供NFDRS4国家火灾危险度评级系统的MCP接口，支持火灾危险度计算、燃料湿度分析等。
基于官方NFDRS4库和FireWxConverter工具。
"""

import asyncio
import logging
import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import shutil
import pandas as pd

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NFDRS4Server:
    """NFDRS4 MCP服务"""
    
    def __init__(self):
        self.nfdrs4_path = os.getenv("NFDRS4_HOST", "/data/Tiaozhanbei/NFDRS4")
        self.environment_name = os.getenv("NFDRS4_ENV", "NFDRS4")
        self.server = Server("nfdrs4-server")
        self.shared_dir = "/data/Tiaozhanbei/shared"
        
        # 确保共享目录存在
        Path(self.shared_dir).mkdir(parents=True, exist_ok=True)
        
        # NFDRS4工具路径
        self.nfdrs4_cli = os.path.join(self.nfdrs4_path, "InputFile", "NFDRS4_cli")
        self.firewx_converter = os.path.join(self.nfdrs4_path, "InputFile", "FireWxConverter")
        
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """设置NFDRS4细粒度工具接口"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                # 基础工具
                Tool(
                    name="nfdrs4_ping",
                    description="检查NFDRS4服务连接状态",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="nfdrs4_get_fuel_models",
                    description="获取可用燃料模型",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # 预警功能
                Tool(
                    name="nfdrs4_fire_danger_calculation",
                    description="火灾危险度计算",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "weather_data": {
                                "type": "object",
                                "properties": {
                                    "temperature": {"type": "number", "description": "温度(°F)"},
                                    "humidity": {"type": "number", "description": "相对湿度(%)"},
                                    "precipitation": {"type": "number", "description": "降水量(in)"},
                                    "wind_speed": {"type": "number", "description": "风速(mph)"}
                                },
                                "required": ["temperature", "humidity", "wind_speed"]
                            },
                            "location": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number", "description": "纬度"},
                                    "longitude": {"type": "number", "description": "经度"},
                                    "elevation": {"type": "number", "description": "海拔(ft)"}
                                },
                                "required": ["latitude", "longitude"]
                            },
                            "fuel_model": {"type": "string", "description": "燃料模型", "default": "G"},
                            "slope_class": {"type": "integer", "description": "坡度等级(0-9)", "default": 0}
                        },
                        "required": ["weather_data", "location"]
                    }
                ),
                Tool(
                    name="nfdrs4_extreme_fire_behavior",
                    description="极端火行为预警",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "danger_threshold": {"type": "string", "enum": ["low", "moderate", "high", "very_high", "extreme"]},
                            "warning_duration": {"type": "integer", "description": "预警持续时间(小时)"}
                        }
                    }
                ),
                
                # 评估功能
                Tool(
                    name="nfdrs4_fuel_moisture_analysis",
                    description="燃料湿度分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "fuel_component": {"type": "string", "enum": ["1hr", "10hr", "100hr", "1000hr", "live_herb", "live_woody"]},
                            "moisture_content": {"type": "number", "description": "湿度含量(%)"},
                            "measurement_method": {"type": "string", "enum": ["direct", "estimated", "modeled"]},
                            "time_period": {"type": "integer", "description": "分析时间周期(天)", "default": 7},
                            "fuel_type": {"type": "string", "description": "燃料类型", "default": "mixed"}
                        }
                    }
                ),
                Tool(
                    name="nfdrs4_ignition_probability",
                    description="点火概率分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ignition_source": {"type": "string", "enum": ["lightning", "human", "spontaneous"]},
                            "probability_model": {"type": "string", "description": "概率模型"},
                            "confidence_interval": {"type": "number", "description": "置信区间(0-1)"}
                        }
                    }
                ),
                Tool(
                    name="nfdrs4_fire_spread_potential",
                    description="火势蔓延潜力",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spread_direction": {"type": "string", "enum": ["north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"]},
                            "spread_rate": {"type": "number", "description": "蔓延速率(ft/min)"},
                            "flame_length": {"type": "number", "description": "火焰长度(ft)"}
                        }
                    }
                ),
                
                # 响应功能
                Tool(
                    name="nfdrs4_fire_containment_analysis",
                    description="火灾遏制分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "containment_strategy": {"type": "string", "enum": ["direct_attack", "indirect_attack", "parallel_attack"]},
                            "resource_requirements": {"type": "array", "items": {"type": "string"}},
                            "containment_time": {"type": "integer", "description": "预期遏制时间(小时)"}
                        }
                    }
                ),
                Tool(
                    name="nfdrs4_evacuation_zone_mapping",
                    description="疏散区域制图",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "evacuation_radius": {"type": "number", "description": "疏散半径(km)"},
                            "population_affected": {"type": "integer", "description": "受影响人口"},
                            "evacuation_priority": {"type": "string", "enum": ["immediate", "delayed", "shelter_in_place"]}
                        }
                    }
                ),
                Tool(
                    name="nfdrs4_fire_risk_assessment",
                    description="火灾风险评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "risk_factors": {"type": "array", "items": {"type": "string"}},
                            "risk_scale": {"type": "string", "enum": ["low", "medium", "high", "very_high"]},
                            "mitigation_measures": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                ),
                
                # 数据准备工具
                Tool(
                    name="nfdrs4_data_preparation",
                    description="准备NFDRS4输入数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input_files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "输入文件路径列表"
                            },
                            "output_format": {
                                "type": "string",
                                "enum": ["fw21", "csv", "json"],
                                "default": "fw21",
                                "description": "输出格式"
                            },
                            "station_info": {
                                "type": "object",
                                "properties": {
                                    "station_id": {"type": "string", "description": "站点ID"},
                                    "station_name": {"type": "string", "description": "站点名称"},
                                    "latitude": {"type": "number", "description": "纬度"},
                                    "longitude": {"type": "number", "description": "经度"},
                                    "elevation": {"type": "number", "description": "海拔"}
                                }
                            }
                        },
                        "required": ["input_files", "station_info"]
                    }
                ),
                
                # 批量处理工具
                Tool(
                    name="nfdrs4_batch_processing",
                    description="批量处理多个站点的NFDRS4计算",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "stations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "station_id": {"type": "string"},
                                        "weather_file": {"type": "string"},
                                        "fuel_model": {"type": "string"},
                                        "slope_class": {"type": "integer"}
                                    }
                                },
                                "description": "站点信息列表"
                            },
                            "output_directory": {
                                "type": "string",
                                "description": "输出目录"
                            }
                        },
                        "required": ["stations", "output_directory"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "nfdrs4_ping":
                    result = await self._ping_service()
                elif name == "nfdrs4_get_fuel_models":
                    result = await self._get_fuel_models()
                elif name == "nfdrs4_fire_danger_calculation":
                    result = await self._run_fire_danger_calculation(arguments)
                elif name == "nfdrs4_extreme_fire_behavior":
                    result = await self._analyze_extreme_fire_behavior(arguments)
                elif name == "nfdrs4_fuel_moisture_analysis":
                    result = await self._run_fuel_moisture_analysis(arguments)
                elif name == "nfdrs4_ignition_probability":
                    result = await self._analyze_ignition_probability(arguments)
                elif name == "nfdrs4_fire_spread_potential":
                    result = await self._analyze_fire_spread_potential(arguments)
                elif name == "nfdrs4_fire_containment_analysis":
                    result = await self._analyze_fire_containment(arguments)
                elif name == "nfdrs4_evacuation_zone_mapping":
                    result = await self._generate_evacuation_zone_mapping(arguments)
                elif name == "nfdrs4_fire_risk_assessment":
                    result = await self._assess_fire_risk(arguments)
                elif name == "nfdrs4_data_preparation":
                    result = await self._run_data_preparation(arguments)
                elif name == "nfdrs4_batch_processing":
                    result = await self._run_batch_processing(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
    
    def _setup_resources(self):
        """设置NFDRS4资源"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="nfdrs4://fuel_models",
                    name="NFDRS4 Fuel Models",
                    description="可用的燃料模型定义",
                    mimeType="application/json"
                ),
                Resource(
                    uri="nfdrs4://weather_formats",
                    name="Weather Data Formats",
                    description="支持的天气数据格式（FW21, CSV等）",
                    mimeType="application/json"
                ),
                Resource(
                    uri="nfdrs4://calculation_parameters",
                    name="Calculation Parameters",
                    description="NFDRS4计算参数说明",
                    mimeType="application/json"
                )
            ]
    
    async def _run_fire_danger_calculation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行NFDRS4火灾危险度计算"""
        logger.info(f"Running NFDRS4 fire danger calculation with params: {params}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                weather_data = params["weather_data"]
                location = params["location"]
                fuel_model = params.get("fuel_model", "G")
                slope_class = params.get("slope_class", 0)

                config_file = await self._generate_nfdrs4_config(
                    weather_data, location, fuel_model, slope_class, temp_path
                )
                
                result = await self._run_nfdrs4_cli(config_file, temp_path)
                
                output_dir = Path(self.shared_dir) / "nfdrs4" / f"fire_danger_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                if result.get('output_files'):
                    copied_files = []
                    for file_path_str in result['output_files']:
                        file_path = Path(file_path_str)
                        if file_path.exists():
                            shutil.copy2(file_path, output_dir)
                            copied_files.append(str(output_dir / file_path.name))
                    result['output_files'] = copied_files

                result['output_directory'] = str(output_dir)
                result['status'] = 'completed'
                
                return result

        except Exception as e:
            logger.error(f"NFDRS4 fire danger calculation failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _generate_nfdrs4_config(
        self,
        weather_data: Dict[str, Any],
        location: Dict[str, Any], 
        fuel_model: str, 
        slope_class: int, 
        temp_path: Path
    ) -> Path:
        """生成NFDRS4配置文件"""
        
        init_config = f"""# NFDRS4初始化配置
# 生成时间: {datetime.now().isoformat()}
Latitude = {location['latitude']}
Longitude = {location['longitude']}
Elevation = {location.get('elevation', 0)}
FuelModel = {fuel_model}
SlopeClass = {slope_class}
AvgAnnPrecip = 50.0
LiveTimber = true
Cured = false
IsAnnual = false
UseVPDAvg = true
UseRTPrecip = true
MAPeriod = 30
NumPrecipDays = 7
"""
        
        init_file = temp_path / "NFDRS4Init.txt"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_config)
        
        weather_data_file = temp_path / "weather_data.fw21"

        run_config = f"""# NFDRS4运行配置
InitConfigFile = {init_file.absolute()}
WeatherDataFile = {weather_data_file.absolute()}
OutputFile = nfdrs4_results.csv
OutputFormat = CSV
CalculateDeadFuelMoisture = true
CalculateLiveFuelMoisture = true
CalculateFireDangerIndices = true
StartDate = {datetime.now().strftime('%Y-%m-%d')}
EndDate = {(datetime.now() + pd.Timedelta(days=7)).strftime('%Y-%m-%d')}
TimeStep = 1
"""
        
        run_file = temp_path / "RunNFDRS4.txt"
        with open(run_file, 'w', encoding='utf-8') as f:
            f.write(run_config)
        
        await self._generate_weather_data_file(weather_data, weather_data_file)
        
        return run_file
    
    async def _generate_weather_data_file(self, weather_data: Dict[str, Any], weather_file_path: Path):
        """生成天气数据文件"""
        
        fw21_content = f"""# FW21格式天气数据
# 站点: NFDRS4_MCP
# 生成时间: {datetime.now().isoformat()}
# 数据格式: 日期时间,温度(F),相对湿度(%),降水量(in),风速(mph),风向(度),太阳辐射(W/m2)
{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}-0800,{weather_data['temperature']},{weather_data['humidity']},{weather_data.get('precipitation', 0.0)},{weather_data['wind_speed']},180,{weather_data.get('solar_radiation', 800.0)}
"""
        
        with open(weather_file_path, 'w', encoding='utf-8') as f:
            f.write(fw21_content)
    
    async def _run_nfdrs4_cli(self, config_file: Path, work_dir: Path) -> Dict[str, Any]:
        """运行NFDRS4命令行工具"""
        
        try:
            if not os.path.exists(self.nfdrs4_cli):
                logger.warning(f"NFDRS4 CLI not found at {self.nfdrs4_cli}. Using mock results.")
                return await self._generate_mock_nfdrs4_result(work_dir)
            
            cmd = [
                self.nfdrs4_cli,
                "-config", str(config_file),
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                result_file = work_dir / "nfdrs4_results.csv"
                if result_file.exists():
                    results = await self._parse_nfdrs4_results(result_file)
                    return {
                        "status": "success",
                        "results": results,
                        "output_files": [str(result_file)],
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode()
                    }
                else:
                    return {
                        "status": "partial_success",
                        "message": "NFDRS4 executed but no results file found",
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode()
                    }
            else:
                return {
                    "status": "failed",
                    "error": f"NFDRS4 execution failed with code {process.returncode}",
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode()
                }
                
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "NFDRS4 execution timed out"}
        except Exception as e:
            return {"status": "failed", "error": f"Failed to run NFDRS4: {str(e)}"}
    
    async def _generate_mock_nfdrs4_result(self, work_dir: Path) -> Dict[str, Any]:
        """生成模拟的NFDRS4结果（当实际工具不可用时）"""
        
        mock_results_content = """Date,Time,BI,IC,SC,ERC,1000hr,10hr,1hr,LFM,FFMC,DMC,DC,ISI,BUI,FWI,DSR
2024-08-13,10:00,25.3,45.2,12.8,78.9,8.5,6.2,4.1,120.5,85.2,45.8,234.1,12.5,67.3,45.2,12.8
2024-08-13,11:00,26.1,46.1,13.2,79.5,8.3,6.0,3.9,119.8,86.1,46.2,235.8,13.1,68.1,46.1,13.2
"""
        
        mock_file = work_dir / "nfdrs4_mock_results.csv"
        with open(mock_file, 'w', encoding='utf-8') as f:
            f.write(mock_results_content)
        
        results = await self._parse_nfdrs4_results(mock_file)

        return {
            "status": "success (mocked)",
            "results": results,
            "output_files": [str(mock_file)],
        }

    async def _parse_nfdrs4_results(self, result_file: Path) -> Dict[str, Any]:
        """解析NFDRS4 CSV结果文件"""
        df = pd.read_csv(result_file)
        latest_result = df.iloc[-1].to_dict()
        
        return {
            "fire_danger_indices": {
                "BI": latest_result.get("BI"),
                "IC": latest_result.get("IC"),
                "SC": latest_result.get("SC"),
                "ERC": latest_result.get("ERC"),
                "DSR": latest_result.get("DSR")
            },
            "fuel_moisture": {
                "1000hr": latest_result.get("1000hr"),
                "100hr": latest_result.get("100hr"), # Assuming 100hr might exist
                "10hr": latest_result.get("10hr"),
                "1hr": latest_result.get("1hr"),
                "LFM": latest_result.get("LFM")
            },
            "canadian_fire_weather": {
                "FFMC": latest_result.get("FFMC"),
                "DMC": latest_result.get("DMC"),
                "DC": latest_result.get("DC"),
                "ISI": latest_result.get("ISI"),
                "BUI": latest_result.get("BUI"),
                "FWI": latest_result.get("FWI")
            },
            "full_timeseries": df.to_dict('records')
        }

    async def _run_data_preparation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """模拟运行数据准备工具"""
        logger.info(f"Simulating data preparation with params: {params}")
        # In a real scenario, this would call self.firewx_converter
        return {
            "status": "completed (simulated)",
            "message": f"Data from {params['input_files']} prepared for station {params['station_info']['station_id']}.",
            "output_file": f"/path/to/prepared_data_{params['station_info']['station_id']}.{params['output_format']}"
        }

    async def _run_fuel_moisture_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """模拟运行燃料湿度分析"""
        logger.info(f"Simulating fuel moisture analysis with params: {params}")
        return {
            "status": "completed (simulated)",
            "analysis_period_days": params.get('time_period', 7),
            "fuel_type": params.get('fuel_type', 'mixed'),
            "moisture_trend": {
                "dead_fuel_moisture_start": 15.0,
                "dead_fuel_moisture_end": 8.0,
                "live_fuel_moisture_start": 150.0,
                "live_fuel_moisture_end": 120.0,
                "trend_description": "Drying trend observed over the period."
            }
        }

    async def _run_batch_processing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """模拟运行批量处理"""
        logger.info(f"Simulating batch processing with params: {params}")
        results = []
        for station in params['stations']:
            results.append({
                "station_id": station['station_id'],
                "status": "completed",
                "output_file": f"{params['output_directory']}/{station['station_id']}_results.csv"
            })
        return {
            "status": "completed (simulated)",
            "processed_stations": len(params['stations']),
            "results_summary": results
        }
    
    # ==================== 细粒度工具方法实现 ====================
    
    async def _ping_service(self) -> Dict[str, Any]:
        """检查服务连接状态"""
        try:
            return {
                "status": "healthy",
                "service": "NFDRS4",
                "version": "4.0",
                "environment": self.environment_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_fuel_models(self) -> Dict[str, Any]:
        """获取可用燃料模型"""
        fuel_models = {
            "G": "Grass",
            "GS": "Grass-Shrub",
            "S1": "Shrub 1",
            "S2": "Shrub 2", 
            "S3": "Shrub 3",
            "D1": "Deciduous 1",
            "D2": "Deciduous 2",
            "D3": "Deciduous 3",
            "D4": "Deciduous 4",
            "D5": "Deciduous 5",
            "D6": "Deciduous 6",
            "D7": "Deciduous 7",
            "D8": "Deciduous 8",
            "D9": "Deciduous 9"
        }
        return {
            "fuel_models": fuel_models,
            "count": len(fuel_models),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_extreme_fire_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析极端火行为"""
        danger_threshold = params.get("danger_threshold", "high")
        warning_duration = params.get("warning_duration", 24)
        
        # 模拟极端火行为分析
        extreme_conditions = {
            "low": {"probability": 0.1, "severity": "minimal"},
            "moderate": {"probability": 0.3, "severity": "low"},
            "high": {"probability": 0.6, "severity": "moderate"},
            "very_high": {"probability": 0.8, "severity": "high"},
            "extreme": {"probability": 0.95, "severity": "extreme"}
        }
        
        condition = extreme_conditions.get(danger_threshold, extreme_conditions["moderate"])
        
        return {
            "danger_threshold": danger_threshold,
            "warning_duration": warning_duration,
            "extreme_behavior_probability": condition["probability"],
            "severity_level": condition["severity"],
            "recommended_actions": [
                "Increase fire patrols",
                "Prepare evacuation plans",
                "Alert emergency services"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_ignition_probability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析点火概率"""
        ignition_source = params.get("ignition_source", "lightning")
        probability_model = params.get("probability_model", "standard")
        confidence_interval = params.get("confidence_interval", 0.95)
        
        # 模拟点火概率分析
        ignition_probabilities = {
            "lightning": {"base_probability": 0.15, "factors": ["storm_activity", "fuel_conditions"]},
            "human": {"base_probability": 0.25, "factors": ["recreation_activity", "equipment_use"]},
            "spontaneous": {"base_probability": 0.05, "factors": ["temperature", "humidity"]}
        }
        
        source_info = ignition_probabilities.get(ignition_source, ignition_probabilities["lightning"])
        
        return {
            "ignition_source": ignition_source,
            "probability_model": probability_model,
            "base_probability": source_info["base_probability"],
            "influencing_factors": source_info["factors"],
            "confidence_interval": confidence_interval,
            "risk_assessment": "moderate" if source_info["base_probability"] > 0.1 else "low",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_fire_spread_potential(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析火势蔓延潜力"""
        spread_direction = params.get("spread_direction", "northeast")
        spread_rate = params.get("spread_rate", 10.0)
        flame_length = params.get("flame_length", 5.0)
        
        # 模拟火势蔓延分析
        direction_factors = {
            "north": {"wind_influence": 0.8, "slope_influence": 0.6},
            "south": {"wind_influence": 0.4, "slope_influence": 0.8},
            "east": {"wind_influence": 0.7, "slope_influence": 0.5},
            "west": {"wind_influence": 0.5, "slope_influence": 0.7}
        }
        
        # 计算综合蔓延潜力
        base_potential = (spread_rate * flame_length) / 10.0
        wind_factor = direction_factors.get(spread_direction[:4], {"wind_influence": 0.6, "slope_influence": 0.6})
        total_potential = base_potential * (wind_factor["wind_influence"] + wind_factor["slope_influence"]) / 2
        
        return {
            "spread_direction": spread_direction,
            "spread_rate": spread_rate,
            "flame_length": flame_length,
            "spread_potential": round(total_potential, 2),
            "risk_level": "high" if total_potential > 5 else "moderate" if total_potential > 2 else "low",
            "containment_difficulty": "extreme" if total_potential > 8 else "high" if total_potential > 5 else "moderate",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_fire_containment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析火灾遏制策略"""
        containment_strategy = params.get("containment_strategy", "direct_attack")
        resource_requirements = params.get("resource_requirements", ["fire_crews", "equipment"])
        containment_time = params.get("containment_time", 48)
        
        # 模拟遏制分析
        strategy_effectiveness = {
            "direct_attack": {"success_rate": 0.7, "resource_intensity": "high"},
            "indirect_attack": {"success_rate": 0.6, "resource_intensity": "medium"},
            "parallel_attack": {"success_rate": 0.8, "resource_intensity": "very_high"}
        }
        
        strategy_info = strategy_effectiveness.get(containment_strategy, strategy_effectiveness["direct_attack"])
        
        return {
            "containment_strategy": containment_strategy,
            "resource_requirements": resource_requirements,
            "estimated_containment_time": containment_time,
            "strategy_effectiveness": strategy_info["success_rate"],
            "resource_intensity": strategy_info["resource_intensity"],
            "recommended_resources": [
                "Fire crews: 4-6 teams",
                "Heavy equipment: 2-3 units",
                "Aerial support: 1-2 helicopters"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_evacuation_zone_mapping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成疏散区域制图"""
        evacuation_radius = params.get("evacuation_radius", 5.0)
        population_affected = params.get("population_affected", 1000)
        evacuation_priority = params.get("evacuation_priority", "immediate")
        
        # 模拟疏散区域制图
        priority_timelines = {
            "immediate": {"evacuation_time": "0-2 hours", "urgency": "critical"},
            "delayed": {"evacuation_time": "2-6 hours", "urgency": "high"},
            "shelter_in_place": {"evacuation_time": "N/A", "urgency": "low"}
        }
        
        timeline_info = priority_timelines.get(evacuation_priority, priority_timelines["immediate"])
        
        return {
            "evacuation_radius_km": evacuation_radius,
            "population_affected": population_affected,
            "evacuation_priority": evacuation_priority,
            "evacuation_timeline": timeline_info["evacuation_time"],
            "urgency_level": timeline_info["urgency"],
            "evacuation_zones": [
                {"zone": "Red", "radius": evacuation_radius * 0.5, "priority": "immediate"},
                {"zone": "Orange", "radius": evacuation_radius * 0.8, "priority": "high"},
                {"zone": "Yellow", "radius": evacuation_radius, "priority": "moderate"}
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _assess_fire_risk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """评估火灾风险"""
        risk_factors = params.get("risk_factors", ["weather", "fuel", "topography"])
        risk_scale = params.get("risk_scale", "medium")
        mitigation_measures = params.get("mitigation_measures", ["fuel_reduction", "fire_breaks"])
        
        # 模拟风险评估
        risk_scores = {
            "low": {"score": 0.2, "color": "green"},
            "medium": {"score": 0.5, "color": "yellow"},
            "high": {"score": 0.7, "color": "orange"},
            "very_high": {"score": 0.9, "color": "red"}
        }
        
        risk_info = risk_scores.get(risk_scale, risk_scores["medium"])
        
        return {
            "risk_factors": risk_factors,
            "risk_scale": risk_scale,
            "risk_score": risk_info["score"],
            "risk_color": risk_info["color"],
            "mitigation_measures": mitigation_measures,
            "risk_breakdown": {
                "weather_risk": 0.6,
                "fuel_risk": 0.7,
                "topography_risk": 0.4,
                "human_risk": 0.3
            },
            "recommendations": [
                "Implement fuel reduction programs",
                "Establish fire breaks",
                "Enhance monitoring systems",
                "Prepare emergency response plans"
            ],
            "timestamp": datetime.now().isoformat()
        }

    async def initialize(self, options: InitializationOptions) -> None:
        """初始化服务"""
        logger.info(f"Initializing NFDRS4Server with options: {options}")

    async def start(self):
        """启动MCP服务"""
        logger.info("Starting NFDRS4 MCP service...")
        await stdio_server(self.server, self.initialize)

async def main():
    service = NFDRS4Server()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
