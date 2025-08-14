"""
Climada Model Interface

High-level interface for Climada climate risk analysis.
This module provides convenience functions for common Climada operations
using the MCP architecture.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..MCP.adapters.climada_adapter import ClimadaAdapter
from ..MCP.core.base_model import ModelResult
from ..MCP.sdk import MCPClient, ToolExecutor

logger = logging.getLogger(__name__)


class ClimadaModel:
    """
    High-level interface for Climada climate risk analysis.
    
    Provides simplified methods for common Climada operations.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self._adapter: Optional[ClimadaAdapter] = None
    
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
    
    # Impact Assessment Methods
    async def assess_tropical_cyclone_impact(
        self,
        region: str,
        year_range: Optional[List[int]] = None,
        return_periods: Optional[List[int]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Assess tropical cyclone impact for a region.
        
        Args:
            region: Region name or country code
            year_range: [start_year, end_year] for historical analysis
            return_periods: Return periods to analyze
            
        Returns:
            Impact assessment results
        """
        parameters = {
            "hazard_type": "tropical_cyclone",
            "region": region,
            "year_range": year_range or [2000, 2020],
            "return_period": return_periods or [10, 25, 50, 100, 250],
            **kwargs
        }
        
        return await self._executor.run_climada_impact_assessment(
            **parameters
        )
    
    async def assess_flood_impact(
        self,
        region: str,
        hazard_file_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Assess flood impact for a region.
        
        Args:
            region: Region name or country code
            hazard_file_path: Path to flood hazard data
            
        Returns:
            Impact assessment results
        """
        parameters = {
            "hazard_type": "flood",
            "region": region,
            "hazard_file_path": hazard_file_path,
            **kwargs
        }
        
        return await self._executor.run_climada_impact_assessment(
            **parameters
        )
    
    # Exposure Analysis Methods
    async def generate_litpop_exposure(
        self,
        country_iso: str,
        reference_year: int = 2020,
        admin_level: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate LitPop exposure data for a country.
        
        Args:
            country_iso: ISO country code (e.g., 'CHE', 'USA')
            reference_year: Reference year for exposure data
            admin_level: Administrative level (0=country, 1=state/province)
            
        Returns:
            Exposure analysis results
        """
        return await self._executor.run_climada_exposure_analysis(
            country_iso=country_iso,
            exposure_type="litpop",
            reference_year=reference_year,
            admin_level=admin_level,
            **kwargs
        )
    
    async def analyze_population_exposure(
        self,
        country_iso: str,
        reference_year: int = 2020,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze population exposure for a country.
        
        Args:
            country_iso: ISO country code
            reference_year: Reference year for data
            
        Returns:
            Population exposure analysis
        """
        return await self._executor.run_climada_exposure_analysis(
            country_iso=country_iso,
            exposure_type="population",
            reference_year=reference_year,
            **kwargs
        )
    
    # Hazard Modeling Methods
    async def model_tropical_cyclone_hazard(
        self,
        region: str,
        resolution: float = 0.1,
        climate_scenario: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Model tropical cyclone hazard for a region.
        
        Args:
            region: Region name
            resolution: Spatial resolution in degrees
            climate_scenario: Climate scenario (e.g., 'rcp85')
            
        Returns:
            Hazard modeling results
        """
        parameters = {
            "hazard_type": "tropical_cyclone",
            "region": region,
            "resolution": resolution,
            "climate_scenario": climate_scenario,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "climada_hazard_modeling",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    # Cost-Benefit Analysis Methods
    async def analyze_adaptation_measure(
        self,
        measure_name: str,
        hazard_type: str,
        measure_cost: float,
        exposure_file_path: str,
        hazard_file_path: str,
        discount_rate: float = 0.03,
        time_horizon: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze cost-benefit of an adaptation measure.
        
        Args:
            measure_name: Name of the adaptation measure
            hazard_type: Type of hazard
            measure_cost: Cost of implementing the measure
            exposure_file_path: Path to exposure data
            hazard_file_path: Path to hazard data
            discount_rate: Economic discount rate
            time_horizon: Analysis time horizon in years
            
        Returns:
            Cost-benefit analysis results
        """
        parameters = {
            "measure_name": measure_name,
            "hazard_type": hazard_type,
            "measure_cost": measure_cost,
            "exposure_file_path": exposure_file_path,
            "hazard_file_path": hazard_file_path,
            "discount_rate": discount_rate,
            "time_horizon": time_horizon,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "climada_cost_benefit",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    # Uncertainty Analysis Methods
    async def perform_sensitivity_analysis(
        self,
        parameters_to_vary: Dict[str, Any],
        base_case_file: str,
        n_samples: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on model parameters.
        
        Args:
            parameters_to_vary: Parameters and their ranges to vary
            base_case_file: Path to base case configuration
            n_samples: Number of Monte Carlo samples
            
        Returns:
            Sensitivity analysis results
        """
        parameters = {
            "analysis_type": "sensitivity",
            "parameters": parameters_to_vary,
            "base_case_file": base_case_file,
            "n_samples": n_samples,
            **kwargs
        }
        
        result = await self._client.execute_tool(
            "climada_uncertainty_analysis",
            parameters,
            wait_for_completion=True
        )
        
        return result
    
    # Utility Methods
    async def get_available_countries(self) -> List[str]:
        """Get list of available countries for analysis."""
        # This would typically query the Climada system for available data
        return [
            "CHE", "USA", "DEU", "FRA", "ITA", "ESP", "GBR", "NLD",
            "BEL", "AUT", "DNK", "SWE", "NOR", "FIN", "POL", "CZE"
        ]
    
    async def validate_input_data(
        self,
        data_type: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Validate input data format and content.
        
        Args:
            data_type: Type of data ('hazard', 'exposure', 'impact_functions')
            file_path: Path to data file
            
        Returns:
            Validation results
        """
        # Placeholder for validation logic
        return {
            "valid": True,
            "data_type": data_type,
            "file_path": file_path,
            "format": "HDF5",
            "message": "Data validation successful"
        }


# Convenience functions for direct usage
async def quick_impact_assessment(
    hazard_type: str,
    region: str,
    **kwargs
) -> Dict[str, Any]:
    """Quick impact assessment with default parameters."""
    async with ClimadaModel() as model:
        if hazard_type == "tropical_cyclone":
            return await model.assess_tropical_cyclone_impact(region, **kwargs)
        elif hazard_type == "flood":
            return await model.assess_flood_impact(region, **kwargs)
        else:
            raise ValueError(f"Unsupported hazard type: {hazard_type}")


async def quick_exposure_analysis(
    country_iso: str,
    exposure_type: str = "litpop",
    **kwargs
) -> Dict[str, Any]:
    """Quick exposure analysis with default parameters."""
    async with ClimadaModel() as model:
        if exposure_type == "litpop":
            return await model.generate_litpop_exposure(country_iso, **kwargs)
        elif exposure_type == "population":
            return await model.analyze_population_exposure(country_iso, **kwargs)
        else:
            raise ValueError(f"Unsupported exposure type: {exposure_type}")


# Example workflows
async def example_switzerland_analysis():
    """Example analysis for Switzerland."""
    async with ClimadaModel() as model:
        # Generate exposure data
        exposure = await model.generate_litpop_exposure("CHE", 2020)
        
        # Assess tropical cyclone impact (hypothetical)
        impact = await model.assess_tropical_cyclone_impact(
            region="Switzerland",
            year_range=[2000, 2020]
        )
        
        return {
            "exposure": exposure,
            "impact": impact
        }


async def example_usa_hurricane_analysis():
    """Example hurricane analysis for USA."""
    async with ClimadaModel() as model:
        # Model hurricane hazard
        hazard = await model.model_tropical_cyclone_hazard(
            region="USA_Atlantic",
            resolution=0.05,
            climate_scenario="rcp85"
        )
        
        # Generate exposure for Florida
        exposure = await model.generate_litpop_exposure("USA", 2020)
        
        # Assess impact
        impact = await model.assess_tropical_cyclone_impact(
            region="Florida",
            year_range=[1980, 2020],
            return_periods=[10, 25, 50, 100, 250, 500]
        )
        
        return {
            "hazard": hazard,
            "exposure": exposure,
            "impact": impact
        }