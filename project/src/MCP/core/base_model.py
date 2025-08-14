"""
Base Model Classes for MCP

Defines the base interfaces and data structures that all model adapters
must implement.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model execution status."""
    IDLE = "idle"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModelResult:
    """Standardized result from model execution."""
    
    # Core fields
    model_name: str
    tool_name: str
    status: ModelStatus
    execution_id: str
    
    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    
    # Results
    data: Optional[Dict[str, Any]] = None
    files: Optional[List[str]] = None  # Output file paths
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    error: Optional[str] = None
    traceback: Optional[str] = None
    
    # Execution details
    environment: Optional[str] = None
    command: Optional[str] = None
    working_directory: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "model_name": self.model_name,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "data": self.data,
            "files": self.files,
            "metadata": self.metadata,
            "error": self.error,
            "traceback": self.traceback,
            "environment": self.environment,
            "command": self.command,
            "working_directory": self.working_directory
        }
    
    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class BaseModel(ABC):
    """
    Abstract base class for all model adapters.
    
    Each model adapter must implement this interface to be compatible
    with the MCP system.
    """
    
    def __init__(self, name: str, version: str = "latest"):
        self.name = name
        self.version = version
        self.status = ModelStatus.IDLE
        self.current_execution_id: Optional[str] = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup model-specific logging."""
        self.logger = logging.getLogger(f"mcp.{self.name}")
    
    @property
    @abstractmethod
    def model_path(self) -> Path:
        """Path to the model installation directory."""
        pass
    
    @property
    @abstractmethod
    def conda_environment(self) -> str:
        """Name of the Conda environment for this model."""
        pass
    
    @property
    @abstractmethod 
    def available_tools(self) -> List[str]:
        """List of available tools for this model."""
        pass
    
    @abstractmethod
    async def validate_environment(self) -> bool:
        """
        Validate that the model environment is properly set up.
        
        Returns:
            True if environment is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> ModelResult:
        """
        Execute a specific tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute  
            parameters: Parameters for the tool
            execution_id: Optional execution ID for tracking
            
        Returns:
            ModelResult with execution results
        """
        pass
    
    async def prepare_execution_environment(self, execution_id: str) -> Path:
        """
        Prepare a clean execution environment for a model run.
        
        Args:
            execution_id: Unique execution identifier
            
        Returns:
            Path to the execution directory
        """
        # Create temporary directory for this execution
        temp_dir = Path(tempfile.mkdtemp(prefix=f"{self.name}_{execution_id}_"))
        self.logger.info(f"Created execution directory: {temp_dir}")
        return temp_dir
    
    async def cleanup_execution_environment(self, execution_dir: Path):
        """
        Clean up execution environment after model run.
        
        Args:
            execution_dir: Path to the execution directory
        """
        try:
            import shutil
            shutil.rmtree(execution_dir)
            self.logger.info(f"Cleaned up execution directory: {execution_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup {execution_dir}: {e}")
    
    async def run_conda_command(
        self, 
        command: List[str], 
        working_dir: Optional[Path] = None,
        timeout: int = 3600
    ) -> subprocess.CompletedProcess:
        """
        Run a command in the model's Conda environment.
        
        Args:
            command: Command to execute
            working_dir: Working directory for execution
            timeout: Timeout in seconds
            
        Returns:
            CompletedProcess result
        """
        # Prepare command with conda activation
        conda_cmd = [
            "conda", "run", "-n", self.conda_environment,
            "--no-capture-output"
        ] + command
        
        self.logger.info(f"Executing: {' '.join(conda_cmd)}")
        
        # Execute command
        process = await asyncio.create_subprocess_exec(
            *conda_cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds")
        
        result = subprocess.CompletedProcess(
            args=conda_cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        if result.returncode != 0:
            self.logger.error(f"Command failed with code {result.returncode}")
            self.logger.error(f"STDERR: {result.stderr.decode()}")
        
        return result
    
    def create_result(
        self,
        tool_name: str,
        execution_id: str,
        status: ModelStatus = ModelStatus.COMPLETED,
        **kwargs
    ) -> ModelResult:
        """
        Create a standardized ModelResult.
        
        Args:
            tool_name: Name of the executed tool
            execution_id: Execution identifier
            status: Execution status
            **kwargs: Additional result data
            
        Returns:
            ModelResult instance
        """
        return ModelResult(
            model_name=self.name,
            tool_name=tool_name,
            status=status,
            execution_id=execution_id,
            start_time=datetime.now(),
            environment=self.conda_environment,
            **kwargs
        )
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, version={self.version})"
    
    def __repr__(self) -> str:
        return self.__str__()