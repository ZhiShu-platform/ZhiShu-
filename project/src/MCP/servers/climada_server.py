#!/usr/bin/env python3
"""
CLIMADA MCP服务

提供CLIMADA气候风险评估模型的MCP接口，支持影响评估、灾害建模、成本效益分析等。
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

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CliMadaService:
    """CLIMADA MCP服务"""

    def __init__(self):
        self.climada_path = os.getenv("CLIMADA_HOST", "/data/Tiaozhanbei/Climada")
        self.environment_name = os.getenv("CLIMADA_ENV", "Climada")
        self.server = Server("climada-service")
        self.shared_dir = "/data/Tiaozhanbei/shared"

        # 确保共享目录存在
        Path(self.shared_dir).mkdir(parents=True, exist_ok=True)

        self._setup_tools()
        self._setup_resources()

    def _setup_tools(self):
        """设置CLIMADA细粒度工具接口"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                # 基础工具
                Tool(
                    name="climada_ping",
                    description="检查CLIMADA服务连接状态",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="climada_get_environment_info",
                    description="获取CLIMADA环境信息",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # 预警功能
                Tool(
                    name="climada_hazard_detection",
                    description="灾害事件检测",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hazard_type": {"type": "string", "enum": ["tropical_cyclone", "flood", "drought", "heatwave"]},
                            "intensity_threshold": {"type": "number", "description": "强度阈值"},
                            "spatial_resolution": {"type": "string", "description": "空间分辨率"}
                        }
                    }
                ),
                Tool(
                    name="climada_early_warning",
                    description="早期预警系统",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "warning_type": {"type": "string", "enum": ["immediate", "short_term", "medium_term"]},
                            "confidence_level": {"type": "number", "description": "置信度(0-1)"}
                        }
                    }
                ),
                
                # ==================== 精准识别灾情 ====================
                
                # 灾害事件检测
                Tool(
                    name="climada_hazard_detection",
                    description="精准检测灾害事件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hazard_type": {
                                "type": "string", 
                                "enum": ["tropical_cyclone", "flood", "drought", "heatwave", "wildfire", "storm_surge"],
                                "description": "灾害类型"
                            },
                            "detection_method": {
                                "type": "string",
                                "enum": ["satellite", "ground_station", "model_output", "combined"],
                                "description": "检测方法"
                            },
                            "spatial_resolution": {
                                "type": "string",
                                "enum": ["0.1deg", "0.25deg", "0.5deg", "1deg"],
                                "description": "空间分辨率"
                            },
                            "temporal_resolution": {
                                "type": "string",
                                "enum": ["hourly", "daily", "monthly"],
                                "description": "时间分辨率"
                            },
                            "intensity_threshold": {
                                "type": "number",
                                "description": "强度阈值"
                            }
                        },
                        "required": ["hazard_type", "detection_method"]
                    }
                ),
                
                # 早期预警系统
                Tool(
                    name="climada_early_warning",
                    description="灾害早期预警",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "warning_type": {
                                "type": "string", 
                                "enum": ["immediate", "short_term", "medium_term", "long_term"],
                                "description": "预警类型"
                            },
                            "warning_level": {
                                "type": "string",
                                "enum": ["blue", "yellow", "orange", "red"],
                                "description": "预警等级"
                            },
                            "confidence_level": {
                                "type": "number", 
                                "description": "置信度(0-1)",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "lead_time": {
                                "type": "integer",
                                "description": "提前预警时间(小时)",
                                "minimum": 1,
                                "maximum": 168
                            }
                        },
                        "required": ["warning_type", "warning_level"]
                    }
                ),
                
                # ==================== 量化评估风险 ====================
                
                # 暴露度分析
                Tool(
                    name="climada_exposure_analysis",
                    description="暴露度分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "exposure_type": {
                                "type": "string",
                                "enum": ["population", "infrastructure", "agriculture", "ecosystem", "economic_assets"],
                                "description": "暴露类型"
                            },
                            "spatial_scale": {
                                "type": "string",
                                "enum": ["country", "province", "city", "district", "grid"],
                                "description": "空间尺度"
                            },
                            "temporal_scale": {
                                "type": "string",
                                "enum": ["annual", "seasonal", "monthly", "event_based"],
                                "description": "时间尺度"
                            },
                            "vulnerability_factors": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["age", "income", "education", "infrastructure_quality", "access_to_services"]
                                },
                                "description": "脆弱性因子"
                            }
                        },
                        "required": ["exposure_type", "spatial_scale"]
                    }
                ),
                
                # 脆弱性评估
                Tool(
                    name="climada_vulnerability_assessment",
                    description="脆弱性评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vulnerability_dimensions": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["physical", "social", "economic", "environmental", "institutional"]
                                },
                                "description": "脆弱性维度"
                            },
                            "assessment_method": {
                                "type": "string",
                                "enum": ["index_based", "indicator_based", "expert_judgment", "statistical"],
                                "description": "评估方法"
                            },
                            "vulnerability_indicators": {
                                "type": "object",
                                "properties": {
                                    "sensitivity": {"type": "number", "description": "敏感性指数(0-1)"},
                                    "adaptive_capacity": {"type": "number", "description": "适应能力指数(0-1)"},
                                    "exposure_level": {"type": "number", "description": "暴露水平指数(0-1)"}
                                }
                            }
                        },
                        "required": ["vulnerability_dimensions"]
                    }
                ),
                
                # 风险量化
                Tool(
                    name="climada_risk_quantification",
                    description="风险量化评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "risk_metrics": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["expected_annual_loss", "value_at_risk", "probable_maximum_loss", "risk_curve"]
                                },
                                "description": "风险指标"
                            },
                            "time_horizon": {
                                "type": "integer",
                                "description": "时间范围(年)",
                                "minimum": 1,
                                "maximum": 100
                            },
                            "confidence_intervals": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "置信区间",
                                "default": [0.05, 0.5, 0.95]
                            },
                            "uncertainty_analysis": {
                                "type": "boolean",
                                "description": "是否进行不确定性分析"
                            }
                        },
                        "required": ["risk_metrics"]
                    }
                ),
                
                # ==================== 主动协同调度 ====================
                
                # 影响评估
                Tool(
                    name="climada_impact_assessment",
                    description="灾害影响评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "impact_categories": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["direct_damage", "indirect_losses", "cascading_effects", "recovery_costs"]
                                },
                                "description": "影响类别"
                            },
                            "assessment_methodology": {
                                "type": "string",
                                "enum": ["damage_functions", "empirical_models", "expert_estimation", "hybrid"],
                                "description": "评估方法"
                            },
                            "economic_valuation": {
                                "type": "object",
                                "properties": {
                                    "currency": {"type": "string", "default": "CNY"},
                                    "price_year": {"type": "integer", "description": "价格基准年"},
                                    "discount_rate": {"type": "number", "description": "贴现率", "default": 0.05}
                                }
                            }
                        },
                        "required": ["impact_categories"]
                    }
                ),
                
                # 适应策略评估
                Tool(
                    name="climada_adaptation_assessment",
                    description="适应策略评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "adaptation_options": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["infrastructure_upgrade", "early_warning_system", "land_use_planning", "capacity_building"]
                                },
                                "description": "适应选项"
                            },
                            "evaluation_criteria": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["cost_effectiveness", "feasibility", "co_benefits", "robustness"]
                                },
                                "description": "评估标准"
                            },
                            "time_horizon": {
                                "type": "integer",
                                "description": "评估时间范围(年)",
                                "minimum": 5,
                                "maximum": 50
                            }
                        },
                        "required": ["adaptation_options"]
                    }
                ),
                
                # 成本效益分析
                Tool(
                    name="climada_cost_benefit_analysis",
                    description="成本效益分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "intervention_options": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "description": "干预选项名称"
                                },
                                "description": "干预选项"
                            },
                            "analysis_period": {
                                "type": "integer",
                                "description": "分析周期(年)",
                                "minimum": 10,
                                "maximum": 100
                            },
                            "discount_rate": {
                                "type": "number",
                                "description": "社会贴现率",
                                "default": 0.03
                            },
                            "sensitivity_analysis": {
                                "type": "boolean",
                                "description": "是否进行敏感性分析"
                            }
                        },
                        "required": ["intervention_options"]
                    }
                ),
                
                # ==================== 量化评估灾损 ====================
                
                # 损失评估
                Tool(
                    name="climada_loss_assessment",
                    description="灾害损失量化评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "loss_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["property_damage", "business_interruption", "infrastructure_damage", "agricultural_losses", "human_health"]
                                },
                                "description": "损失类型"
                            },
                            "assessment_method": {
                                "type": "string",
                                "enum": ["damage_functions", "empirical_models", "expert_judgment", "hybrid_approach"],
                                "description": "评估方法"
                            },
                            "spatial_resolution": {
                                "type": "string",
                                "enum": ["national", "provincial", "city", "district", "grid"],
                                "description": "空间分辨率"
                            },
                            "temporal_resolution": {
                                "type": "string",
                                "enum": ["annual", "seasonal", "monthly", "event_based"],
                                "description": "时间分辨率"
                            }
                        },
                        "required": ["loss_types", "assessment_method"]
                    }
                ),
                
                # 恢复时间评估
                Tool(
                    name="climada_recovery_assessment",
                    description="恢复时间评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "recovery_phases": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["immediate_response", "short_term_recovery", "long_term_recovery", "reconstruction"]
                                },
                                "description": "恢复阶段"
                            },
                            "recovery_factors": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["infrastructure_resilience", "financial_resources", "institutional_capacity", "social_cohesion"]
                                },
                                "description": "恢复因子"
                            },
                            "time_estimation": {
                                "type": "string",
                                "enum": ["deterministic", "probabilistic", "scenario_based"],
                                "description": "时间估算方法"
                            }
                        },
                        "required": ["recovery_phases"]
                    }
                ),
                
                # 社会经济影响评估
                Tool(
                    name="climada_socioeconomic_impact",
                    description="社会经济影响评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "impact_domains": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["gdp_impact", "employment_impact", "poverty_impact", "inequality_impact", "migration_impact"]
                                },
                                "description": "影响领域"
                            },
                            "assessment_scale": {
                                "type": "string",
                                "enum": ["household", "community", "regional", "national"],
                                "description": "评估尺度"
                            },
                            "time_horizon": {
                                "type": "integer",
                                "description": "评估时间范围(年)",
                                "minimum": 1,
                                "maximum": 50
                            }
                        },
                        "required": ["impact_domains"]
                    }
                ),
                
                # 基础工具
                Tool(
                    name="climada_ping",
                    description="检查CLIMADA服务连接状态",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                Tool(
                    name="climada_get_environment_info",
                    description="获取CLIMADA环境信息",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # 原有工具保留
                Tool(
                    name="climada_exposure_analysis",
                    description="暴露度分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "exposure_type": {"type": "string", "enum": ["population", "infrastructure", "agriculture", "economic"]},
                            "spatial_unit": {"type": "string", "description": "空间单元"},
                            "temporal_resolution": {"type": "string", "description": "时间分辨率"}
                        }
                    }
                ),
                Tool(
                    name="climada_vulnerability_assessment",
                    description="脆弱性评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vulnerability_factors": {"type": "array", "items": {"type": "string"}},
                            "weighting_scheme": {"type": "string", "description": "权重方案"}
                        }
                    }
                ),
                Tool(
                    name="climada_risk_quantification",
                    description="风险量化",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "risk_metric": {"type": "string", "enum": ["expected_annual_loss", "probable_maximum_loss", "risk_index"]},
                            "time_horizon": {"type": "integer", "description": "时间范围(年)"},
                            "return_periods": {"type": "array", "items": {"type": "integer"}}
                        }
                    }
                ),
                Tool(
                    name="climada_impact_assessment",
                    description="灾害影响评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hazard_type": {"type": "string", "enum": ["wildfire", "flood", "earthquake", "hurricane", "tropical_cyclone"]},
                            "location": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                            "intensity": {"type": "number", "minimum": 0, "maximum": 1},
                            "exposure_data": {"type": "object"},
                            "vulnerability_function": {"type": "string"}
                        },
                        "required": ["hazard_type", "location", "intensity"]
                    }
                ),
                Tool(
                    name="climada_hazard_modeling",
                    description="灾害建模",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hazard_type": {"type": "string"},
                            "scenario_params": {"type": "object"},
                            "time_horizon": {"type": "integer", "default": 50},
                            "return_periods": {"type": "array", "items": {"type": "integer"}}
                        },
                        "required": ["hazard_type"]
                    }
                ),
                
                # 响应功能
                Tool(
                    name="climada_adaptation_planning",
                    description="适应规划",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "adaptation_type": {"type": "string", "enum": ["structural", "non_structural", "ecosystem"]},
                            "cost_effectiveness": {"type": "boolean", "description": "是否进行成本效益分析"}
                        }
                    }
                ),
                Tool(
                    name="climada_mitigation_strategy",
                    description="减缓策略",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "strategy_type": {"type": "string", "enum": ["emission_reduction", "carbon_sequestration", "efficiency"]},
                            "target_year": {"type": "integer", "description": "目标年份"}
                        }
                    }
                ),
                Tool(
                    name="climada_cost_benefit",
                    description="成本效益分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "measures": {"type": "array", "items": {"type": "string"}},
                            "time_horizon": {"type": "integer", "default": 30},
                            "discount_rate": {"type": "number", "default": 0.03},
                            "baseline_scenario": {"type": "object"},
                            "adaptation_scenario": {"type": "object"}
                        },
                        "required": ["measures"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "climada_ping":
                    result = await self._ping_service()
                elif name == "climada_get_environment_info":
                    result = await self._get_environment_info()
                elif name == "climada_hazard_detection":
                    result = await self._detect_hazard(arguments)
                elif name == "climada_early_warning":
                    result = await self._generate_early_warning(arguments)
                elif name == "climada_exposure_analysis":
                    result = await self._run_exposure_analysis(arguments)
                elif name == "climada_vulnerability_assessment":
                    result = await self._assess_vulnerability(arguments)
                elif name == "climada_risk_quantification":
                    result = await self._quantify_risk(arguments)
                elif name == "climada_impact_assessment":
                    result = await self._run_impact_assessment(arguments)
                elif name == "climada_hazard_modeling":
                    result = await self._run_hazard_modeling(arguments)
                elif name == "climada_adaptation_planning":
                    result = await self._plan_adaptation(arguments)
                elif name == "climada_mitigation_strategy":
                    result = await self._develop_mitigation_strategy(arguments)
                elif name == "climada_cost_benefit":
                    result = await self._run_cost_benefit(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

    def _setup_resources(self):
        """设置CLIMADA资源"""

        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="climada://hazard_sets",
                    name="CLIMADA Hazard Sets",
                    description="可用的灾害数据集",
                    mimeType="application/json"
                ),
                Resource(
                    uri="climada://exposure_data",
                    name="Exposure Data",
                    description="经济暴露数据",
                    mimeType="application/json"
                ),
                Resource(
                    uri="climada://vulnerability_functions",
                    name="Vulnerability Functions",
                    description="不同灾害的损害函数",
                    mimeType="application/json"
                )
            ]

    async def _run_impact_assessment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行CLIMADA影响评估"""
        logger.info(f"Running CLIMADA impact assessment with params: {params}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_content = self._generate_impact_assessment_script(params, temp_path)
            script_file = temp_path / "climada_impact.py"

            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)

            try:
                result = await self._run_in_climada_env(script_file, temp_path)

                output_dir = Path(self.shared_dir) / "climada" / f"impact_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
                logger.error(f"CLIMADA execution failed: {e}")
                return {
                    "error": str(e),
                    "status": "failed"
                }

    def _generate_impact_assessment_script(self, params: Dict[str, Any], temp_path: Path) -> str:
        """生成CLIMADA影响评估脚本"""
        hazard_type = params['hazard_type']
        location = params['location']
        intensity = params['intensity']

        # Note: The original script had some issues with ImpactFunc creation.
        # This version uses a more robust approach and corrects the class names.
        script = f"""
