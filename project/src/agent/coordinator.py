"""Multi-agent coordinator for disaster response management."""
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
# ?? ToolExecutor ?I? ToolNode????? ToolExecutor ???????
from langgraph.prebuilt import ToolNode # ???????

from ..core.models import (
    DisasterEvent, DisasterType, Location, AlertLevel,
    AgentMessage, SensorData, MultiModalInput, AgentRole
)
from ..core.llm import llm_client
from ..MCP.client import mcp_client
from .disaster_experts import create_disaster_expert

@dataclass
class CoordinatorState:
    """State maintained by the coordinator agent."""
    active_events: Dict[str, DisasterEvent] = field(default_factory=dict)
    agent_assignments: Dict[str, List[str]] = field(default_factory=dict)
    resource_allocation: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    communication_log: List[AgentMessage] = field(default_factory=list)
    system_status: str = "normal"
    last_update: datetime = field(default_factory=datetime.now)

class DisasterCoordinator:
    """Central coordinator for multi-agent disaster response."""
    
    def __init__(self):
        self.agent_id = "disaster_coordinator"
        self.role = AgentRole.COORDINATOR
        self.state = CoordinatorState()
        
        # Initialize available agents
        self.available_agents = {
            "wildfire_expert": create_disaster_expert(DisasterType.WILDFIRE),
            "flood_expert": create_disaster_expert(DisasterType.FLOOD),
            "earthquake_expert": create_disaster_expert(DisasterType.EARTHQUAKE),
            "hurricane_expert": create_disaster_expert(DisasterType.HURRICANE),
        }
        
        # Available resources (in real system, this would be dynamic)
        self.available_resources = {
            "personnel": {
                "firefighters": 200,
                "emergency_responders": 150,
                "medical_teams": 25,
                "search_rescue": 50,
                "structural_engineers": 12
            },
            "equipment": {
                "aircraft": 8,
                "helicopters": 6,
                "ground_vehicles": 40,
                "boats": 15,
                "medical_equipment": 30
            },
            "facilities": {
                "shelters": 12,
                "hospitals": 5,
                "command_centers": 3,
                "supply_depots": 8
            }
        }
        
        # Build coordination graph
        self.graph = self._build_coordination_graph()
    
    def _build_coordination_graph(self) -> StateGraph:
        """Build the LangGraph coordination workflow."""
        
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("assess_situation", self._assess_situation)
        workflow.add_node("classify_disaster", self._classify_disaster)
        workflow.add_node("activate_experts", self._activate_experts)
        workflow.add_node("coordinate_response", self._coordinate_response)
        workflow.add_node("monitor_progress", self._monitor_progress)
        workflow.add_node("update_status", self._update_status)
        
        # Define workflow edges
        workflow.set_entry_point("assess_situation")
        
        workflow.add_edge("assess_situation", "classify_disaster")
        workflow.add_edge("classify_disaster", "activate_experts")
        workflow.add_edge("activate_experts", "coordinate_response")
        workflow.add_edge("coordinate_response", "monitor_progress")
        workflow.add_edge("monitor_progress", "update_status")
        workflow.add_edge("update_status", END)
        
        return workflow.compile()
    
    async def _assess_situation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the incoming disaster situation."""
        
        input_data = state.get("input_data", {})
        
        # Process multi-modal inputs
        situation_assessment = {
            "timestamp": datetime.now().isoformat(),
            "input_type": input_data.get("type", "unknown"),
            "location": input_data.get("location", {}),
            "severity_indicators": [],
            "confidence": 0.5
        }
        
        # Use LLM for initial assessment
        if input_data:
            assessment = await llm_client.process_multimodal_input(
                input_data, input_data.get("type", "sensor")
            )
            situation_assessment.update(assessment)
        
        state["situation_assessment"] = situation_assessment
        state["coordinator_log"] = [f"Situation assessed at {datetime.now()}"]
        
        return state
    
    async def _classify_disaster(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the type of disaster based on assessment."""
        
        assessment = state.get("situation_assessment", {})
        
        # Disaster classification logic
        indicators = assessment.get("disaster_indicators", [])
        classification_scores = {
            DisasterType.WILDFIRE: 0.0,
            DisasterType.FLOOD: 0.0,
            DisasterType.EARTHQUAKE: 0.0,
            DisasterType.HURRICANE: 0.0
        }
        
        # Score based on indicators
        for indicator in indicators:
            if any(term in indicator.lower() for term in ["fire", "smoke", "burn", "heat"]):
                classification_scores[DisasterType.WILDFIRE] += 0.3
            elif any(term in indicator.lower() for term in ["flood", "water", "rain", "river"]):
                classification_scores[DisasterType.FLOOD] += 0.3
            elif any(term in indicator.lower() for term in ["earthquake", "seismic", "tremor", "shake"]):
                classification_scores[DisasterType.EARTHQUAKE] += 0.3
            elif any(term in indicator.lower() for term in ["hurricane", "storm", "wind", "cyclone"]):
                classification_scores[DisasterType.HURRICANE] += 0.3
        
        # Determine primary disaster type
        primary_disaster = max(classification_scores, key=classification_scores.get)
        confidence = classification_scores[primary_disaster]
        
        # Create disaster event
        location_data = assessment.get("geographic_info", {})
        location = Location(
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0),
            region=location_data.get("region", "Unknown"),
            country=location_data.get("country", "Unknown")
        )
        
        event_id = f"{primary_disaster.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        disaster_event = DisasterEvent(
            event_id=event_id,
            disaster_type=primary_disaster,
            location=location,
            start_time=datetime.now(),
            alert_level=AlertLevel.MODERATE,
            description=f"Detected {primary_disaster.value} event",
            affected_area=assessment.get("affected_area", 10.0),
            estimated_population=assessment.get("estimated_population", 1000),
            confidence_score=confidence
        )
        
        # Store event
        self.state.active_events[event_id] = disaster_event
        
        state["disaster_event"] = disaster_event
        state["primary_disaster_type"] = primary_disaster
        state["classification_confidence"] = confidence
        state["coordinator_log"].append(f"Classified as {primary_disaster.value} (confidence: {confidence:.2f})")
        
        return state
    
    async def _activate_experts(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Activate appropriate expert agents for the disaster."""
        
        disaster_event = state.get("disaster_event")
        primary_type = state.get("primary_disaster_type")
        
        # Select primary expert
        primary_expert_key = f"{primary_type.value}_expert"
        activated_experts = [primary_expert_key]
        
        # Activate supporting experts based on severity and type
        if disaster_event.confidence_score > 0.7:
            # High confidence - activate additional support
            if primary_type == DisasterType.WILDFIRE:
                activated_experts.extend(["flood_expert"])  # For water drops
            elif primary_type == DisasterType.FLOOD:
                activated_experts.extend(["earthquake_expert"])  # For dam integrity
            elif primary_type == DisasterType.HURRICANE:
                activated_experts.extend(["flood_expert"])  # For storm surge
        
        # Assign tasks to experts
        expert_assignments = {}
        for expert_key in activated_experts:
            if expert_key in self.available_agents:
                expert = self.available_agents[expert_key]
                
                if expert_key == primary_expert_key:
                    # Primary expert gets full analysis
                    expert_assignments[expert_key] = [
                        "analyze_conditions",
                        "predict_evolution",
                        "recommend_response",
                        "monitor_situation"
                    ]
                else:
                    # Supporting experts get specific tasks
                    expert_assignments[expert_key] = [
                        "analyze_conditions",
                        "provide_specialized_input"
                    ]
        
        state["activated_experts"] = activated_experts
        state["expert_assignments"] = expert_assignments
        state["coordinator_log"].append(f"Activated experts: {activated_experts}")
        
        return state
    
    async def _coordinate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate response actions across all agents."""
        
        disaster_event = state.get("disaster_event")
        expert_assignments = state.get("expert_assignments", {})
        
        # Collect expert analyses
        expert_results = {}
        coordination_tasks = []
        
        for expert_key, tasks in expert_assignments.items():
            if expert_key in self.available_agents:
                expert = self.available_agents[expert_key]
                
                # Create coordination task for each expert
                task = self._coordinate_expert_analysis(
                    expert, disaster_event, tasks
                )
                coordination_tasks.append(task)
        
        # Execute expert analyses in parallel
        expert_analyses = await asyncio.gather(*coordination_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(expert_analyses):
            expert_key = list(expert_assignments.keys())[i]
            if not isinstance(result, Exception):
                expert_results[expert_key] = result
        
        # Use LLM to create overall coordination plan
        coordination_data = {
            "disaster_event": disaster_event.to_dict(),
            "expert_analyses": expert_results,
            "available_resources": self.available_resources
        }
        
        coordination_plan = await llm_client.coordinate_agents(
            coordination_data,
            list(expert_assignments.keys())
        )
        
        # Allocate resources
        resource_allocation = self._allocate_resources(
            disaster_event, coordination_plan, expert_results
        )
        
        state["expert_results"] = expert_results
        state["coordination_plan"] = coordination_plan
        state["resource_allocation"] = resource_allocation
        state["coordinator_log"].append("Response coordination completed")
        
        return state
    
    async def _coordinate_expert_analysis(
        self,
        expert,
        disaster_event: DisasterEvent,
        tasks: List[str]
    ) -> Dict[str, Any]:
        """Coordinate analysis from a specific expert."""
        
        results = {"expert_id": expert.agent_id, "analyses": {}}
        
        try:
            # Simulate sensor data for analysis
            sensor_data = [
                SensorData(
                    sensor_id="sensor_001",
                    sensor_type="weather",
                    location=disaster_event.location,
                    timestamp=datetime.now(),
                    readings={
                        "temperature": 32.5,
                        "humidity": 25.0,
                        "wind_speed": 28.0,
                        "pressure": 1010.2
                    }
                )
            ]
            
            weather_data = {
                "temperature": 32.5,
                "humidity": 25.0,
                "wind_speed": 28.0,
                "precipitation": 0.0
            }
            
            if "analyze_conditions" in tasks:
                condition_analysis = await expert.analyze_conditions(
                    sensor_data, weather_data
                )
                results["analyses"]["conditions"] = condition_analysis
            
            if "predict_evolution" in tasks:
                evolution_prediction = await expert.predict_evolution(
                    weather_data, disaster_event.location
                )
                results["analyses"]["evolution"] = evolution_prediction
            
            if "recommend_response" in tasks:
                response_recommendation = await expert.recommend_response(
                    disaster_event, self.available_resources
                )
                results["analyses"]["response"] = response_recommendation
                
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def _allocate_resources(
        self,
        disaster_event: DisasterEvent,
        coordination_plan: Dict[str, Any],
        expert_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Allocate available resources based on coordination plan."""
        
        allocation = {
            "event_id": disaster_event.event_id,
            "allocation_timestamp": datetime.now().isoformat(),
            "resource_assignments": {},
            "priority_level": coordination_plan.get("priorities", [3])[0]
        }
        
        # Base allocation based on disaster type and severity
        severity_multiplier = disaster_event.confidence_score
        population_factor = min(disaster_event.estimated_population / 1000, 5.0)
        
        if disaster_event.disaster_type == DisasterType.WILDFIRE:
            allocation["resource_assignments"] = {
                "firefighters": min(int(50 * severity_multiplier), self.available_resources["personnel"]["firefighters"]),
                "aircraft": min(int(3 * severity_multiplier), self.available_resources["equipment"]["aircraft"]),
                "ground_vehicles": min(int(10 * severity_multiplier), self.available_resources["equipment"]["ground_vehicles"])
            }
        elif disaster_event.disaster_type == DisasterType.FLOOD:
            allocation["resource_assignments"] = {
                "emergency_responders": min(int(30 * severity_multiplier), self.available_resources["personnel"]["emergency_responders"]),
                "boats": min(int(8 * severity_multiplier), self.available_resources["equipment"]["boats"]),
                "shelters": min(int(3 * population_factor), self.available_resources["facilities"]["shelters"])
            }
        
        # Update available resources
        for resource_type, amount in allocation["resource_assignments"].items():
            for category in self.available_resources.values():
                if resource_type in category:
                    category[resource_type] = max(0, category[resource_type] - amount)
        
        return allocation
    
    async def _monitor_progress(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor progress of ongoing response efforts."""
        
        disaster_event = state.get("disaster_event")
        coordination_plan = state.get("coordination_plan", {})
        
        # Simulate progress monitoring
        progress_metrics = {
            "event_id": disaster_event.event_id,
            "monitoring_timestamp": datetime.now().isoformat(),
            "response_effectiveness": 0.75,  # Simulated
            "resource_utilization": 0.85,    # Simulated
            "situation_status": "under_control",
            "estimated_resolution_time": "6 hours",
            "key_milestones": [
                {"milestone": "Initial response deployed", "status": "completed", "timestamp": datetime.now().isoformat()},
                {"milestone": "Evacuation initiated", "status": "in_progress", "timestamp": (datetime.now() + timedelta(minutes=30)).isoformat()},
                {"milestone": "Containment achieved", "status": "pending", "timestamp": (datetime.now() + timedelta(hours=4)).isoformat()}
            ]
        }
        
        state["progress_monitoring"] = progress_metrics
        state["coordinator_log"].append("Progress monitoring initiated")
        
        return state
    
    async def _update_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Update overall system status and prepare final report."""
        
        disaster_event = state.get("disaster_event")
        coordination_plan = state.get("coordination_plan", {})
        progress_monitoring = state.get("progress_monitoring", {})
        
        # Update coordinator state
        self.state.last_update = datetime.now()
        self.state.system_status = "active_response"
        
        # Create final coordination report
        final_report = {
            "coordination_summary": {
                "event_id": disaster_event.event_id,
                "disaster_type": disaster_event.disaster_type.value,
                "alert_level": disaster_event.alert_level.value,
                "coordination_timestamp": datetime.now().isoformat(),
                "activated_experts": state.get("activated_experts", []),
                "resource_allocation": state.get("resource_allocation", {}),
                "progress_status": progress_monitoring.get("situation_status", "unknown")
            },
            "next_actions": [
                "Continue monitoring situation",
                "Adjust resource allocation as needed",
                "Coordinate with local authorities",
                "Prepare damage assessment"
            ],
            "estimated_duration": coordination_plan.get("timeline", "unknown"),
            "success_probability": 0.8  # Simulated
        }
        
        state["final_report"] = final_report
        state["coordinator_log"].append("Status update completed")
        
        return state
    
    async def process_disaster_alert(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Main entry point for processing disaster alerts."""
        
        # Initialize state
        initial_state = {
            "input_data": input_data,
            "coordinator_log": []
        }
        
        # Execute coordination workflow
        result = await self.graph.ainvoke(initial_state)
        
        return result
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        
        active_events_summary = {}
        for event_id, event in self.state.active_events.items():
            active_events_summary[event_id] = {
                "disaster_type": event.disaster_type.value,
                "alert_level": event.alert_level.value,
                "start_time": event.start_time.isoformat(),
                "confidence": event.confidence_score
            }
        
        return {
            "coordinator_id": self.agent_id,
            "system_status": self.state.system_status,
            "last_update": self.state.last_update.isoformat(),
            "active_events": active_events_summary,
            "available_agents": list(self.available_agents.keys()),
            "resource_status": self.available_resources,
            "total_events_handled": len(self.state.active_events)
        }

# Global coordinator instance
disaster_coordinator = DisasterCoordinator()
