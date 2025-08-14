"""Disaster-specific expert agents for the emergency management platform."""
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
# MODIFIED: Changed ToolExecutor to ToolNode
from langgraph.prebuilt import ToolNode


from ..core.models import (
    DisasterEvent, DisasterType, Location, AlertLevel, 
    ModelResult, SensorData, MultiModalInput
)
from ..core.llm import llm_client
from ..MCP.client import mcp_client

class DisasterExpertAgent:
    """Base class for disaster-specific expert agents."""
    
    def __init__(self, disaster_type: DisasterType, agent_id: str):
        self.disaster_type = disaster_type
        self.agent_id = agent_id
        self.specialized_knowledge = self._load_specialized_knowledge()
        self.active_events = {}
        
    def _load_specialized_knowledge(self) -> Dict[str, Any]:
        """Load specialized knowledge for this disaster type."""
        knowledge_base = {
            DisasterType.WILDFIRE: {
                "key_indicators": ["temperature", "humidity", "wind_speed", "fuel_moisture"],
                "critical_thresholds": {
                    "temperature": 35.0,  # °C
                    "humidity": 20.0,     # %
                    "wind_speed": 25.0,   # km/h
                    "fuel_moisture": 8.0  # %
                },
                "response_protocols": [
                    "immediate_evacuation", "fire_suppression", "perimeter_control",
                    "air_support", "resource_deployment"
                ],
                "prediction_models": ["cell2fire", "nfdrs4"]
            },
            DisasterType.FLOOD: {
                "key_indicators": ["precipitation", "river_level", "soil_saturation", "dam_status"],
                "critical_thresholds": {
                    "precipitation": 50.0,      # mm/hour
                    "river_level": 8.5,         # meters
                    "soil_saturation": 90.0,    # %
                    "dam_capacity": 95.0        # %
                },
                "response_protocols": [
                    "evacuation_zones", "dam_release", "emergency_shelters",
                    "rescue_operations", "infrastructure_protection"
                ],
                "prediction_models": ["lisflood"]
            },
            DisasterType.EARTHQUAKE: {
                "key_indicators": ["seismic_activity", "ground_acceleration", "magnitude"],
                "critical_thresholds": {
                    "magnitude": 6.0,           # Richter scale
                    "ground_acceleration": 0.3, # g
                    "aftershock_probability": 0.7 # probability
                },
                "response_protocols": [
                    "search_rescue", "medical_response", "infrastructure_assessment",
                    "aftershock_monitoring", "emergency_communication"
                ],
                "prediction_models": ["seismic_model"]
            },
            DisasterType.HURRICANE: {
                "key_indicators": ["wind_speed", "pressure", "storm_surge", "precipitation"],
                "critical_thresholds": {
                    "wind_speed": 119.0,    # km/h (Category 1)
                    "pressure": 980.0,      # hPa
                    "storm_surge": 2.0,     # meters
                    "precipitation": 200.0  # mm/24h
                },
                "response_protocols": [
                    "mass_evacuation", "shelter_operations", "emergency_supplies",
                    "infrastructure_shutdown", "coastal_protection"
                ],
                "prediction_models": ["pangu", "aurora"]
            }
        }
        return knowledge_base.get(self.disaster_type, {})
    
    async def analyze_conditions(
        self, 
        sensor_data: List[SensorData], 
        weather_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze current conditions for disaster risk."""
        
        # Extract relevant indicators
        indicators = {}
        for sensor in sensor_data:
            for key, value in sensor.readings.items():
                if key in self.specialized_knowledge.get("key_indicators", []):
                    indicators[key] = value
        
        # Add weather data
        indicators.update(weather_data)
        
        # Check against thresholds
        risk_factors = []
        thresholds = self.specialized_knowledge.get("critical_thresholds", {})
        
        for indicator, value in indicators.items():
            if indicator in thresholds:
                threshold = thresholds[indicator]
                if value >= threshold:
                    risk_factors.append({
                        "indicator": indicator,
                        "value": value,
                        "threshold": threshold,
                        "severity": min((value / threshold), 2.0)
                    })
        
        # Use LLM for expert analysis
        analysis_data = {
            "disaster_type": self.disaster_type.value,
            "indicators": indicators,
            "risk_factors": risk_factors,
            "thresholds": thresholds
        }
        
        expert_analysis = await llm_client.analyze_disaster_data(
            analysis_data, self.disaster_type
        )
        
        return {
            "agent_id": self.agent_id,
            "disaster_type": self.disaster_type.value,
            "analysis_timestamp": datetime.now().isoformat(),
            "raw_indicators": indicators,
            "risk_factors": risk_factors,
            "expert_assessment": expert_analysis,
            "recommended_actions": expert_analysis.get("recommended_actions", [])
        }
    
    async def predict_evolution(
        self, 
        current_conditions: Dict[str, Any],
        location: Location
    ) -> Dict[str, Any]:
        """Predict how the disaster will evolve."""
        
        predictions = []
        
        # Call relevant prediction models
        model_names = self.specialized_knowledge.get("prediction_models", [])
        
        for model_name in model_names:
            try:
                if model_name == "cell2fire" and self.disaster_type == DisasterType.WILDFIRE:
                    result = await mcp_client.call_cell2fire_model(
                        location=location,
                        weather_data=current_conditions,
                        fuel_data={"fuel_type": "mixed", "moisture": 8.5},
                        ignition_points=[{"lat": location.latitude, "lon": location.longitude, "intensity": 100}]
                    )
                    predictions.append(result)
                    
                elif model_name == "lisflood" and self.disaster_type == DisasterType.FLOOD:
                    result = await mcp_client.call_lisflood_model(
                        location=location,
                        precipitation_data=current_conditions,
                        terrain_data={"elevation": location.elevation or 100, "slope": 5.2}
                    )
                    predictions.append(result)
                    
            except Exception as e:
                print(f"Error calling {model_name}: {e}")
        
        return {
            "agent_id": self.agent_id,
            "prediction_timestamp": datetime.now().isoformat(),
            "model_predictions": [pred.to_dict() for pred in predictions],
            "evolution_timeline": self._generate_timeline(predictions),
            "confidence_score": sum([p.confidence for p in predictions]) / len(predictions) if predictions else 0.5
        }
    
    def _generate_timeline(self, predictions: List[ModelResult]) -> List[Dict[str, Any]]:
        """Generate evolution timeline from model predictions."""
        timeline = []
        current_time = datetime.now()
        
        # Generate timeline based on disaster type
        if self.disaster_type == DisasterType.WILDFIRE:
            timeline = [
                {"time": current_time + timedelta(hours=1), "event": "Initial spread", "severity": "moderate"},
                {"time": current_time + timedelta(hours=6), "event": "Peak intensity", "severity": "high"},
                {"time": current_time + timedelta(hours=12), "event": "Containment efforts", "severity": "moderate"},
                {"time": current_time + timedelta(hours=24), "event": "Controlled", "severity": "low"}
            ]
        elif self.disaster_type == DisasterType.FLOOD:
            timeline = [
                {"time": current_time + timedelta(hours=2), "event": "Water level rising", "severity": "moderate"},
                {"time": current_time + timedelta(hours=6), "event": "Peak flood level", "severity": "critical"},
                {"time": current_time + timedelta(hours=18), "event": "Water receding", "severity": "moderate"},
                {"time": current_time + timedelta(hours=48), "event": "Normal levels", "severity": "low"}
            ]
        
        # Convert datetime to ISO format
        for event in timeline:
            event["time"] = event["time"].isoformat()
        
        return timeline
    
    async def recommend_response(
        self, 
        disaster_event: DisasterEvent,
        available_resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend specific response actions."""
        
        # Get base protocols for this disaster type
        protocols = self.specialized_knowledge.get("response_protocols", [])
        
        # Use LLM to customize recommendations
        recommendation_data = {
            "disaster_event": disaster_event.to_dict(),
            "available_resources": available_resources,
            "protocols": protocols,
            "specialized_knowledge": self.specialized_knowledge
        }
        
        expert_recommendations = await llm_client.coordinate_agents(
            recommendation_data,
            ["responder", "analyst"]
        )
        
        return {
            "agent_id": self.agent_id,
            "event_id": disaster_event.event_id,
            "recommendation_timestamp": datetime.now().isoformat(),
            "priority_actions": expert_recommendations.get("agent_assignments", {}).get("responder", []),
            "resource_allocation": self._allocate_resources(available_resources, disaster_event),
            "timeline": expert_recommendations.get("timeline", "immediate"),
            "coordination_plan": expert_recommendations
        }
    
    def _allocate_resources(
        self, 
        available_resources: Dict[str, Any], 
        event: DisasterEvent
    ) -> Dict[str, Any]:
        """Allocate resources based on disaster type and severity."""
        
        allocation = {}
        
        if self.disaster_type == DisasterType.WILDFIRE:
            allocation = {
                "firefighters": min(available_resources.get("firefighters", 0), event.estimated_population // 50),
                "aircraft": min(available_resources.get("aircraft", 0), 5),
                "ground_vehicles": min(available_resources.get("ground_vehicles", 0), 10),
                "water_tankers": min(available_resources.get("water_tankers", 0), 8)
            }
        elif self.disaster_type == DisasterType.FLOOD:
            allocation = {
                "rescue_boats": min(available_resources.get("rescue_boats", 0), 12),
                "helicopters": min(available_resources.get("helicopters", 0), 3),
                "emergency_personnel": min(available_resources.get("emergency_personnel", 0), event.estimated_population // 100),
                "shelters": min(available_resources.get("shelters", 0), event.estimated_population // 200)
            }
        
        return allocation

class WildfireExpert(DisasterExpertAgent):
    """Specialized agent for wildfire disasters."""
    
    def __init__(self):
        super().__init__(DisasterType.WILDFIRE, "wildfire_expert")
    
    async def assess_fire_behavior(
        self, 
        weather_data: Dict[str, Any], 
        fuel_data: Dict[str, Any],
        terrain_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess fire behavior based on weather, fuel, and terrain."""
        
        # Calculate fire danger rating
        temperature = weather_data.get("temperature", 20)
        humidity = weather_data.get("humidity", 50)
        wind_speed = weather_data.get("wind_speed", 10)
        
        # Haines Index calculation (simplified)
        haines_index = ((temperature - 10) / 5) + ((100 - humidity) / 20)
        
        # Fire Weather Index calculation (simplified)
        fwi = (temperature * wind_speed) / (humidity + 10)
        
        return {
            "fire_danger_rating": min(haines_index * fwi / 10, 10),
            "spread_probability": min((wind_speed * (100 - humidity)) / 1000, 1.0),
            "suppression_difficulty": max(wind_speed / 50, 0.1),
            "evacuation_urgency": "immediate" if fwi > 20 else "planned",
            "resource_requirements": {
                "priority": "critical" if fwi > 25 else "high",
                "air_support_needed": wind_speed > 30,
                "ground_crew_size": max(int(fwi * 2), 10)
            }
        }

class FloodExpert(DisasterExpertAgent):
    """Specialized agent for flood disasters."""
    
    def __init__(self):
        super().__init__(DisasterType.FLOOD, "flood_expert")
    
    async def assess_flood_risk(
        self, 
        precipitation_data: Dict[str, Any],
        river_data: Dict[str, Any],
        infrastructure_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess flood risk based on precipitation, river levels, and infrastructure."""
        
        rainfall_intensity = precipitation_data.get("intensity", 0)  # mm/hour
        river_level = river_data.get("current_level", 0)  # meters
        dam_capacity = infrastructure_data.get("dam_capacity_used", 0)  # %
        
        # Flood risk calculation
        risk_score = (
            (rainfall_intensity / 50) * 0.4 +
            (river_level / 10) * 0.4 +
            (dam_capacity / 100) * 0.2
        )
        
        return {
            "flood_risk_score": min(risk_score, 1.0),
            "inundation_probability": min(risk_score * 1.2, 1.0),
            "evacuation_zones": self._identify_evacuation_zones(river_level, rainfall_intensity),
            "dam_release_recommendation": dam_capacity > 90,
            "rescue_preparation": {
                "boats_needed": max(int(risk_score * 10), 2),
                "personnel_required": max(int(risk_score * 50), 10),
                "shelters_to_activate": max(int(risk_score * 5), 1)
            }
        }
    
    def _identify_evacuation_zones(self, river_level: float, rainfall: float) -> List[Dict[str, Any]]:
        """Identify areas that need evacuation."""
        zones = []
        
        if river_level > 8 or rainfall > 40:
            zones.extend([
                {"zone": "Riverside District", "priority": "immediate", "population": 2500},
                {"zone": "Downtown Low Areas", "priority": "high", "population": 1800}
            ])
        
        if river_level > 6 or rainfall > 25:
            zones.append({"zone": "Floodplains", "priority": "moderate", "population": 3200})
        
        return zones

class EarthquakeExpert(DisasterExpertAgent):
    """Specialized agent for earthquake disasters."""
    
    def __init__(self):
        super().__init__(DisasterType.EARTHQUAKE, "earthquake_expert")
    
    async def assess_seismic_risk(
        self, 
        seismic_data: Dict[str, Any],
        infrastructure_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess earthquake risk and impact."""
        
        magnitude = seismic_data.get("magnitude", 0)
        depth = seismic_data.get("depth", 10)  # km
        building_vulnerability = infrastructure_data.get("vulnerability_index", 0.5)
        
        # Impact assessment
        intensity = magnitude - 0.0031 * depth  # Modified Mercalli intensity
        damage_probability = min((magnitude - 4) / 5, 1.0) * building_vulnerability
        
        return {
            "seismic_intensity": intensity,
            "damage_probability": damage_probability,
            "aftershock_likelihood": min(magnitude / 10, 0.9),
            "search_rescue_priority": damage_probability > 0.5,
            "infrastructure_assessment_needed": magnitude > 5.5,
            "response_requirements": {
                "search_rescue_teams": max(int(damage_probability * 20), 2),
                "medical_teams": max(int(damage_probability * 15), 3),
                "structural_engineers": max(int(magnitude), 2)
            }
        }

class HurricaneExpert(DisasterExpertAgent):
    """Specialized agent for hurricane disasters."""
    
    def __init__(self):
        super().__init__(DisasterType.HURRICANE, "hurricane_expert")
    
    async def assess_hurricane_impact(
        self, 
        storm_data: Dict[str, Any],
        coastal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess hurricane impact and required response."""
        
        wind_speed = storm_data.get("wind_speed", 0)  # km/h
        pressure = storm_data.get("pressure", 1013)  # hPa
        storm_surge = storm_data.get("surge_height", 0)  # meters
        
        # Hurricane category
        category = self._get_category(wind_speed)
        
        # Impact assessment
        wind_damage = min(wind_speed / 250, 1.0)
        surge_damage = min(storm_surge / 10, 1.0)
        combined_impact = max(wind_damage, surge_damage)
        
        return {
            "hurricane_category": category,
            "wind_damage_potential": wind_damage,
            "surge_damage_potential": surge_damage,
            "combined_impact_score": combined_impact,
            "evacuation_mandatory": wind_speed > 150 or storm_surge > 3,
            "landfall_preparation": {
                "shelters_needed": max(int(combined_impact * 10), 3),
                "evacuation_time": "72 hours" if category >= 3 else "48 hours",
                "emergency_supplies": max(int(combined_impact * 1000), 500)
            }
        }
    
    def _get_category(self, wind_speed: float) -> int:
        """Get hurricane category based on wind speed."""
        if wind_speed >= 252:
            return 5
        elif wind_speed >= 209:
            return 4
        elif wind_speed >= 178:
            return 3
        elif wind_speed >= 154:
            return 2
        elif wind_speed >= 119:
            return 1
        else:
            return 0

# Agent factory
def create_disaster_expert(disaster_type: DisasterType) -> DisasterExpertAgent:
    """Create appropriate disaster expert agent."""
    agents = {
        DisasterType.WILDFIRE: WildfireExpert,
        DisasterType.FLOOD: FloodExpert,
        DisasterType.EARTHQUAKE: EarthquakeExpert,
        DisasterType.HURRICANE: HurricaneExpert
    }
    
    agent_class = agents.get(disaster_type, DisasterExpertAgent)
    return agent_class() if disaster_type in agents else DisasterExpertAgent(disaster_type, f"{disaster_type.value}_expert")