import sys
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

# 添加CLIMADA路径
sys.path.append('{self.climada_path}')

try:
    from climada.entity import Exposures, ImpactFuncSet, ImpactFunc
    from climada.hazard import Hazard
    from climada.engine import Impact
    from climada.util import coordinates as coord_util
    from climada.util import files_handler as fh

    print("CLIMADA imported successfully")

    # 设置工作目录
    work_dir = Path('{temp_path}')
    work_dir.mkdir(exist_ok=True)

    # 参数
    hazard_type = '{hazard_type}'
    lat = {location['lat']}
    lng = {location['lng']}
    intensity_param = {intensity}

    print(f"Processing {{hazard_type}} hazard at ({{lat}}, {{lng}}) with intensity {{intensity_param}}")

    # 创建模拟灾害数据
    hazard = Hazard(haz_type=hazard_type)

    # 设置时间范围（过去10年）
    years = np.arange(2015, 2025)
    hazard.event_name = [f'event_{{y}}' for y in years]
    hazard.date = [int(f'{{y}}0101') for y in years]
    hazard.frequency = np.ones(len(years)) / len(years)
    hazard.event_id = np.arange(1, len(years) + 1)
    
    # 创建网格点
    grid_size = 0.1  # 度
    lats = np.arange(lat - grid_size/2, lat + grid_size/2, grid_size/10)
    lons = np.arange(lng - grid_size/2, lng + grid_size/2, grid_size/10)
    centroids = coord_util.grid_to_centroids(lats, lons)
    hazard.centroids = centroids

    # 设置强度数据（模拟）
    intensity_data = np.random.exponential(intensity_param, size=(len(years), len(centroids.lat)))
    from scipy.sparse import csr_matrix
    hazard.intensity = csr_matrix(intensity_data)
    hazard.check()

    # 创建暴露数据
    print("Creating simulated exposure data")
    exposures = Exposures(pd.DataFrame({{
        'latitude': [lat],
        'longitude': [lng],
        'value': [1000000],  # 1M USD
        'if_': 1 # Impact function ID
    }}))

    # 创建影响函数
    impact_funcs = ImpactFuncSet()
    if_ = ImpactFunc()
    if_.haz_type = hazard_type
    if_.id = 1
    if_.intensity = np.linspace(0, 10, 100)
    if_.mdd = np.ones(100)
    if_.paa = np.geomspace(0.01, 1, 100)
    impact_funcs.append(if_)
    
    # 计算影响
    impact = Impact()
    impact.calc(exposures, impact_funcs, hazard)

    # 保存结果
    results = {{
        'hazard_type': hazard_type,
        'location': {{'lat': lat, 'lng': lng}},
        'intensity': intensity_param,
        'total_impact': float(impact.aai_agg),
        'annual_impacts': impact.imp_mat.sum(axis=1).getA1().tolist(),
        'max_impact': float(impact.at_event.max()),
        'affected_assets': int(np.count_nonzero(impact.at_event)),
        'confidence': 0.8
    }}

    # 保存图表
    output_files = []
    try:
        import matplotlib.pyplot as plt

        # 影响时间序列图
        plt.figure(figsize=(10, 6))
        plt.plot(years, results['annual_impacts'])
        plt.title(f'{{hazard_type.title()}} Impact Over Time')
        plt.xlabel('Year')
        plt.ylabel('Impact (USD)')
        plt.grid(True)
        img_path = work_dir / 'impact_timeline.png'
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        output_files.append(str(img_path))

        # 影响分布图
        if impact.at_event.size > 1:
            plt.figure(figsize=(8, 6))
            plt.hist(impact.at_event, bins=20, alpha=0.7)
            plt.title(f'{{hazard_type.title()}} Impact Distribution')
            plt.xlabel('Impact per Event (USD)')
            plt.ylabel('Frequency')
            plt.grid(True)
            img_path = work_dir / 'impact_distribution.png'
            plt.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()
            output_files.append(str(img_path))

    except Exception as e:
        print(f"Could not generate plots: {{e}}")

    results['output_files'] = output_files
    
    # 保存到文件并打印到stdout
    output_file = work_dir / 'impact_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print("Impact assessment completed successfully")
    print(json.dumps(results, indent=2))

