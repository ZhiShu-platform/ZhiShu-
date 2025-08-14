# LangGraph与MCP集成使用指南

本文档详细说明如何在LangGraph工作流中使用MCP (Model Control Plane) 系统进行科学建模。

## 目录

1. [基本概念](#基本概念)
2. [集成方式](#集成方式)
3. [实际使用案例](#实际使用案例)
4. [最佳实践](#最佳实践)
5. [故障排除](#故障排除)

## 基本概念

### MCP架构
MCP系统提供统一接口访问多个科学模型：
- **Climada**: 气候风险评估和损害分析
- **Lisflood**: 水文建模和洪水预测
- **未来扩展**: Cell2Fire, NFDRS4, Pangu等

### LangGraph集成点
MCP可以在LangGraph工作流的以下节点中使用：
- **威胁检测**: 使用气象模型预测危险
- **损害评估**: 使用Climada评估经济影响
- **洪水分析**: 使用Lisflood进行水文建模
- **决策支持**: 综合多模型结果

## 集成方式

### 方式1: 直接工具集成

```python
from src.MCP.tools.climada_tools import get_climada_tools
from src.MCP.tools.lisflood_tools import get_lisflood_tools
from langgraph.prebuilt import ToolExecutor

# 获取所有MCP工具
async def setup_mcp_tools():
    climada_tools = get_climada_tools()
    lisflood_tools = get_lisflood_tools()
    
    tools = []
    for tool_name, tool_info in climada_tools.items():
        tools.append(tool_info["class"]())
    
    for tool_name, tool_info in lisflood_tools.items():
        tools.append(tool_info["class"]())
    
    return ToolExecutor(tools)

# 在LangGraph节点中使用
async def climate_analysis_node(state):
    tool_executor = await setup_mcp_tools()
    
    # 执行Climada影响评估
    result = await tool_executor.ainvoke({
        "tool": "climada_impact_assessment",
        "tool_input": {
            "hazard_type": "hurricane",
            "region": "Florida",
            "year_range": [2020, 2024]
        }
    })
    
    state["climate_analysis"] = result
    return state
```

### 方式2: MCP客户端调用

```python
from src.MCP.sdk import MCPClient, ToolExecutor

async def disaster_assessment_node(state):
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        
        # 并行执行多个分析
        tasks = []
        
        # Climada影响评估
        tasks.append(
            executor.run_climada_impact_assessment(
                hazard_type=state["disaster_type"],
                region=state["location"]["region"]
            )
        )
        
        # Lisflood洪水分析（如果适用）
        if state["disaster_type"] in ["flood", "hurricane"]:
            tasks.append(
                executor.run_lisflood_simulation(
                    start_date="2024-01-01",
                    end_date="2024-12-31",
                    settings_file="config/settings.xml",
                    output_dir="./output"
                )
            )
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        state["model_results"] = {
            "climada": results[0],
            "lisflood": results[1] if len(results) > 1 else None
        }
    
    return state
```

### 方式3: 高级接口使用

```python
from src.model.climada import ClimadaModel
from src.model.lisflood import LisfloodModel

async def comprehensive_analysis_node(state):
    # 使用高级接口进行分析
    async with ClimadaModel() as climada:
        # 热带气旋影响评估
        hurricane_impact = await climada.assess_tropical_cyclone_impact(
            region=state["location"]["region"],
            year_range=[2020, 2024]
        )
        
        # 暴露分析
        exposure = await climada.generate_litpop_exposure(
            country_iso=state["location"]["country_iso"]
        )
    
    # 洪水建模（如果需要）
    flood_results = None
    if state["disaster_type"] in ["flood", "hurricane"]:
        async with LisfloodModel() as lisflood:
            flood_results = await lisflood.run_flood_simulation(
                start_date="2024-01-01",
                end_date="2024-12-31",
                settings_file="config/settings.xml",
                output_dir="./output"
            )
    
    state["comprehensive_analysis"] = {
        "climate": {
            "impact": hurricane_impact,
            "exposure": exposure
        },
        "flood": flood_results
    }
    
    return state
```

## 实际使用案例

### 案例1: 飓风威胁评估工作流

```python
from langgraph.graph import StateGraph, END

def create_hurricane_assessment_workflow():
    workflow = StateGraph(dict)
    
    # 添加节点
    workflow.add_node("data_collection", collect_hurricane_data)
    workflow.add_node("wind_analysis", analyze_wind_patterns) 
    workflow.add_node("storm_surge", assess_storm_surge)
    workflow.add_node("damage_prediction", predict_damage_mcp)
    workflow.add_node("evacuation_planning", plan_evacuation)
    
    # 设置流程
    workflow.set_entry_point("data_collection")
    workflow.add_edge("data_collection", "wind_analysis")
    workflow.add_edge("wind_analysis", "storm_surge")
    workflow.add_edge("storm_surge", "damage_prediction")
    workflow.add_edge("damage_prediction", "evacuation_planning")
    workflow.add_edge("evacuation_planning", END)
    
    return workflow.compile()

async def predict_damage_mcp(state):
    """使用MCP进行损害预测"""
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        
        # 使用Climada进行飓风影响评估
        damage_assessment = await executor.run_climada_impact_assessment(
            hazard_type="tropical_cyclone",
            region=state["hurricane_data"]["landfall_region"],
            year_range=[2020, 2024],
            return_period=[10, 25, 50, 100, 250]
        )
        
        # 使用Lisflood进行风暴潮洪水分析
        flood_analysis = await executor.run_lisflood_simulation(
            start_date=state["hurricane_data"]["start_date"],
            end_date=state["hurricane_data"]["end_date"],
            settings_file="config/storm_surge_settings.xml",
            output_dir=f"./output/{state['hurricane_data']['storm_id']}"
        )
        
        # 综合分析结果
        state["damage_prediction"] = {
            "economic_impact": damage_assessment,
            "flood_impact": flood_analysis,
            "combined_risk_score": calculate_combined_risk(
                damage_assessment, flood_analysis
            )
        }
    
    return state
```

### 案例2: 实时洪水预警系统

```python
def create_flood_warning_system():
    workflow = StateGraph(dict)
    
    # 实时数据处理节点
    workflow.add_node("sensor_data", process_sensor_data)
    workflow.add_node("weather_forecast", fetch_weather_data)
    workflow.add_node("flood_modeling", run_flood_model_mcp)
    workflow.add_node("risk_assessment", assess_flood_risk)
    workflow.add_node("alert_generation", generate_alerts)
    
    # 并行处理传感器和天气数据
    workflow.set_entry_point("sensor_data")
    workflow.add_edge("sensor_data", "weather_forecast")
    workflow.add_edge("weather_forecast", "flood_modeling")
    workflow.add_edge("flood_modeling", "risk_assessment")
    workflow.add_edge("risk_assessment", "alert_generation")
    workflow.add_edge("alert_generation", END)
    
    return workflow.compile()

async def run_flood_model_mcp(state):
    """使用MCP运行洪水模型"""
    async with LisfloodModel() as lisflood:
        # 实时洪水预报
        forecast = await lisflood.run_real_time_forecast(
            current_date=state["current_time"],
            forecast_days=7,
            settings_file="config/realtime_settings.xml",
            real_time_data=state["weather_data"]["forecast_file"]
        )
        
        # 河流路由分析
        routing = await lisflood.analyze_river_routing(
            start_date=state["current_time"],
            end_date=add_days(state["current_time"], 7),
            settings_file="config/realtime_settings.xml",
            discharge_points=state["monitoring_stations"]
        )
        
        state["flood_forecast"] = {
            "ensemble_forecast": forecast,
            "river_routing": routing,
            "confidence": calculate_forecast_confidence(forecast)
        }
    
    return state
```

### 案例3: 气候变化影响评估

```python
async def climate_impact_assessment_node(state):
    """气候变化影响评估节点"""
    
    async with ClimadaModel() as climada:
        # 当前气候条件下的风险评估
        current_risk = await climada.assess_tropical_cyclone_impact(
            region=state["study_region"],
            year_range=[1980, 2020]  # 历史基线
        )
        
        # 未来气候情景下的风险评估
        future_scenarios = []
        for scenario in ["RCP4.5", "RCP8.5"]:
            scenario_risk = await climada.assess_tropical_cyclone_impact(
                region=state["study_region"],
                year_range=[2050, 2080],  # 未来时期
                climate_scenario=scenario.lower()
            )
            future_scenarios.append({
                "scenario": scenario,
                "risk_assessment": scenario_risk
            })
        
        # 计算气候变化影响
        climate_impact = calculate_climate_change_impact(
            baseline=current_risk,
            future_scenarios=future_scenarios
        )
        
        state["climate_impact_assessment"] = {
            "baseline_risk": current_risk,
            "future_scenarios": future_scenarios,
            "climate_change_impact": climate_impact
        }
    
    return state
```

## 最佳实践

### 1. 异步并行执行

```python
# ✅ 好的做法：并行执行多个模型
async def parallel_modeling(state):
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        
        # 同时运行多个分析
        tasks = [
            executor.run_climada_impact_assessment(**params1),
            executor.run_lisflood_simulation(**params2),
            executor.run_climada_exposure_analysis(**params3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return process_results(results)

# ❌ 避免：顺序执行（效率低）
async def sequential_modeling(state):
    result1 = await run_climada_analysis()
    result2 = await run_lisflood_analysis()  # 等待第一个完成
    result3 = await run_exposure_analysis()  # 等待第二个完成
```

### 2. 错误处理和重试

```python
import asyncio
from functools import wraps

def retry_on_failure(max_retries=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:  # 最后一次尝试
                        raise e
                    await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
async def robust_climate_analysis(state):
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        return await executor.run_climada_impact_assessment(
            hazard_type=state["disaster_type"],
            region=state["region"]
        )
```

### 3. 资源管理

```python
# ✅ 使用上下文管理器
async def proper_resource_management(state):
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        # 客户端会自动关闭
        return await executor.run_analysis()

# ✅ 批量处理减少连接开销
async def batch_processing(disaster_events):
    async with MCPClient() as client:
        executor = ToolExecutor(client)
        
        results = []
        for event in disaster_events:
            result = await executor.run_analysis(event)
            results.append(result)
        
        return results  # 单个连接处理所有事件
```

### 4. 配置管理

```python
# config/mcp_settings.py
MCP_CONFIG = {
    "server_url": "http://localhost:8000",
    "timeout": 300,  # 5分钟超时
    "retry_attempts": 3,
    "model_settings": {
        "climada": {
            "default_year_range": [2000, 2024],
            "default_return_periods": [10, 25, 50, 100, 250]
        },
        "lisflood": {
            "default_time_step": "daily",
            "default_output_format": "netcdf"
        }
    }
}

# 在节点中使用配置
async def configured_analysis_node(state):
    config = MCP_CONFIG["model_settings"]["climada"]
    
    async with MCPClient(MCP_CONFIG["server_url"]) as client:
        executor = ToolExecutor(client)
        
        result = await executor.run_climada_impact_assessment(
            hazard_type=state["disaster_type"],
            region=state["region"],
            year_range=config["default_year_range"],
            return_period=config["default_return_periods"]
        )
        
        return {"analysis_result": result}
```

## 故障排除

### 常见问题

#### 1. MCP服务器连接失败

```python
# 检查MCP服务器状态
async def check_mcp_health():
    try:
        async with MCPClient() as client:
            health = await client.health_check()
            print(f"MCP服务器状态: {health}")
            return health["status"] == "healthy"
    except Exception as e:
        print(f"MCP服务器连接失败: {e}")
        return False

# 在工作流开始前检查
async def robust_workflow_start(state):
    if not await check_mcp_health():
        state["error"] = "MCP服务器不可用"
        return state
    
    # 继续正常流程
    return await normal_processing(state)
```

#### 2. 模型执行超时

```python
# 设置合适的超时时间
async def timeout_protected_analysis(state):
    try:
        async with asyncio.timeout(600):  # 10分钟超时
            async with MCPClient() as client:
                executor = ToolExecutor(client)
                return await executor.run_long_analysis(state)
    except asyncio.TimeoutError:
        return {"error": "分析超时", "status": "timeout"}
```

#### 3. 内存使用优化

```python
# 处理大量数据时的内存优化
async def memory_efficient_batch_processing(events):
    results = []
    batch_size = 10  # 批量处理大小
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        
        async with MCPClient() as client:
            executor = ToolExecutor(client)
            
            batch_results = []
            for event in batch:
                result = await executor.run_analysis(event)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        # 可选：在批次之间添加延迟
        await asyncio.sleep(1.0)
    
    return results
```

### 监控和日志

```python
import logging
from datetime import datetime

# 设置详细日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logged_mcp_analysis(state):
    start_time = datetime.now()
    
    try:
        logger.info(f"开始MCP分析: {state['disaster_type']} at {state['location']}")
        
        async with MCPClient() as client:
            executor = ToolExecutor(client)
            result = await executor.run_analysis(state)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"MCP分析完成，耗时: {duration:.2f}秒")
        
        return {"result": result, "duration": duration}
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"MCP分析失败，耗时: {duration:.2f}秒，错误: {e}")
        raise
```

## 总结

MCP系统为LangGraph工作流提供了强大的科学建模能力。通过合适的集成方式和最佳实践，可以构建高效、可靠的灾害管理系统。

关键要点：
- 使用异步并行执行提高效率
- 实施适当的错误处理和重试机制
- 合理管理资源和连接
- 添加监控和日志记录
- 根据具体需求选择合适的集成方式

更多详细信息，请参考MCP API文档和LangGraph官方文档。