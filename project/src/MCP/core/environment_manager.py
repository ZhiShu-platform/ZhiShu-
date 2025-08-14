"""
Environment Manager for MCP

Manages Conda environments for different models, handles environment
activation, validation, and isolation.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """
    Manages Conda environments for different models.
    
    Provides functionality to:
    - Detect available Conda environments
    - Validate environment requirements
    - Activate environments for model execution
    - Install missing dependencies
    """
    
    def __init__(self):
        self.conda_base_path = self._find_conda_base()
        self.environments: Dict[str, Dict[str, str]] = {}
        self._cache_environments()
    
    def _find_conda_base(self) -> Optional[Path]:
        """Find the Conda base installation path."""
        # Try common Conda locations
        conda_paths = [
            Path(os.environ.get("CONDA_PREFIX", "")),
            Path.home() / "anaconda3",
            Path.home() / "miniconda3", 
            Path("/opt/anaconda3"),
            Path("/opt/miniconda3"),
            Path("C:/ProgramData/Anaconda3"),
            Path("C:/Users") / os.environ.get("USERNAME", "") / "Anaconda3"
        ]
        
        for path in conda_paths:
            if path.exists() and (path / "bin" / "conda").exists() or (path / "Scripts" / "conda.exe").exists():
                logger.info(f"Found Conda installation at: {path}")
                return path
        
        # Try to find conda in PATH
        try:
            result = subprocess.run(
                ["conda", "info", "--base"],
                capture_output=True,
                text=True,
                check=True
            )
            base_path = Path(result.stdout.strip())
            if base_path.exists():
                logger.info(f"Found Conda base via conda info: {base_path}")
                return base_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        logger.warning("Could not find Conda installation")
        return None
    
    def _cache_environments(self):
        """Cache information about available Conda environments."""
        if not self.conda_base_path:
            return
        
        try:
            result = subprocess.run(
                ["conda", "env", "list", "--json"],
                capture_output=True,
                text=True,
                check=True
            )
            
            env_info = json.loads(result.stdout)
            for env_path in env_info["envs"]:
                env_path = Path(env_path)
                env_name = env_path.name
                
                self.environments[env_name] = {
                    "path": str(env_path),
                    "name": env_name,
                    "python_version": self._get_python_version(env_path)
                }
            
            logger.info(f"Found {len(self.environments)} Conda environments")
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to list Conda environments: {e}")
    
    def _get_python_version(self, env_path: Path) -> str:
        """Get Python version for a specific environment."""
        try:
            if os.name == "nt":  # Windows
                python_exe = env_path / "python.exe"
            else:
                python_exe = env_path / "bin" / "python"
            
            if python_exe.exists():
                result = subprocess.run(
                    [str(python_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1]
        except Exception:
            pass
        
        return "unknown"
    
    async def list_environments(self) -> List[Dict[str, str]]:
        """List all available Conda environments."""
        return list(self.environments.values())
    
    async def environment_exists(self, env_name: str) -> bool:
        """Check if a Conda environment exists."""
        return env_name in self.environments
    
    async def validate_environment(
        self, 
        env_name: str, 
        required_packages: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Validate that an environment exists and has required packages.
        
        Args:
            env_name: Name of the Conda environment
            required_packages: List of required package names
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "environment_exists": False,
            "packages_installed": False,
            "environment_accessible": False
        }
        
        # Check if environment exists
        if not await self.environment_exists(env_name):
            logger.warning(f"Environment '{env_name}' does not exist")
            return results
        
        results["environment_exists"] = True
        
        # Test environment accessibility
        try:
            await self._run_in_environment(
                env_name, 
                ["python", "--version"],
                timeout=30
            )
            results["environment_accessible"] = True
        except Exception as e:
            logger.error(f"Environment '{env_name}' is not accessible: {e}")
            return results
        
        # Check required packages if specified
        if required_packages:
            missing_packages = await self._check_packages(env_name, required_packages)
            results["packages_installed"] = len(missing_packages) == 0
            results["missing_packages"] = missing_packages
        else:
            results["packages_installed"] = True
        
        return results
    
    async def _check_packages(self, env_name: str, packages: List[str]) -> List[str]:
        """Check which packages are missing from an environment."""
        missing = []
        
        for package in packages:
            try:
                # Use conda list to check if package is installed
                result = await self._run_in_environment(
                    env_name,
                    ["conda", "list", package],
                    timeout=30
                )
                
                if package not in result.stdout.decode():
                    missing.append(package)
                    
            except Exception as e:
                logger.warning(f"Could not check package '{package}': {e}")
                missing.append(package)
        
        return missing
    
    async def _run_in_environment(
        self, 
        env_name: str, 
        command: List[str],
        timeout: int = 300,
        cwd: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a command in a specific Conda environment.
        
        Args:
            env_name: Name of the Conda environment
            command: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory
            
        Returns:
            CompletedProcess result
        """
        # Prepare conda run command
        conda_cmd = [
            "conda", "run", "-n", env_name,
            "--no-capture-output"
        ] + command
        
        logger.debug(f"Running in {env_name}: {' '.join(conda_cmd)}")
        
        # Execute command
        process = await asyncio.create_subprocess_exec(
            *conda_cmd,
            cwd=cwd,
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
        
        return subprocess.CompletedProcess(
            args=conda_cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
    
    async def create_environment(
        self,
        env_name: str,
        python_version: str = "3.9",
        packages: Optional[List[str]] = None
    ) -> bool:
        """
        Create a new Conda environment.
        
        Args:
            env_name: Name for the new environment
            python_version: Python version to install
            packages: Additional packages to install
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create base environment
            create_cmd = [
                "conda", "create", "-n", env_name,
                f"python={python_version}",
                "-y"
            ]
            
            if packages:
                create_cmd.extend(packages)
            
            logger.info(f"Creating Conda environment '{env_name}'")
            
            process = await asyncio.create_subprocess_exec(
                *create_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully created environment '{env_name}'")
                # Refresh environment cache
                self._cache_environments()
                return True
            else:
                logger.error(f"Failed to create environment '{env_name}': {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating environment '{env_name}': {e}")
            return False
    
    async def install_packages(
        self,
        env_name: str,
        packages: List[str],
        use_pip: bool = False
    ) -> bool:
        """
        Install packages in a Conda environment.
        
        Args:
            env_name: Name of the environment
            packages: List of packages to install
            use_pip: Whether to use pip instead of conda
            
        Returns:
            True if successful, False otherwise
        """
        if not await self.environment_exists(env_name):
            logger.error(f"Environment '{env_name}' does not exist")
            return False
        
        try:
            if use_pip:
                cmd = ["pip", "install"] + packages
            else:
                cmd = ["conda", "install", "-y"] + packages
            
            result = await self._run_in_environment(env_name, cmd, timeout=1800)
            
            if result.returncode == 0:
                logger.info(f"Successfully installed packages in '{env_name}': {packages}")
                return True
            else:
                logger.error(f"Failed to install packages: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing packages in '{env_name}': {e}")
            return False
    
    async def get_environment_info(self, env_name: str) -> Optional[Dict[str, str]]:
        """Get detailed information about an environment."""
        if env_name not in self.environments:
            return None
        
        env_info = self.environments[env_name].copy()
        
        # Add additional runtime information
        try:
            validation = await self.validate_environment(env_name)
            env_info.update(validation)
        except Exception as e:
            logger.warning(f"Could not get runtime info for '{env_name}': {e}")
        
        return env_info
    
    async def cleanup_temporary_files(self):
        """Clean up any temporary files created by the environment manager."""
        try:
            # Clean up conda cache
            await asyncio.create_subprocess_exec(
                "conda", "clean", "--all", "-y",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except Exception as e:
            logger.warning(f"Could not clean conda cache: {e}")


# Global environment manager instance
environment_manager = EnvironmentManager()