except Exception as e:
    import traceback
    error_info = {{
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(f"Error in CLIMADA execution: {{e}}")
    print(json.dumps(error_info))
    sys.exit(1)
"""
        return script

    async def _run_hazard_modeling(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行CLIMADA灾害建模"""
        logger.info(f"Running CLIMADA hazard modeling with params: {params}")
        # 模拟实现
        return {
            "hazard_type": params["hazard_type"],
            "scenario_results": {
                "return_periods": params.get("return_periods", [5, 10, 25, 50, 100]),
                "intensities": [0.2, 0.4, 0.6, 0.8, 1.0],
                "probabilities": [0.2, 0.1, 0.04, 0.02, 0.01]
            },
            "time_horizon": params.get("time_horizon", 50),
            "confidence": 0.75,
            "status": "completed"
        }

    async def _run_exposure_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行CLIMADA暴露分析"""
        logger.info(f"Running CLIMADA exposure analysis with params: {params}")
        # 模拟实现
        return {
            "country_iso": params["country_iso"],
            "exposure_type": params.get("exposure_type", "litpop"),
            "reference_year": params.get("reference_year", 2020),
            "resolution": params.get("resolution", "10arcsec"),
            "total_exposure": 1000000000,  # 10B USD
            "population": 50000000,
            "status": "completed"
        }

    async def _run_cost_benefit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行CLIMADA成本效益分析"""
        logger.info(f"Running CLIMADA cost-benefit analysis with params: {params}")
        # 模拟实现
        measures = params["measures"]
        total_cost = sum(abs(hash(measure)) % 1000000 for measure in measures)
        total_benefit = sum(abs(hash(measure)) % 1500000 for measure in measures) * 1.5

        return {
            "measures": measures,
            "total_cost": total_cost,
            "total_benefit": total_benefit,
            "benefit_cost_ratio": total_benefit / total_cost if total_cost > 0 else 0,
            "net_present_value": total_benefit - total_cost,
            "time_horizon": params.get("time_horizon", 30),
            "discount_rate": params.get("discount_rate", 0.03),
            "status": "completed"
        }

    async def _run_in_climada_env(self, script_file: Path, work_dir: Path) -> Dict[str, Any]:
        """在指定的conda环境中运行CLIMADA脚本"""
        logger.info(f"Running script {script_file} in env {self.environment_name}")

        command = [
            "conda", "run", "-n", self.environment_name,
            "python", str(script_file)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_message = stderr.decode('utf-8', errors='ignore')
                logger.error(f"Script execution failed:\n{error_message}")
                raise RuntimeError(f"CLIMADA script failed: {error_message}")

            output = stdout.decode('utf-8', errors='ignore')
            logger.info(f"Script output:\n{output}")

            # 从输出中解析JSON结果
            try:
                # Find the last line that looks like a JSON object
                json_output_str = [line for line in output.strip().split('\n') if line.startswith('{')][-1]
                return json.loads(json_output_str)
            except (json.JSONDecodeError, IndexError):
                logger.error("Failed to parse JSON from script stdout, trying file.")
                result_file = work_dir / 'impact_results.json'
                if result_file.exists():
                    with open(result_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                raise ValueError("Could not retrieve results from CLIMADA script.")

        except Exception as e:
            logger.error(f"Error running subprocess: {e}")
            raise

    async def initialize(self, options: InitializationOptions) -> None:
        """初始化服务"""
        logger.info(f"Initializing CliMadaService with options: {options}")
        # 可根据需要添加初始化逻辑

    async def start(self):
        """启动MCP服务"""
        logger.info("Starting CLIMADA MCP service...")
        await stdio_server(self.server, self.initialize)


async def main():
    service = CliMadaService()
    await service.start()


if __name__ == "__main__":
    # To run this script, you would need to have the mcp library installed
    # and a conda environment named "Climada" with climada and its dependencies.
    asyncio.run(main())
