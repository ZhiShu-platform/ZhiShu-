"""Emergency management tools for disaster response agents."""
import os
import json
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv

from ..core.models import DisasterType, Location, ModelResult
from ..core.config import config
from ..MCP.client import mcp_client

# Load environment variables
load_dotenv()

# ==============================================================================
# Disaster Simulation Tools
# ==============================================================================

@tool
def run_wildfire_simulation(
    location_data: Dict[str, Any], 
    weather_conditions: Dict[str, Any],
    fuel_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute wildfire spread simulation using Cell2Fire model.
    
    Args:
        location_data: Geographic area data including latitude, longitude, region
        weather_conditions: Weather data including temperature, humidity, wind speed
        fuel_data: Optional fuel moisture and type data
        
    Returns:
        Dictionary with simulation results including spread predictions and containment estimates
    """
    print("🔥 Running wildfire simulation (Cell2Fire)...")
    print(f"   - Location: {location_data}")
    print(f"   - Weather: {weather_conditions}")
    
    try:
        # Create location object
        location = Location(
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0),
            region=location_data.get("region", "Unknown")
        )
        
        # Prepare fuel data
        if fuel_data is None:
            fuel_data = {
                "fuel_type": "mixed_forest",
                "moisture": weather_conditions.get("humidity", 30) / 10,  # Convert to fuel moisture
                "load": 15.0  # tons per hectare
            }
        
        # Prepare ignition points
        ignition_points = [{
            "lat": location.latitude,
            "lon": location.longitude,
            "intensity": 100  # kW/m
        }]
        
        # Call Cell2Fire model via MCP
        result = asyncio.run(mcp_client.call_cell2fire_model(
            location=location,
            weather_data=weather_conditions,
            fuel_data=fuel_data,
            ignition_points=ignition_points
        ))
        
        simulation_output = {
            "simulation_id": f"wildfire_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "spread_area_km2": result.predictions.get("final_burned_area", 0),
            "time_to_contain_hours": result.predictions.get("containment_time", 48),
            "confidence_score": result.confidence,
            "fire_perimeter": result.predictions.get("perimeter_coords", []),
            "peak_fire_weather_index": weather_conditions.get("temperature", 20) * 
                                     weather_conditions.get("wind_speed", 10) / 
                                     (weather_conditions.get("humidity", 50) + 10)
        }
        
        return {"status": "success", "data": simulation_output}
        
    except Exception as e:
        print(f"   - [ERROR] Wildfire simulation failed: {e}")
        return {
            "status": "error", 
            "message": f"Wildfire simulation failed: {str(e)}",
            "fallback_data": {
                "estimated_spread_area_km2": 5.0,
                "time_to_contain_hours": 72,
                "confidence_score": 0.3
            }
        }


@tool
def run_flood_simulation(
    location_data: Dict[str, Any],
    precipitation_data: Dict[str, Any],
    terrain_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute flood simulation using LisFlood model.
    
    Args:
        location_data: Geographic area data
        precipitation_data: Rainfall intensity and duration data
        terrain_data: Optional elevation and slope data
        
    Returns:
        Dictionary with flood simulation results including inundation areas and depths
    """
    print("🌊 Running flood simulation (LisFlood)...")
    print(f"   - Location: {location_data}")
    print(f"   - Precipitation: {precipitation_data}")
    
    try:
        location = Location(
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0),
            region=location_data.get("region", "Unknown")
        )
        
        if terrain_data is None:
            terrain_data = {
                "elevation": 100,  # meters
                "slope": 5.0,      # degrees
                "soil_type": "mixed"
            }
        
        # Call LisFlood model via MCP
        result = asyncio.run(mcp_client.call_lisflood_model(
            location=location,
            precipitation_data=precipitation_data,
            terrain_data=terrain_data
        ))
        
        simulation_output = {
            "simulation_id": f"flood_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "max_water_depth_m": result.predictions.get("max_depth", 0),
            "inundated_area_km2": result.predictions.get("flooded_area", 0),
            "peak_flow_time_hours": result.predictions.get("peak_time", 6),
            "confidence_score": result.confidence,
            "evacuation_zones": result.predictions.get("critical_zones", [])
        }
        
        return {"status": "success", "data": simulation_output}
        
    except Exception as e:
        print(f"   - [ERROR] Flood simulation failed: {e}")
        return {
            "status": "error",
            "message": f"Flood simulation failed: {str(e)}",
            "fallback_data": {
                "estimated_inundated_area_km2": 2.0,
                "max_water_depth_m": 1.5,
                "confidence_score": 0.3
            }
        }


