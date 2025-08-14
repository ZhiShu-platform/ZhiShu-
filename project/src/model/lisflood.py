"""
Lisflood Model Interface

High-level interface for Lisflood hydrological modeling.
This module provides convenience functions for common Lisflood operations
using the MCP architecture.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..MCP.adapters.lisflood_adapter import LisfloodAdapter
from ..MCP.core.base_model import ModelResult
from ..MCP.sdk import MCPClient, ToolExecutor

logger = logging.getLogger(__name__)


class LisfloodModel:
    """
    High-level interface for Lisflood hydrological modeling.
    
    Provides simplified methods for common Lisflood operations.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self._adapter: Optional[LisfloodAdapter] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = MCPClient(self.server_url)
        await self._client.__aenter__()
        self._executor = ToolExecutor(self._client)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    # Flood Simulation Methods
    async def run_flood_simulation(
        self,
        start_date: str,
        end_date: str,
        settings_file: str,
        output_dir: str,
        time_step: str = "daily",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a complete flood simulation.
        
        Args:
            start_date: Simulation start date (YYYY-MM-DD or DD/MM/YYYY)
            end_date: Simulation end date (YYYY-MM-DD or DD/MM/YYYY)
            settings_file: Path to Lisflood settings XML file
            output_dir: Directory for simulation outputs
            time_step: Time step ('hourly', '6hourly', 'daily')
            
        Returns:
            Simulation results and output file paths
        """
        parameters = {
            "start_date": start_date,
            "end_date": end_date,
            "settings_file": settings_file,
            "output_dir": output_dir,
            "time_step": time_step,
            **kwargs
        }
        
        return await self._executor.run_lisflood_simulation(**parameters)
    
    async def run_water_balance_analysis(
        self,
        start_date: str,
        end_date: str,
        settings_file: str,
        output_dir: str,
        components: Optional[List[str]] = None,
        spatial_aggregation: str = "catchment",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run water balance analysis.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            settings_file: Path to settings file
            output_dir: Output directory
            components: Water balance components to analyze
            spatial_aggregation: Spatial aggregation level
            
        Returns:
            Water balance analysis results
        """
        parameters = {
            "start_date": start_date,
            "end_date": end_date,
            "settings_file": settings_file,
            "output_dir": output_dir,
            "components": components or ["precipitation", "evapotranspiration", "runoff"],
            "spatial_aggregation": spatial_aggregation,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "lisflood_water_balance",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    # Forecasting Methods
    async def run_flood_forecast(
        self,
        forecast_start: str,
        forecast_horizon: int,
        settings_file: str,
        meteorological_forecast: str,
        ensemble_size: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run flood forecasting with meteorological ensemble.
        
        Args:
            forecast_start: Forecast start date
            forecast_horizon: Forecast horizon in days
            settings_file: Path to settings file
            meteorological_forecast: Path to meteorological forecast data
            ensemble_size: Number of ensemble members
            
        Returns:
            Forecast results for all ensemble members
        """
        parameters = {
            "forecast_start": forecast_start,
            "forecast_horizon": forecast_horizon,
            "settings_file": settings_file,
            "meteorological_forecast": meteorological_forecast,
            "ensemble_size": ensemble_size,
            **kwargs
        }
        
        return await self._executor.run_lisflood_forecast(**parameters)
    
    async def run_real_time_forecast(
        self,
        current_date: str,
        forecast_days: int = 7,
        settings_file: str,
        real_time_data: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run real-time flood forecast for emergency management.
        
        Args:
            current_date: Current date for forecast initialization
            forecast_days: Number of days to forecast
            settings_file: Path to settings file
            real_time_data: Path to real-time meteorological data
            
        Returns:
            Real-time forecast results
        """
        return await self.run_flood_forecast(
            forecast_start=current_date,
            forecast_horizon=forecast_days,
            settings_file=settings_file,
            meteorological_forecast=real_time_data,
            ensemble_size=10,  # Use ensemble for uncertainty estimation
            **kwargs
        )
    
    # River Routing Methods
    async def analyze_river_routing(
        self,
        start_date: str,
        end_date: str,
        settings_file: str,
        discharge_points: List[Dict[str, Any]],
        routing_method: str = "kinematic",
        calibration_data: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze river routing and discharge at specific points.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            settings_file: Path to settings file
            discharge_points: List of discharge measurement points
            routing_method: Routing method ('kinematic', 'dynamic')
            calibration_data: Path to observed discharge data
            
        Returns:
            River routing analysis results
        """
        parameters = {
            "start_date": start_date,
            "end_date": end_date,
            "settings_file": settings_file,
            "discharge_points": discharge_points,
            "routing_method": routing_method,
            "calibration_data": calibration_data,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "lisflood_river_routing",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    # Scenario Analysis Methods
    async def run_land_use_scenario(
        self,
        scenario_name: str,
        start_date: str,
        end_date: str,
        settings_file: str,
        land_use_maps: Dict[str, str],
        compare_to_baseline: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run land use change scenario analysis.
        
        Args:
            scenario_name: Name of the scenario
            start_date: Scenario start date
            end_date: Scenario end date
            settings_file: Path to settings file
            land_use_maps: Dictionary of land use map file paths
            compare_to_baseline: Whether to compare with baseline scenario
            
        Returns:
            Scenario analysis results
        """
        parameters = {
            "scenario_name": scenario_name,
            "start_date": start_date,
            "end_date": end_date,
            "settings_file": settings_file,
            "land_use_maps": land_use_maps,
            "compare_to_baseline": compare_to_baseline,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "lisflood_land_use_scenario",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    async def run_climate_scenario(
        self,
        scenario_name: str,
        climate_data: str,
        baseline_period: List[str],
        future_period: List[str],
        settings_file: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run climate change scenario analysis.
        
        Args:
            scenario_name: Climate scenario name (e.g., 'RCP4.5', 'RCP8.5')
            climate_data: Path to climate scenario data
            baseline_period: [start, end] dates for baseline
            future_period: [start, end] dates for future scenario
            settings_file: Path to settings file
            
        Returns:
            Climate scenario analysis results
        """
        # Run baseline simulation
        baseline_result = await self.run_flood_simulation(
            start_date=baseline_period[0],
            end_date=baseline_period[1],
            settings_file=settings_file,
            output_dir=f"baseline_{scenario_name}",
            **kwargs
        )
        
        # Run future scenario simulation
        future_result = await self.run_flood_simulation(
            start_date=future_period[0],
            end_date=future_period[1],
            settings_file=settings_file,
            output_dir=f"future_{scenario_name}",
            **kwargs
        )
        
        return {
            "scenario_name": scenario_name,
            "climate_data": climate_data,
            "baseline_period": baseline_period,
            "future_period": future_period,
            "baseline_results": baseline_result,
            "future_results": future_result
        }
    
    # Calibration Methods
    async def calibrate_model(
        self,
        calibration_period: List[str],
        validation_period: List[str],
        parameters_to_calibrate: List[str],
        observed_data: str,
        settings_file: str,
        optimization_method: str = "nsga2",
        n_generations: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calibrate model parameters against observed data.
        
        Args:
            calibration_period: [start, end] dates for calibration
            validation_period: [start, end] dates for validation
            parameters_to_calibrate: List of parameter names to calibrate
            observed_data: Path to observed discharge/water level data
            settings_file: Path to settings file
            optimization_method: Optimization algorithm ('nsga2', 'pso', 'de')
            n_generations: Number of optimization generations
            
        Returns:
            Calibration results with optimized parameters
        """
        parameters = {
            "calibration_period": calibration_period,
            "validation_period": validation_period,
            "parameters_to_calibrate": parameters_to_calibrate,
            "observed_data": observed_data,
            "settings_file": settings_file,
            "optimization_method": optimization_method,
            "n_generations": n_generations,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "lisflood_calibration",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    # Utility Methods
    async def validate_settings_file(self, settings_file: str) -> Dict[str, Any]:
        """
        Validate Lisflood settings XML file.
        
        Args:
            settings_file: Path to settings file
            
        Returns:
            Validation results
        """
        # Basic XML validation
        try:
            from xml.etree import ElementTree as ET
            tree = ET.parse(settings_file)
            root = tree.getroot()
            
            # Extract key settings
            settings_info = {
                "valid": True,
                "file_path": settings_file,
                "root_element": root.tag,
                "options_count": len(root.findall(".//setoption")),
                "variables_count": len(root.findall(".//textvar")),
                "message": "Settings file validation successful"
            }
            
            return settings_info
            
        except Exception as e:
            return {
                "valid": False,
                "file_path": settings_file,
                "error": str(e),
                "message": "Settings file validation failed"
            }
    
    async def estimate_simulation_time(
        self,
        start_date: str,
        end_date: str,
        time_step: str = "daily",
        domain_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate simulation runtime based on parameters.
        
        Args:
            start_date: Simulation start date
            end_date: Simulation end date
            time_step: Time step resolution
            domain_size: Domain size description ('small', 'medium', 'large')
            
        Returns:
            Runtime estimation
        """
        from datetime import datetime
        
        # Calculate time span
        start = datetime.strptime(start_date.replace('-', '/'), '%Y/%m/%d')
        end = datetime.strptime(end_date.replace('-', '/'), '%Y/%m/%d')
        days = (end - start).days
        
        # Estimate based on time step and domain size
        base_time_per_day = {
            'hourly': 2.0,    # minutes per day
            '6hourly': 0.5,
            'daily': 0.1
        }.get(time_step, 0.1)
        
        domain_multiplier = {
            'small': 1.0,
            'medium': 3.0,
            'large': 10.0
        }.get(domain_size or 'medium', 3.0)
        
        estimated_minutes = days * base_time_per_day * domain_multiplier
        
        return {
            "simulation_days": days,
            "time_step": time_step,
            "domain_size": domain_size or "medium",
            "estimated_runtime_minutes": round(estimated_minutes, 1),
            "estimated_runtime_hours": round(estimated_minutes / 60, 2)
        }


# Convenience functions for direct usage
async def quick_flood_simulation(
    start_date: str,
    end_date: str,
    settings_file: str,
    output_dir: str = "./output",
    **kwargs
) -> Dict[str, Any]:
    """Quick flood simulation with default parameters."""
    async with LisfloodModel() as model:
        return await model.run_flood_simulation(
            start_date, end_date, settings_file, output_dir, **kwargs
        )


async def quick_flood_forecast(
    forecast_start: str,
    forecast_days: int,
    settings_file: str,
    meteo_forecast: str,
    **kwargs
) -> Dict[str, Any]:
    """Quick flood forecast with default parameters."""
    async with LisfloodModel() as model:
        return await model.run_flood_forecast(
            forecast_start=forecast_start,
            forecast_horizon=forecast_days,
            settings_file=settings_file,
            meteorological_forecast=meteo_forecast,
            **kwargs
        )


async def quick_water_balance(
    start_date: str,
    end_date: str,
    settings_file: str,
    **kwargs
) -> Dict[str, Any]:
    """Quick water balance analysis with default parameters."""
    async with LisfloodModel() as model:
        return await model.run_water_balance_analysis(
            start_date, end_date, settings_file, "./output", **kwargs
        )


# Example workflows
async def example_rhine_flood_simulation():
    """Example flood simulation for Rhine River basin."""
    async with LisfloodModel() as model:
        # Validate settings file
        validation = await model.validate_settings_file("settings/rhine_settings.xml")
        
        if not validation["valid"]:
            return {"error": "Invalid settings file", "details": validation}
        
        # Estimate runtime
        time_estimate = await model.estimate_simulation_time(
            start_date="2021-07-01",
            end_date="2021-07-31",
            time_step="daily",
            domain_size="large"
        )
        
        # Run simulation
        simulation = await model.run_flood_simulation(
            start_date="2021-07-01",
            end_date="2021-07-31",
            settings_file="settings/rhine_settings.xml",
            output_dir="./output/rhine_july2021",
            time_step="daily"
        )
        
        return {
            "validation": validation,
            "time_estimate": time_estimate,
            "simulation": simulation
        }


async def example_danube_forecast():
    """Example flood forecast for Danube River."""
    async with LisfloodModel() as model:
        # Run 7-day ensemble forecast
        forecast = await model.run_flood_forecast(
            forecast_start="2024-03-15",
            forecast_horizon=7,
            settings_file="settings/danube_settings.xml",
            meteorological_forecast="data/ecmwf_forecast.nc",
            ensemble_size=15
        )
        
        # Analyze river routing at key stations
        routing = await model.analyze_river_routing(
            start_date="2024-03-15",
            end_date="2024-03-22",
            settings_file="settings/danube_settings.xml",
            discharge_points=[
                {"name": "Vienna", "lat": 48.2082, "lon": 16.3738},
                {"name": "Budapest", "lat": 47.4979, "lon": 19.0402},
                {"name": "Belgrade", "lat": 44.7866, "lon": 20.4489}
            ]
        )
        
        return {
            "forecast": forecast,
            "routing_analysis": routing
        }


async def example_climate_impact_assessment():
    """Example climate change impact assessment."""
    async with LisfloodModel() as model:
        # Compare historical period with future projections
        climate_analysis = await model.run_climate_scenario(
            scenario_name="RCP8.5",
            climate_data="data/climate_projections_rcp85.nc",
            baseline_period=["1981-01-01", "2010-12-31"],
            future_period=["2071-01-01", "2100-12-31"],
            settings_file="settings/climate_settings.xml"
        )
        
        # Test land use change impact
        land_use_scenario = await model.run_land_use_scenario(
            scenario_name="increased_urbanization",
            start_date="2050-01-01",
            end_date="2050-12-31",
            settings_file="settings/climate_settings.xml",
            land_use_maps={
                "urban": "data/future_urban_2050.tif",
                "forest": "data/future_forest_2050.tif",
                "agriculture": "data/future_agriculture_2050.tif"
            }
        )
        
        return {
            "climate_scenario": climate_analysis,
            "land_use_scenario": land_use_scenario
        }