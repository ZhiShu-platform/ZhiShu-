#!/usr/bin/env python3
"""
工作流引擎

负责工作流的定义、执行、监控和管理
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    description: str
    step_type: str  # mcp_call, data_fetch, data_save, geoserver_publish
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    parameters_schema: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowInstance:
    """工作流实例"""
    id: str
    workflow_name: str
    parameters: Dict[str, Any]
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.workflow_instances: Dict[str, WorkflowInstance] = {}
        self.running_instances: Dict[str, asyncio.Task] = {}
        
        # 初始化预定义的工作流
        self._initialize_workflows()
    
    def _initialize_workflows(self):
        """初始化预定义的工作流"""
        
        # 1. NFDRS4火灾风险评估工作流
        nfdrs4_workflow = WorkflowDefinition(
            name="nfdrs4_fire_risk_assessment",
            description="NFDRS4火灾风险评估完整工作流",
            version="1.0.0",
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "火灾发生地点"},
                    "coordinates": {"type": "object", "description": "地理坐标"},
                    "fuel_type": {"type": "string", "description": "燃料类型"},
                    "weather_conditions": {"type": "string", "description": "天气条件"}
                },
                "required": ["location", "coordinates"]
            },
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="fetch_fire_event_data",
                    description="从数据库获取火灾事件数据",
                    step_type="data_fetch",
                    parameters={"data_type": "fire_event", "filters": {}},
                    dependencies=[]
                ),
                WorkflowStep(
                    id="step_2",
                    name="call_nfdrs4_risk_assessment",
                    description="调用NFDRS4火灾风险评估工具",
                    step_type="mcp_call",
                    parameters={
                        "service": "nfdrs4",
                        "tool": "nfdrs4_fire_risk_assessment",
                        "arguments": {}
                    },
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="save_assessment_result",
                    description="将风险评估结果保存到数据库",
                    step_type="data_save",
                    parameters={"table": "risk_assessments", "data": {}},
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="publish_to_geoserver",
                    description="通过GeoServer发布结果到前端",
                    step_type="geoserver_publish",
                    parameters={"layer_name": "nfdrs4_fire_risk", "data": {}},
                    dependencies=["step_3"]
                )
            ]
        )
        
        # 2. LISFLOOD洪水风险评估工作流
        lisflood_workflow = WorkflowDefinition(
            name="lisflood_flood_risk_assessment",
            description="LISFLOOD洪水风险评估完整工作流",
            version="1.0.0",
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "洪水发生地点"},
                    "coordinates": {"type": "object", "description": "地理坐标"},
                    "water_level": {"type": "number", "description": "水位高度"},
                    "rainfall_intensity": {"type": "string", "description": "降雨强度"}
                },
                "required": ["location", "coordinates"]
            },
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="fetch_flood_event_data",
                    description="从数据库获取洪水事件数据",
                    step_type="data_fetch",
                    parameters={"data_type": "flood_event", "filters": {}},
                    dependencies=[]
                ),
                WorkflowStep(
                    id="step_2",
                    name="call_lisflood_risk_assessment",
                    description="调用LISFLOOD洪水风险评估工具",
                    step_type="mcp_call",
                    parameters={
                        "service": "lisflood",
                        "tool": "lisflood_flood_risk_assessment",
                        "arguments": {}
                    },
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="save_assessment_result",
                    description="将风险评估结果保存到数据库",
                    step_type="data_save",
                    parameters={"table": "risk_assessments", "data": {}},
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="publish_to_geoserver",
                    description="通过GeoServer发布结果到前端",
                    step_type="geoserver_publish",
                    parameters={"layer_name": "lisflood_flood_risk", "data": {}},
                    dependencies=["step_3"]
                )
            ]
        )
        
        # 3. CLIMADA气候风险评估工作流
        climada_workflow = WorkflowDefinition(
            name="climada_climate_risk_assessment",
            description="CLIMADA气候风险评估完整工作流",
            version="1.0.0",
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "气候事件发生地点"},
                    "coordinates": {"type": "object", "description": "地理坐标"},
                    "climate_type": {"type": "string", "description": "气候类型"},
                    "wind_speed": {"type": "number", "description": "风速"}
                },
                "required": ["location", "coordinates"]
            },
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="fetch_climate_event_data",
                    description="从数据库获取气候事件数据",
                    step_type="data_fetch",
                    parameters={"data_type": "climate_event", "filters": {}},
                    dependencies=[]
                ),
                WorkflowStep(
                    id="step_2",
                    name="call_climada_risk_quantification",
                    description="调用CLIMADA气候风险评估工具",
                    step_type="mcp_call",
                    parameters={
                        "service": "climada",
                        "tool": "climada_risk_quantification",
                        "arguments": {}
                    },
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="save_assessment_result",
                    description="将风险评估结果保存到数据库",
                    step_type="data_save",
                    parameters={"table": "risk_assessments", "data": {}},
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="publish_to_geoserver",
                    description="通过GeoServer发布结果到前端",
                    step_type="geoserver_publish",
                    parameters={"layer_name": "climada_climate_risk", "data": {}},
                    dependencies=["step_3"]
                )
            ]
        )
        
        # 4. 综合灾害评估工作流
        comprehensive_workflow = WorkflowDefinition(
            name="comprehensive_disaster_assessment",
            description="综合灾害评估工作流（多模型协同）",
            version="1.0.0",
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "灾害发生地点"},
                    "coordinates": {"type": "object", "description": "地理坐标"},
                    "disaster_types": {"type": "array", "description": "灾害类型列表"}
                },
                "required": ["location", "coordinates", "disaster_types"]
            },
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="fetch_comprehensive_data",
                    description="从数据库获取综合灾害数据",
                    step_type="data_fetch",
                    parameters={"data_type": "comprehensive_disaster", "filters": {}},
                    dependencies=[]
                ),
                WorkflowStep(
                    id="step_2",
                    name="parallel_model_assessment",
                    description="并行调用多个模型进行评估",
                    step_type="parallel_mcp_calls",
                    parameters={
                        "services": ["nfdrs4", "lisflood", "climada"],
                        "tools": ["fire_risk", "flood_risk", "climate_risk"]
                    },
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="integrate_results",
                    description="整合多个模型的评估结果",
                    step_type="data_integration",
                    parameters={"integration_method": "weighted_average"},
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="save_integrated_result",
                    description="保存整合后的评估结果",
                    step_type="data_save",
                    parameters={"table": "integrated_assessments", "data": {}},
                    dependencies=["step_3"]
                ),
                WorkflowStep(
                    id="step_5",
                    name="publish_comprehensive_layer",
                    description="发布综合评估结果到GeoServer",
                    step_type="geoserver_publish",
                    parameters={"layer_name": "comprehensive_disaster_risk", "data": {}},
                    dependencies=["step_4"]
                )
            ]
        )
        
        # 注册工作流定义
        self.workflow_definitions[nfdrs4_workflow.name] = nfdrs4_workflow
        self.workflow_definitions[lisflood_workflow.name] = lisflood_workflow
        self.workflow_definitions[climada_workflow.name] = climada_workflow
        self.workflow_definitions[comprehensive_workflow.name] = comprehensive_workflow
        
        logger.info(f"初始化了 {len(self.workflow_definitions)} 个工作流定义")
    
    def get_workflow_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工作流定义"""
        definitions = []
        for name, definition in self.workflow_definitions.items():
            definitions.append({
                "name": definition.name,
                "description": definition.description,
                "version": definition.version,
                "step_count": len(definition.steps),
                "parameters_schema": definition.parameters_schema,
                "created_at": definition.created_at.isoformat(),
                "updated_at": definition.updated_at.isoformat()
            })
        return definitions
    
    def get_workflow_instances(self) -> List[Dict[str, Any]]:
        """获取所有工作流实例"""
        instances = []
        for instance_id, instance in self.workflow_instances.items():
            instances.append({
                "id": instance.id,
                "workflow_name": instance.workflow_name,
                "status": instance.status.value,
                "current_step": instance.current_step,
                "start_time": instance.start_time.isoformat() if instance.start_time else None,
                "end_time": instance.end_time.isoformat() if instance.end_time else None,
                "total_execution_time": instance.total_execution_time,
                "created_at": instance.created_at.isoformat()
            })
        return instances
    
    def start_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> str:
        """启动工作流"""
        if workflow_name not in self.workflow_definitions:
            raise ValueError(f"工作流 {workflow_name} 不存在")
        
        # 创建新的工作流实例
        definition = self.workflow_definitions[workflow_name]
        instance_id = str(uuid.uuid4())
        
        # 复制步骤定义
        steps = []
        for step_def in definition.steps:
            step = WorkflowStep(
                id=step_def.id,
                name=step_def.name,
                description=step_def.description,
                step_type=step_def.step_type,
                parameters=step_def.parameters.copy(),
                dependencies=step_def.dependencies.copy()
            )
            steps.append(step)
        
        instance = WorkflowInstance(
            id=instance_id,
            workflow_name=workflow_name,
            parameters=parameters,
            steps=steps
        )
        
        self.workflow_instances[instance_id] = instance
        logger.info(f"启动工作流 {workflow_name}，实例ID: {instance_id}")
        
        return instance_id
    
    async def execute_workflow_background(self, instance_id: str):
        """在后台执行工作流"""
        try:
            await self.execute_workflow(instance_id)
        except Exception as e:
            logger.error(f"工作流 {instance_id} 执行失败: {e}")
            instance = self.workflow_instances.get(instance_id)
            if instance:
                instance.status = WorkflowStatus.FAILED
                instance.end_time = datetime.now()
    
    async def execute_workflow(self, instance_id: str):
        """执行工作流"""
        instance = self.workflow_instances.get(instance_id)
        if not instance:
            raise ValueError(f"工作流实例 {instance_id} 不存在")
        
        instance.status = WorkflowStatus.RUNNING
        instance.start_time = datetime.now()
        
        logger.info(f"开始执行工作流 {instance.workflow_name}，实例ID: {instance_id}")
        
        try:
            # 按依赖顺序执行步骤
            completed_steps = set()
            
            while len(completed_steps) < len(instance.steps):
                # 找到可以执行的步骤
                for step in instance.steps:
                    if step.id in completed_steps:
                        continue
                    
                    # 检查依赖是否满足
                    if all(dep in completed_steps for dep in step.dependencies):
                        # 执行步骤
                        await self._execute_step(step, instance)
                        completed_steps.add(step.id)
                        
                        # 更新当前步骤
                        instance.current_step = step.id
                        
                        # 检查步骤是否成功
                        if step.status == StepStatus.FAILED:
                            instance.status = WorkflowStatus.FAILED
                            instance.end_time = datetime.now()
                            logger.error(f"工作流 {instance_id} 在步骤 {step.id} 失败")
                            return
                
                # 避免死循环
                if len(completed_steps) == 0:
                    logger.error(f"工作流 {instance_id} 无法找到可执行的步骤")
                    instance.status = WorkflowStatus.FAILED
                    instance.end_time = datetime.now()
                    return
                
                await asyncio.sleep(0.1)  # 避免过度占用CPU
            
            # 工作流执行完成
            instance.status = WorkflowStatus.COMPLETED
            instance.end_time = datetime.now()
            if instance.start_time:
                instance.total_execution_time = (instance.end_time - instance.start_time).total_seconds()
            
            logger.info(f"工作流 {instance_id} 执行完成")
            
        except Exception as e:
            logger.error(f"工作流 {instance_id} 执行异常: {e}")
            instance.status = WorkflowStatus.FAILED
            instance.end_time = datetime.now()
            raise
    
    async def _execute_step(self, step: WorkflowStep, instance: WorkflowInstance):
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        
        logger.info(f"执行步骤 {step.name} ({step.id})")
        
        try:
            if step.step_type == "data_fetch":
                result = await self._execute_data_fetch_step(step, instance)
            elif step.step_type == "mcp_call":
                result = await self._execute_mcp_call_step(step, instance)
            elif step.step_type == "data_save":
                result = await self._execute_data_save_step(step, instance)
            elif step.step_type == "geoserver_publish":
                result = await self._execute_geoserver_publish_step(step, instance)
            elif step.step_type == "parallel_mcp_calls":
                result = await self._execute_parallel_mcp_calls_step(step, instance)
            elif step.step_type == "data_integration":
                result = await self._execute_data_integration_step(step, instance)
            else:
                raise ValueError(f"不支持的步骤类型: {step.step_type}")
            
            step.result = result
            step.status = StepStatus.COMPLETED
            
        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED
            logger.error(f"步骤 {step.id} 执行失败: {e}")
            raise
        
        finally:
            step.end_time = datetime.now()
            if step.start_time:
                step.execution_time = (step.end_time - step.start_time).total_seconds()
    
    async def _execute_data_fetch_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """执行数据获取步骤"""
        # 模拟数据获取
        await asyncio.sleep(1)
        
        data_type = step.parameters.get("data_type", "unknown")
        filters = step.parameters.get("filters", {})
        
        # 根据数据类型返回模拟数据
        if "fire" in data_type:
            data = {
                "event_type": "fire",
                "location": instance.parameters.get("location", "未知地点"),
                "coordinates": instance.parameters.get("coordinates", {"lat": 0, "lng": 0}),
                "severity": "high",
                "timestamp": datetime.now().isoformat()
            }
        elif "flood" in data_type:
            data = {
                "event_type": "flood",
                "location": instance.parameters.get("location", "未知地点"),
                "coordinates": instance.parameters.get("coordinates", {"lat": 0, "lng": 0}),
                "water_level": 15.2,
                "timestamp": datetime.now().isoformat()
            }
        elif "climate" in data_type:
            data = {
                "event_type": "climate",
                "location": instance.parameters.get("location", "未知地点"),
                "coordinates": instance.parameters.get("coordinates", {"lat": 0, "lng": 0}),
                "climate_type": "tropical_cyclone",
                "timestamp": datetime.now().isoformat()
            }
        else:
            data = {"message": f"获取{data_type}类型数据", "timestamp": datetime.now().isoformat()}
        
        return {
            "success": True,
            "data": data,
            "count": 1,
            "source": "database"
        }
    
    async def _execute_mcp_call_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """执行MCP调用步骤"""
        service = step.parameters.get("service")
        tool = step.parameters.get("tool")
        arguments = step.parameters.get("arguments", {})
        
        # 模拟MCP调用
        await asyncio.sleep(2)
        
        # 根据服务类型返回模拟结果
        if service == "nfdrs4":
            result = {
                "risk_level": "high",
                "risk_score": 0.85,
                "confidence": 0.92,
                "recommendations": ["立即启动应急预案", "加强监测和预警"]
            }
        elif service == "lisflood":
            result = {
                "flood_level": "severe",
                "affected_area": "1500 km²",
                "population_at_risk": 25000,
                "evacuation_required": True
            }
        elif service == "climada":
            result = {
                "climate_risk": "moderate",
                "vulnerability_score": 0.65,
                "adaptation_needed": True,
                "economic_impact": "significant"
            }
        else:
            result = {"message": f"模拟{service}服务{tool}工具执行结果"}
        
        return {
            "success": True,
            "service": service,
            "tool": tool,
            "arguments": arguments,
            "result": result,
            "execution_time": 2.0
        }
    
    async def _execute_data_save_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """执行数据保存步骤"""
        table = step.parameters.get("table", "unknown_table")
        data = step.parameters.get("data", {})
        
        # 模拟数据保存
        await asyncio.sleep(1)
        
        record_id = f"record_{int(time.time())}"
        
        return {
            "success": True,
            "table": table,
            "record_id": record_id,
            "saved_at": datetime.now().isoformat(),
            "message": f"数据已保存到表 {table}"
        }
    
    async def _execute_geoserver_publish_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """执行GeoServer发布步骤"""
        layer_name = step.parameters.get("layer_name", "unknown_layer")
        data = step.parameters.get("data", {})
        
        # 模拟GeoServer发布
        await asyncio.sleep(1)
        
        layer_id = f"layer_{layer_name}_{int(time.time())}"
        service_url = f"http://localhost:8080/geoserver/rest/services/{layer_name}/wms"
        
        return {
            "success": True,
            "layer_name": layer_name,
            "layer_id": layer_id,
            "service_url": service_url,
            "published_at": datetime.now().isoformat(),
            "message": f"图层 {layer_name} 已发布到GeoServer"
        }
    
    async def _execute_parallel_mcp_calls_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """执行并行MCP调用步骤"""
        services = step.parameters.get("services", [])
        tools = step.parameters.get("tools", [])
        
        # 并行执行多个MCP调用
        tasks = []
        for i, service in enumerate(services):
            tool = tools[i] if i < len(tools) else "default_tool"
            task = self._execute_single_mcp_call(service, tool, {})
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "success": True,
            "parallel_calls": len(services),
            "results": results,
            "execution_time": 3.0
        }
    
    async def _execute_single_mcp_call(self, service: str, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个MCP调用"""
        await asyncio.sleep(1)
        return {
            "service": service,
            "tool": tool,
            "result": f"模拟{service}服务{tool}工具执行结果"
        }
    
    async def _execute_data_integration_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """执行数据整合步骤"""
        integration_method = step.parameters.get("integration_method", "simple_merge")
        
        # 模拟数据整合
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "integration_method": integration_method,
            "integrated_data": {
                "comprehensive_risk": "high",
                "confidence": 0.88,
                "recommendations": ["启动综合应急预案", "多部门协同响应"]
            },
            "message": f"使用{integration_method}方法整合数据成功"
        }
    
    def get_workflow_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """获取工作流实例"""
        return self.workflow_instances.get(instance_id)
    
    def cancel_workflow(self, instance_id: str) -> bool:
        """取消工作流"""
        instance = self.workflow_instances.get(instance_id)
        if not instance:
            return False
        
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            return False
        
        instance.status = WorkflowStatus.CANCELLED
        instance.end_time = datetime.now()
        
        # 取消正在运行的任务
        if instance_id in self.running_instances:
            task = self.running_instances[instance_id]
            task.cancel()
            del self.running_instances[instance_id]
        
        logger.info(f"工作流 {instance_id} 已取消")
        return True