# ==============================================================================
# Damage Assessment Tools
# ==============================================================================

@tool
def run_damage_assessment(
    disaster_type: str, 
    disaster_impact_data: Dict[str, Any],
    exposure_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute damage assessment using CLIMADA model.
    
    Args:
        disaster_type: Type of disaster ('wildfire', 'flood', 'earthquake', 'hurricane')
        disaster_impact_data: Impact data from simulation (spread area, intensity, etc.)
        exposure_data: Optional building and population exposure data
        
    Returns:
        Dictionary with economic loss estimates and affected population counts
    """
    print("💰 Running damage assessment (CLIMADA)...")
    print(f"   - Disaster type: {disaster_type}")
    print(f"   - Impact data: {disaster_impact_data}")
    
    try:
        # Parse disaster type
        disaster_enum = DisasterType(disaster_type.lower())
        
        # Prepare exposure data
        if exposure_data is None:
            exposure_data = {
                "buildings": 500,
                "population": 2500,
                "infrastructure_value_usd": 50000000
            }
        
        # Prepare hazard data based on disaster type
        if disaster_type == "wildfire":
            hazard_data = {
                "intensity": min(disaster_impact_data.get("peak_fire_weather_index", 10) / 30, 1.0),
                "duration": disaster_impact_data.get("time_to_contain_hours", 48),
                "affected_area": disaster_impact_data.get("spread_area_km2", 5.0)
            }
        elif disaster_type == "flood":
            hazard_data = {
                "intensity": disaster_impact_data.get("max_water_depth_m", 1.0),
                "duration": 24,  # hours
                "affected_area": disaster_impact_data.get("inundated_area_km2", 2.0)
            }
        else:
            hazard_data = {
                "intensity": 0.7,
                "duration": 12,
                "affected_area": 10.0
            }
        
        # Create location from impact data
        location = Location(
            latitude=disaster_impact_data.get("latitude", 0.0),
            longitude=disaster_impact_data.get("longitude", 0.0),
            region=disaster_impact_data.get("region", "Unknown")
        )
        
        # Call CLIMADA model via MCP
        result = asyncio.run(mcp_client.call_climada_model(
            location=location,
            disaster_type=disaster_enum,
            hazard_data=hazard_data,
            exposure_data=exposure_data
        ))
        
        assessment_output = {
            "assessment_id": f"damage_assess_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "estimated_economic_loss_usd": result.predictions.get("economic_loss", 0),
            "affected_population": result.predictions.get("affected_people", 0),
            "buildings_damaged": result.predictions.get("damaged_buildings", 0),
            "buildings_destroyed": result.predictions.get("destroyed_buildings", 0),
            "confidence_score": result.confidence,
            "assessment_timestamp": datetime.now().isoformat()
        }
        
        return {"status": "success", "data": assessment_output}
        
    except Exception as e:
        print(f"   - [ERROR] Damage assessment failed: {e}")
        
        # Provide fallback estimates based on disaster type and impact
        affected_area = disaster_impact_data.get("spread_area_km2", 
                       disaster_impact_data.get("inundated_area_km2", 5.0))
        
        fallback_estimates = {
            "estimated_economic_loss_usd": int(affected_area * 2000000),  # $2M per km²
            "affected_population": int(affected_area * 200),  # 200 people per km²
            "buildings_damaged": int(affected_area * 50),     # 50 buildings per km²
            "buildings_destroyed": int(affected_area * 10),   # 10 destroyed per km²
            "confidence_score": 0.3
        }
        
        return {
            "status": "error",
            "message": f"Damage assessment failed: {str(e)}",
            "fallback_data": fallback_estimates
        }


# ==============================================================================
# Weather and Environmental Tools
# ==============================================================================

@tool
def get_weather_forecast(
    location_data: Dict[str, Any],
    forecast_hours: int = 72
) -> Dict[str, Any]:
    """
    Get weather forecast for disaster response planning.
    
    Args:
        location_data: Geographic location data
        forecast_hours: Number of hours to forecast (default 72)
        
    Returns:
        Dictionary with weather forecast data
    """
    print(f"🌤️ Getting weather forecast for {forecast_hours} hours...")
    print(f"   - Location: {location_data}")
    
    try:
        location = Location(
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0),
            region=location_data.get("region", "Unknown")
        )
        
        # Call weather prediction models (Pangu/Aurora) via MCP
        # For now, provide simulated forecast data
        current_time = datetime.now()
        forecast_data = []
        
        for hour in range(0, forecast_hours, 6):  # 6-hour intervals
            forecast_time = current_time + timedelta(hours=hour)
            forecast_data.append({
                "timestamp": forecast_time.isoformat(),
                "temperature_c": 25 + (hour % 24 - 12) * 0.5,  # Simulated daily cycle
                "humidity_percent": 45 + (hour % 12) * 2,
                "wind_speed_kmh": 15 + (hour % 8) * 2,
                "wind_direction": "NW",
                "precipitation_mm": 0.0 if hour < 24 else 2.0,  # Rain after 24 hours
                "pressure_hpa": 1013 - hour * 0.1
            })
        
        return {
            "status": "success",
            "data": {
                "location": location.to_dict(),
                "forecast_hours": forecast_hours,
                "forecast_data": forecast_data,
                "generated_at": current_time.isoformat()
            }
        }
        
    except Exception as e:
        print(f"   - [ERROR] Weather forecast failed: {e}")
        return {
            "status": "error",
            "message": f"Weather forecast failed: {str(e)}"
        }


# ==============================================================================
# Resource Management Tools
# ==============================================================================

@tool
def check_available_resources(
    resource_type: str = "all",
    location_radius_km: float = 50.0
) -> Dict[str, Any]:
    """
    Check available emergency response resources.
    
    Args:
        resource_type: Type of resources to check ('personnel', 'equipment', 'facilities', 'all')
        location_radius_km: Search radius in kilometers
        
    Returns:
        Dictionary with available resource counts and locations
    """
    print(f"🚑 Checking available resources: {resource_type}")
    print(f"   - Search radius: {location_radius_km} km")
    
    try:
        # Simulated resource availability
        all_resources = {
            "personnel": {
                "firefighters": {"available": 150, "deployed": 50, "total": 200},
                "paramedics": {"available": 80, "deployed": 20, "total": 100},
                "police": {"available": 120, "deployed": 30, "total": 150},
                "search_rescue": {"available": 35, "deployed": 15, "total": 50}
            },
            "equipment": {
                "fire_trucks": {"available": 25, "deployed": 15, "total": 40},
                "ambulances": {"available": 18, "deployed": 7, "total": 25},
                "helicopters": {"available": 4, "deployed": 2, "total": 6},
                "boats": {"available": 12, "deployed": 3, "total": 15}
            },
            "facilities": {
                "hospitals": {"available": 4, "at_capacity": 1, "total": 5},
                "shelters": {"available": 8, "occupied": 4, "total": 12},
                "command_centers": {"available": 2, "active": 1, "total": 3}
            }
        }
        
        if resource_type == "all":
            result_data = all_resources
        else:
            result_data = {resource_type: all_resources.get(resource_type, {})}
        
        return {
            "status": "success",
            "data": {
                "resources": result_data,
                "search_radius_km": location_radius_km,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"   - [ERROR] Resource check failed: {e}")
        return {
            "status": "error",
            "message": f"Resource check failed: {str(e)}"
        }


# ==============================================================================
# Communication and Coordination Tools
# ==============================================================================

@tool
def send_emergency_alert(
    alert_level: str,
    message: str,
    target_areas: List[str],
    channels: List[str] = None
) -> Dict[str, Any]:
    """
    Send emergency alerts to specified areas and communication channels.
    
    Args:
        alert_level: Alert severity ('low', 'moderate', 'high', 'critical')
        message: Alert message content
        target_areas: List of geographic areas to alert
        channels: Communication channels to use (default: ['sms', 'radio', 'social_media'])
        
    Returns:
        Dictionary with alert delivery status
    """
    print(f"📢 Sending emergency alert: {alert_level}")
    print(f"   - Message: {message[:100]}...")
    print(f"   - Target areas: {target_areas}")
    
    if channels is None:
        channels = ['sms', 'radio', 'social_media', 'emergency_broadcast']
    
    try:
        # Simulate alert distribution
        delivery_results = {}
        
        for channel in channels:
            # Simulate different success rates by channel
            if channel == 'sms':
                success_rate = 0.95
            elif channel == 'radio':
                success_rate = 0.85
            elif channel == 'social_media':
                success_rate = 0.90
            else:
                success_rate = 0.80
            
            delivery_results[channel] = {
                "status": "delivered" if success_rate > 0.8 else "partial",
                "success_rate": success_rate,
                "estimated_reach": int(len(target_areas) * 1000 * success_rate)
            }
        
        return {
            "status": "success",
            "data": {
                "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "alert_level": alert_level,
                "target_areas": target_areas,
                "delivery_results": delivery_results,
                "sent_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"   - [ERROR] Alert sending failed: {e}")
        return {
            "status": "error",
            "message": f"Alert sending failed: {str(e)}"
        }


# ==============================================================================
# Workflow Control Tools
# ==============================================================================

@tool
def determine_next_action(
    current_stage: str,
    tool_outputs: List[Dict[str, Any]],
    disaster_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Determine the next action in the emergency response workflow.
    
    Args:
        current_stage: Current response stage
        tool_outputs: Results from previous tool executions
        disaster_context: Current disaster situation context
        
    Returns:
        Dictionary with next action recommendation and reasoning
    """
    print(f"🎯 Determining next action for stage: {current_stage}")
    print(f"   - Previous outputs: {len(tool_outputs)} results")
    
    try:
        next_actions = {
            "initial_alert": {
                "action": "RUN_SIMULATION",
                "priority": "high",
                "reasoning": "Initial alert received, need to run disaster simulation to understand scope"
            },
            "simulation_complete": {
                "action": "ASSESS_DAMAGE",
                "priority": "high", 
                "reasoning": "Simulation complete, now assess potential damage and economic impact"
            },
            "damage_assessed": {
                "action": "PLAN_RESPONSE",
                "priority": "critical",
                "reasoning": "Damage assessment complete, begin coordinated response planning"
            },
            "response_planned": {
                "action": "DEPLOY_RESOURCES",
                "priority": "critical",
                "reasoning": "Response plan ready, deploy emergency resources immediately"
            },
            "resources_deployed": {
                "action": "MONITOR_SITUATION",
                "priority": "medium",
                "reasoning": "Resources deployed, continue monitoring and adjust as needed"
            }
        }
        
        # Check for errors in previous outputs
        has_errors = any(output.get("status") == "error" for output in tool_outputs)
        if has_errors:
            return {
                "status": "success",
                "data": {
                    "next_action": "ESCALATE_TO_HUMAN",
                    "priority": "critical",
                    "reasoning": "Errors detected in previous operations, human oversight required"
                }
            }
        
        # Get recommended action for current stage
        recommendation = next_actions.get(current_stage, {
            "action": "CONTINUE_MONITORING",
            "priority": "medium", 
            "reasoning": f"Unknown stage '{current_stage}', defaulting to monitoring"
        })
        
        return {"status": "success", "data": recommendation}
        
    except Exception as e:
        print(f"   - [ERROR] Action determination failed: {e}")
        return {
            "status": "error",
            "message": f"Action determination failed: {str(e)}"
        }