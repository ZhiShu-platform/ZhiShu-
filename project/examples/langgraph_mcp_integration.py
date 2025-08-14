"""
LangGraph与MCP集成示例

展示如何在LangGraph工作流中使用MCP工具进行灾害建模
"""

import asyncio
from typing import Dict, Any, List
from langgraph import StateGraph, END
from langgraph.graph import Graph
from langgraph.prebuilt import ToolExecutor, ToolInvocation

# 导入MCP组件
from src.MCP.tools.climada_tools import get_climada_tools
from src.MCP.tools.lisflood_tools import get_lisflood_tools
from src.MCP.sdk import MCPClient, ToolExecutor as MCPToolExecutor


class DisasterAnalysisState:
    """灾害分析状态"""
    disaster_type: str
    location: Dict[str, Any]
    severity: float
    climate_data: Dict[str, Any]
    flood_data: Dict[str, Any] 
    analysis_results: Dict[str, Any]
    recommendations: List[str]
    messages: List[Dict[str, Any]]


# 方法1: 直接使用MCP工具作为LangGraph工具
async def create_mcp_langgraph_tools():
    """创建MCP工具的LangGraph包装器"""
    
    # 获取所有MCP工具
    climada_tools = get_climada_tools()
    lisflood_tools = get_lisflood_tools()
    
    # 创建工具列表
    all_tools = []
    
    # 添加Climada工具
    for tool_name, tool_info in climada_tools.items():
        tool_class = tool_info["class"]
        all_tools.append(tool_class())
    
    # 添加Lisflood工具  
    for tool_name, tool_info in lisflood_tools.items():
        tool_class = tool_info["class"]
        all_tools.append(tool_class())
    
    return all_tools


