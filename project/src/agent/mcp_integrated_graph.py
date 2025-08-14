"""
集成MCP的智能体工作流

将MCP服务集成到LangGraph工作流中，实现智能体调用各种灾害模型。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from ..core.models import (
    DisasterEvent, DisasterType, Location, AlertLevel,
    AgentMessage, SensorData, MultiModalInput, AgentRole
)
from ..core.llm import llm_client
from ..MCP.client import mcp_client

logger = logging.getLogger(__name__)


@dataclass
class MCPIntegratedState:
    """集成MCP的状态管理"""
    # 基础状态
    input_data: Optional[MultiModalInput] = None
    disaster_event: Optional[DisasterEvent] = None
    
    # MCP调用状态
    mcp_calls: List[Dict[str, Any]] = field(default_factory=list)
    mcp_results: Dict[str, Any] = field(default_factory=dict)
    
    # 工作流状态
    current_step: str = "initialized"
    workflow_status: str = "running"
    error_message: Optional[str] = None
    
    # 时间戳
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


class MCPIntegratedWorkflow:
    """集成MCP的智能体工作流"""
    
    def __init__(self):
        self.workflow_id = f"mcp_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(MCPIntegratedState)
        
        # 添加节点
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("assess_disaster", self._assess_disaster)
        workflow.add_node("call_climada", self._call_climada_models)
        workflow.add_node("call_lisflood", self._call_lisflood_models)
        workflow.add_node("call_cell2fire", self._call_cell2fire_models)
        workflow.add_node("call_pangu_weather", self._call_pangu_weather_models)
        workflow.add_node("call_nfdrs4", self._call_nfdrs4_models)
        workflow.add_node("integrate_results", self._integrate_mcp_results)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("error_handling", self._handle_errors)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 定义工作流边
        workflow.add_edge("initialize", "assess_disaster")
        workflow.add_edge("assess_disaster", "call_climada")
        workflow.add_edge("call_climada", "call_lisflood")
        workflow.add_edge("call_lisflood", "call_cell2fire")
        workflow.add_edge("call_cell2fire", "call_pangu_weather")
        workflow.add_edge("call_pangu_weather", "call_nfdrs4")
        workflow.add_edge("call_nfdrs4", "integrate_results")
        workflow.add_edge("integrate_results", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # 错误处理边
        workflow.add_edge("error_handling", END)
        
        return workflow.compile()
    
    async def _initialize_workflow(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """初始化工作流"""
        try:
            state.current_step = "initialized"
            state.last_update = datetime.now()
            
            # 检查MCP服务健康状态
            health_status = await mcp_client.health_check()
            state.mcp_results['health_check'] = health_status
            
            # 记录初始化
            state.mcp_calls.append({
                'step': 'initialize',
                'timestamp': datetime.now().isoformat(),
                'operation': 'health_check',
                'result': health_status
            })
            
            logger.info(f"Workflow {self.workflow_id} initialized")
            return state
            
        except Exception as e:
            state.error_message = f"Initialization failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _assess_disaster(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """评估灾害情况"""
        try:
            state.current_step = "assess_disaster"
            state.last_update = datetime.now()
            
            if not state.input_data:
                raise ValueError("No input data provided")
            
            # 分析输入数据，确定灾害类型
            disaster_type = self._analyze_disaster_type(state.input_data)
            state.disaster_event = DisasterEvent(
                event_id=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                disaster_type=disaster_type,
                location=state.input_data.location,
                severity_level=AlertLevel.HIGH,
                timestamp=datetime.now()
            )
            
            # 记录评估结果
            state.mcp_calls.append({
                'step': 'assess_disaster',
                'timestamp': datetime.now().isoformat(),
                'operation': 'disaster_assessment',
                'result': {
                    'disaster_type': disaster_type.value,
                    'location': state.input_data.location.__dict__,
                    'severity': AlertLevel.HIGH.value
                }
            })
            
            logger.info(f"Disaster assessed: {disaster_type.value}")
            return state
            
        except Exception as e:
            state.error_message = f"Disaster assessment failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    def _analyze_disaster_type(self, input_data: MultiModalInput) -> DisasterType:
        """分析输入数据，确定灾害类型"""
        # 基于输入数据内容分析灾害类型
        if "flood" in input_data.text.lower() or "water" in input_data.text.lower():
            return DisasterType.FLOOD
        elif "fire" in input_data.text.lower() or "wildfire" in input_data.text.lower():
            return DisasterType.WILDFIRE
        elif "earthquake" in input_data.text.lower() or "quake" in input_data.text.lower():
            return DisasterType.EARTHQUAKE
        elif "hurricane" in input_data.text.lower() or "storm" in input_data.text.lower():
            return DisasterType.HURRICANE
        else:
            # 默认返回洪水类型
            return DisasterType.FLOOD
    
    async def _call_climada_models(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """调用CLIMADA模型"""
        try:
            state.current_step = "call_climada"
            state.last_update = datetime.now()
            
            if not state.disaster_event:
                raise ValueError("No disaster event available")
            
            # 调用CLIMADA影响评估
            climada_result = await mcp_client.call_climada_impact_assessment(
                hazard_type=state.disaster_event.disaster_type.value,
                location={
                    'lat': state.disaster_event.location.latitude,
                    'lng': state.disaster_event.location.longitude
                },
                intensity=0.8  # 基于严重程度计算
            )
            
            # 记录调用结果
            state.mcp_results['climada'] = climada_result.data if climada_result.success else None
            state.mcp_calls.append({
                'step': 'call_climada',
                'timestamp': datetime.now().isoformat(),
                'operation': 'climada_impact_assessment',
                'success': climada_result.success,
                'result': climada_result.data if climada_result.success else climada_result.error
            })
            
            logger.info("CLIMADA model called successfully")
            return state
            
        except Exception as e:
            state.error_message = f"CLIMADA call failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _call_lisflood_models(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """调用LISFLOOD模型"""
        try:
            state.current_step = "call_lisflood"
            state.last_update = datetime.now()
            
            if not state.disaster_event:
                raise ValueError("No disaster event available")
            
            # 只对洪水灾害调用LISFLOOD
            if state.disaster_event.disaster_type == DisasterType.FLOOD:
                lisflood_result = await mcp_client.call_lisflood_simulation(
                    start_date=datetime.now().strftime('%Y-%m-%d'),
                    end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    settings_file="default_settings.xml",
                    output_dir="./lisflood_output"
                )
                
                state.mcp_results['lisflood'] = lisflood_result.data if lisflood_result.success else None
                state.mcp_calls.append({
                    'step': 'call_lisflood',
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'lisflood_simulation',
                    'success': lisflood_result.success,
                    'result': lisflood_result.data if lisflood_result.success else lisflood_result.error
                })
            else:
                # 非洪水灾害，跳过LISFLOOD
                state.mcp_results['lisflood'] = None
                state.mcp_calls.append({
                    'step': 'call_lisflood',
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'lisflood_simulation',
                    'success': True,
                    'result': 'Skipped - not a flood disaster'
                })
            
            logger.info("LISFLOOD model called successfully")
            return state
            
        except Exception as e:
            state.error_message = f"LISFLOOD call failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _call_cell2fire_models(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """调用Cell2Fire模型"""
        try:
            state.current_step = "call_cell2fire"
            state.last_update = datetime.now()
            
            if not state.disaster_event:
                raise ValueError("No disaster event available")
            
            # 只对火灾灾害调用Cell2Fire
            if state.disaster_event.disaster_type == DisasterType.WILDFIRE:
                cell2fire_result = await mcp_client.call_cell2fire_simulation(
                    ignition_points=[{
                        'x': state.disaster_event.location.longitude,
                        'y': state.disaster_event.location.latitude,
                        'ignition_time': 0
                    }],
                    weather_scenario={
                        'wind_speed': 15.0,
                        'wind_direction': 180.0,
                        'temperature': 25.0,
                        'humidity': 30.0
                    }
                )
                
                state.mcp_results['cell2fire'] = cell2fire_result.data if cell2fire_result.success else None
                state.mcp_calls.append({
                    'step': 'call_cell2fire',
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'cell2fire_simulation',
                    'success': cell2fire_result.success,
                    'result': cell2fire_result.data if cell2fire_result.success else cell2fire_result.error
                })
            else:
                # 非火灾灾害，跳过Cell2Fire
                state.mcp_results['cell2fire'] = None
                state.mcp_calls.append({
                    'step': 'call_cell2fire',
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'cell2fire_simulation',
                    'success': True,
                    'result': 'Skipped - not a wildfire disaster'
                })
            
            logger.info("Cell2Fire model called successfully")
            return state
            
        except Exception as e:
            state.error_message = f"Cell2Fire call failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _call_pangu_weather_models(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """调用Pangu-Weather模型"""
        try:
            state.current_step = "call_pangu_weather"
            state.last_update = datetime.now()
            
            if not state.disaster_event:
                raise ValueError("No disaster event available")
            
            # 调用Pangu-Weather预测
            pangu_result = await mcp_client.call_pangu_forecast(
                region={
                    'north': state.disaster_event.location.latitude + 1.0,
                    'south': state.disaster_event.location.latitude - 1.0,
                    'east': state.disaster_event.location.longitude + 1.0,
                    'west': state.disaster_event.location.longitude - 1.0
                },
                forecast_steps=40
            )
            
            state.mcp_results['pangu_weather'] = pangu_result.data if pangu_result.success else None
            state.mcp_calls.append({
                'step': 'call_pangu_weather',
                'timestamp': datetime.now().isoformat(),
                'operation': 'pangu_forecast',
                'success': pangu_result.success,
                'result': pangu_result.data if pangu_result.success else pangu_result.error
            })
            
            logger.info("Pangu-Weather model called successfully")
            return state
            
        except Exception as e:
            state.error_message = f"Pangu-Weather call failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _call_nfdrs4_models(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """调用NFDRS4模型"""
        try:
            state.current_step = "call_nfdrs4"
            state.last_update = datetime.now()
            
            if not state.disaster_event:
                raise ValueError("No disaster event available")
            
            # 调用NFDRS4火灾危险度计算
            nfdrs4_result = await mcp_client.call_nfdrs4_fire_danger(
                weather_data={
                    'temperature': 25.0,
                    'humidity': 30.0,
                    'wind_speed': 15.0,
                    'precipitation': 0.0
                },
                fuel_moisture={
                    'dead_fuel_moisture': 5.0,
                    'live_fuel_moisture': 80.0
                }
            )
            
            state.mcp_results['nfdrs4'] = nfdrs4_result.data if nfdrs4_result.success else None
            state.mcp_calls.append({
                'step': 'call_nfdrs4',
                'timestamp': datetime.now().isoformat(),
                'operation': 'nfdrs4_fire_danger',
                'success': nfdrs4_result.success,
                'result': nfdrs4_result.data if nfdrs4_result.success else nfdrs4_result.error
            })
            
            logger.info("NFDRS4 model called successfully")
            return state
            
        except Exception as e:
            state.error_message = f"NFDRS4 call failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _integrate_mcp_results(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """整合MCP调用结果"""
        try:
            state.current_step = "integrate_results"
            state.last_update = datetime.now()
            
            # 分析所有MCP调用结果
            successful_calls = [call for call in state.mcp_calls if call.get('success', False)]
            failed_calls = [call for call in state.mcp_calls if not call.get('success', False)]
            
            # 生成整合报告
            integration_report = {
                'total_calls': len(state.mcp_calls),
                'successful_calls': len(successful_calls),
                'failed_calls': len(failed_calls),
                'success_rate': len(successful_calls) / len(state.mcp_calls) if state.mcp_calls else 0,
                'model_results': state.mcp_results,
                'call_summary': state.mcp_calls
            }
            
            state.mcp_results['integration_report'] = integration_report
            
            # 记录整合结果
            state.mcp_calls.append({
                'step': 'integrate_results',
                'timestamp': datetime.now().isoformat(),
                'operation': 'result_integration',
                'success': True,
                'result': integration_report
            })
            
            logger.info("MCP results integrated successfully")
            return state
            
        except Exception as e:
            state.error_message = f"Result integration failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    async def _generate_response(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """生成最终响应"""
        try:
            state.current_step = "generate_response"
            state.last_update = datetime.now()
            
            # 基于MCP结果生成响应
            response = {
                'workflow_id': self.workflow_id,
                'disaster_event': state.disaster_event.__dict__ if state.disaster_event else None,
                'mcp_integration_summary': state.mcp_results.get('integration_report', {}),
                'recommendations': self._generate_recommendations(state),
                'workflow_status': 'completed',
                'completion_time': datetime.now().isoformat()
            }
            
            state.mcp_results['final_response'] = response
            
            # 记录响应生成
            state.mcp_calls.append({
                'step': 'generate_response',
                'timestamp': datetime.now().isoformat(),
                'operation': 'response_generation',
                'success': True,
                'result': response
            })
            
            state.workflow_status = "completed"
            logger.info("Response generated successfully")
            return state
            
        except Exception as e:
            state.error_message = f"Response generation failed: {str(e)}"
            state.workflow_status = "error"
            return state
    
    def _generate_recommendations(self, state: MCPIntegratedState) -> List[str]:
        """基于MCP结果生成建议"""
        recommendations = []
        
        # 基于灾害类型生成建议
        if state.disaster_event:
            if state.disaster_event.disaster_type == DisasterType.FLOOD:
                recommendations.append("立即启动洪水应急预案")
                recommendations.append("疏散低洼地区居民")
                recommendations.append("准备救援物资和装备")
            elif state.disaster_event.disaster_type == DisasterType.WILDFIRE:
                recommendations.append("启动森林火灾应急预案")
                recommendations.append("部署消防队伍和装备")
                recommendations.append("建立火灾隔离带")
            elif state.disaster_event.disaster_type == DisasterType.EARTHQUAKE:
                recommendations.append("启动地震应急预案")
                recommendations.append("检查建筑物结构安全")
                recommendations.append("准备医疗救援队伍")
        
        # 基于MCP结果生成建议
        if state.mcp_results.get('climada'):
            recommendations.append("基于CLIMADA评估结果调整应急响应级别")
        
        if state.mcp_results.get('lisflood'):
            recommendations.append("基于LISFLOOD模拟结果优化洪水应对策略")
        
        if state.mcp_results.get('cell2fire'):
            recommendations.append("基于Cell2Fire模拟结果制定火灾蔓延控制方案")
        
        return recommendations
    
    async def _handle_errors(self, state: MCPIntegratedState) -> MCPIntegratedState:
        """错误处理"""
        state.current_step = "error_handling"
        state.last_update = datetime.now()
        state.workflow_status = "error"
        
        # 记录错误
        state.mcp_calls.append({
            'step': 'error_handling',
            'timestamp': datetime.now().isoformat(),
            'operation': 'error_handling',
            'success': False,
            'result': state.error_message
        })
        
        logger.error(f"Workflow error: {state.error_message}")
        return state
    
    async def execute(
        self,
        input_data: MultiModalInput
    ) -> Dict[str, Any]:
        """执行工作流"""
        try:
            # 创建初始状态
            initial_state = MCPIntegratedState(input_data=input_data)
            
            # 执行工作流
            result = await self.graph.ainvoke(initial_state)
            
            return {
                'workflow_id': self.workflow_id,
                'status': result.workflow_status,
                'final_state': result,
                'mcp_results': result.mcp_results,
                'mcp_calls': result.mcp_calls
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                'workflow_id': self.workflow_id,
                'status': 'error',
                'error': str(e)
            }


# 便捷函数
async def run_mcp_integrated_workflow(input_data: MultiModalInput) -> Dict[str, Any]:
    """运行集成MCP的工作流"""
    workflow = MCPIntegratedWorkflow()
    return await workflow.execute(input_data)