# 方法2: 通过MCP客户端调用工具
class MCPToolNode:
    """MCP工具节点，用于LangGraph工作流"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = None
        self.executor = None
    
    async def __aenter__(self):
        self.client = MCPClient(self.server_url)
        await self.client.__aenter__()
        self.executor = MCPToolExecutor(self.client)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)


# LangGraph节点函数
async def assess_climate_risk(state: DisasterAnalysisState) -> DisasterAnalysisState:
    """评估气候风险节点"""
    
    async with MCPToolNode() as mcp:
        # 使用Climada进行影响评估
        impact_result = await mcp.executor.run_climada_impact_assessment(
            hazard_type=state.disaster_type.lower(),
            region=state.location.get("region", "Unknown"),
            year_range=[2020, 2024]
        )
        
        # 生成暴露分析
        exposure_result = await mcp.executor.run_climada_exposure_analysis(
            country_iso=state.location.get("country_iso", "CHE"),
            exposure_type="litpop"
        )
        
        # 更新状态
        state.climate_data = {
            "impact_assessment": impact_result,
            "exposure_analysis": exposure_result
        }
        
        state.messages.append({
            "type": "climate_analysis",
            "content": f"完成{state.disaster_type}气候风险评估",
            "data": state.climate_data
        })
    
    return state


async def assess_flood_risk(state: DisasterAnalysisState) -> DisasterAnalysisState:
    """评估洪水风险节点"""
    
    # 只有洪水相关灾害才进行洪水建模
    if state.disaster_type.lower() not in ["flood", "hurricane", "storm"]:
        return state
    
    async with MCPToolNode() as mcp:
        # 运行洪水模拟
        flood_result = await mcp.executor.run_lisflood_simulation(
            start_date="2024-01-01",
            end_date="2024-12-31", 
            settings_file="config/flood_settings.xml",
            output_dir="./flood_output"
        )
        
        # 运行洪水预报
        forecast_result = await mcp.executor.run_lisflood_forecast(
            forecast_start="2024-03-15", 
            forecast_horizon=7,
            settings_file="config/flood_settings.xml",
            meteorological_forecast="data/weather_forecast.nc"
        )
        
        # 更新状态
        state.flood_data = {
            "simulation": flood_result,
            "forecast": forecast_result
        }
        
        state.messages.append({
            "type": "flood_analysis", 
            "content": f"完成洪水建模和预报",
            "data": state.flood_data
        })
    
    return state


async def synthesize_results(state: DisasterAnalysisState) -> DisasterAnalysisState:
    """综合分析结果节点"""
    
    # 综合气候和洪水数据
    analysis_results = {
        "disaster_type": state.disaster_type,
        "location": state.location,
        "severity_assessment": state.severity
    }
    
    # 添加气候风险结果
    if state.climate_data:
        analysis_results["climate_impact"] = state.climate_data
    
    # 添加洪水风险结果  
    if state.flood_data:
        analysis_results["flood_impact"] = state.flood_data
    
    # 生成建议
    recommendations = []
    
    if state.severity > 0.7:
        recommendations.append("立即启动应急响应")
        recommendations.append("考虑疏散高风险区域")
    elif state.severity > 0.4:
        recommendations.append("加强监测和预警")
        recommendations.append("准备应急资源")
    else:
        recommendations.append("持续监测情况")
    
    # 基于具体分析结果添加建议
    if state.climate_data and "impact_assessment" in state.climate_data:
        impact = state.climate_data["impact_assessment"]
        if impact.get("data", {}).get("economic_damage", 0) > 1000000:
            recommendations.append("准备经济损失应对措施")
    
    if state.flood_data and "forecast" in state.flood_data:
        forecast = state.flood_data["forecast"] 
        if forecast.get("data", {}).get("max_discharge", 0) > 500:
            recommendations.append("准备洪水防护措施")
    
    # 更新状态
    state.analysis_results = analysis_results
    state.recommendations = recommendations
    
    state.messages.append({
        "type": "final_analysis",
        "content": "完成综合风险分析",
        "recommendations": recommendations
    })
    
    return state


# 条件路由函数
def should_analyze_flood(state: DisasterAnalysisState) -> str:
    """决定是否需要洪水分析"""
    flood_related = ["flood", "hurricane", "storm", "heavy_rain"]
    if state.disaster_type.lower() in flood_related:
        return "flood_analysis"
    else:
        return "synthesis"


# 创建LangGraph工作流
def create_disaster_analysis_workflow() -> Graph:
    """创建灾害分析工作流"""
    
    # 创建状态图
    workflow = StateGraph(DisasterAnalysisState)
    
    # 添加节点
    workflow.add_node("climate_assessment", assess_climate_risk)
    workflow.add_node("flood_analysis", assess_flood_risk) 
    workflow.add_node("synthesis", synthesize_results)
    
    # 添加边
    workflow.add_edge("climate_assessment", "flood_analysis")
    workflow.add_conditional_edges(
        "climate_assessment",
        should_analyze_flood,
        {
            "flood_analysis": "flood_analysis",
            "synthesis": "synthesis"
        }
    )
    workflow.add_edge("flood_analysis", "synthesis")
    workflow.add_edge("synthesis", END)
    
    # 设置入口点
    workflow.set_entry_point("climate_assessment")
    
    return workflow.compile()


# 方法3: 使用MCP工具的自定义LangGraph工具
class ClimadaImpactTool:
    """自定义Climada影响评估工具"""
    
    name = "climada_impact_assessment"
    description = "使用Climada模型评估气候灾害影响"
    
    def __init__(self):
        self.mcp_client = None
    
    async def __call__(self, hazard_type: str, region: str, **kwargs) -> Dict[str, Any]:
        """执行影响评估"""
        if not self.mcp_client:
            self.mcp_client = MCPClient()
            await self.mcp_client.__aenter__()
        
        executor = MCPToolExecutor(self.mcp_client)
        result = await executor.run_climada_impact_assessment(
            hazard_type=hazard_type,
            region=region,
            **kwargs
        )
        
        return result


class LisfloodSimulationTool:
    """自定义Lisflood仿真工具"""
    
    name = "lisflood_simulation"
    description = "使用Lisflood模型进行洪水仿真"
    
    def __init__(self):
        self.mcp_client = None
    
    async def __call__(self, start_date: str, end_date: str, settings_file: str, **kwargs) -> Dict[str, Any]:
        """执行洪水仿真"""
        if not self.mcp_client:
            self.mcp_client = MCPClient()
            await self.mcp_client.__aenter__()
        
        executor = MCPToolExecutor(self.mcp_client)
        result = await executor.run_lisflood_simulation(
            start_date=start_date,
            end_date=end_date, 
            settings_file=settings_file,
            **kwargs
        )
        
        return result


# 使用示例
async def example_disaster_analysis():
    """灾害分析示例"""
    
    # 创建工作流
    workflow = create_disaster_analysis_workflow()
    
    # 初始状态
    initial_state = DisasterAnalysisState()
    initial_state.disaster_type = "Hurricane"
    initial_state.location = {
        "region": "Florida",
        "country_iso": "USA",
        "coordinates": {"lat": 27.7663, "lon": -82.6404}
    }
    initial_state.severity = 0.8
    initial_state.climate_data = {}
    initial_state.flood_data = {}
    initial_state.analysis_results = {}
    initial_state.recommendations = []
    initial_state.messages = []
    
    # 运行工作流
    result = await workflow.ainvoke(initial_state)
    
    return result


# 方法4: 批量工具执行
async def batch_disaster_modeling(disasters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """批量灾害建模"""
    
    async with MCPClient() as client:
        executor = MCPToolExecutor(client)
        
        results = {}
        
        for disaster in disasters:
            disaster_id = disaster.get("id")
            disaster_type = disaster.get("type")
            location = disaster.get("location")
            
            # 并行执行多个分析
            tasks = []
            
            # Climada影响评估
            if disaster_type in ["hurricane", "wildfire", "earthquake"]:
                tasks.append(
                    executor.run_climada_impact_assessment(
                        hazard_type=disaster_type,
                        region=location.get("region"),
                        year_range=[2020, 2024]
                    )
                )
            
            # Lisflood洪水分析
            if disaster_type in ["flood", "hurricane", "storm"]:
                tasks.append(
                    executor.run_lisflood_simulation(
                        start_date="2024-01-01",
                        end_date="2024-12-31",
                        settings_file=f"config/{location.get('region', 'default')}_settings.xml",
                        output_dir=f"./output/{disaster_id}"
                    )
                )
            
            # 等待所有任务完成
            if tasks:
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                results[disaster_id] = {
                    "disaster": disaster,
                    "analysis_results": task_results
                }
        
        return results


if __name__ == "__main__":
    # 运行示例
    async def main():
        print("开始灾害分析工作流...")
        result = await example_disaster_analysis()
        
        print("分析完成!")
        print(f"灾害类型: {result.disaster_type}")
        print(f"建议措施: {result.recommendations}")
        
        # 批量分析示例
        disasters = [
            {
                "id": "hurricane_001",
                "type": "hurricane", 
                "location": {"region": "Florida", "country_iso": "USA"}
            },
            {
                "id": "flood_001",
                "type": "flood",
                "location": {"region": "Netherlands", "country_iso": "NLD"}
            }
        ]
        
        batch_results = await batch_disaster_modeling(disasters)
        print(f"批量分析完成，处理了 {len(batch_results)} 个灾害事件")
    
    asyncio.run(main())