"""
Isaac Sim Tool

This module provides a tool for running robotics simulations in Isaac Sim,
designed to be compatible with autogen's function calling mechanism.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, Any, List, Optional, Union
from loguru import logger
import importlib.util

from roboco.core.tool import Tool
from roboco.core.config import load_config


class SimulationTool(Tool):
    """Tool for running and managing robotics simulations in Isaac Sim."""
    
    def __init__(self):
        """
        Initialize the simulation tool with Isaac Sim integration.
        """
        # Load configuration and check availability
        self.config = load_config()
        
        # Set default paths from config or use reasonable defaults
        sim_config = self.config.get("simulation", {})
        self.isaac_sim_path = sim_config.get("isaac_sim_path", "")
        self.default_simulation_output = sim_config.get("output_directory", "simulation_results")
        
        # Check if Isaac Sim is available
        self.isaac_sim_available = self._check_isaac_sim_available()
        
        # Define the run_simulation function
        def run_simulation(
            scenario: str, 
            parameters: Dict[str, Any] = None, 
            output_format: str = "json",
            max_duration: int = 300
        ) -> Dict[str, Any]:
            """
            Run a simulation scenario in Isaac Sim.
            
            Args:
                scenario: Name or path of the simulation scenario to run
                parameters: Dictionary of parameters to pass to the simulation
                output_format: Format for the simulation results (json, csv, etc.)
                max_duration: Maximum duration of the simulation in seconds
                
            Returns:
                Dictionary with simulation results
            """
            if not self.isaac_sim_available:
                return {
                    "success": False,
                    "error": "Isaac Sim is not available on the system",
                    "scenario": scenario
                }
            
            try:
                # Create a temporary file for simulation parameters
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as param_file:
                    params_path = param_file.name
                    json.dump(parameters or {}, param_file)
                
                # Create a temporary file for simulation results
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{output_format}', delete=False) as output_file:
                    output_path = output_file.name
                
                # Prepare the simulation script path
                # This assumes you have a simulation launcher script in your project
                launcher_script = os.path.join(os.path.dirname(__file__), '..', 'simulation', 'launcher.py')
                if not os.path.exists(launcher_script):
                    # Use a default template if launcher doesn't exist
                    launcher_script = self._create_default_launcher()
                
                # Prepare the command to run Isaac Sim headlessly with the simulation
                if os.path.exists(self.isaac_sim_path):
                    cmd = [
                        os.path.join(self.isaac_sim_path, "python.sh"),  # Isaac Sim Python executable
                        launcher_script,
                        "--scenario", scenario,
                        "--params", params_path,
                        "--output", output_path,
                        "--format", output_format,
                        "--max-duration", str(max_duration)
                    ]
                    
                    # Run the simulation process
                    logger.info(f"Running simulation: {scenario}")
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    stdout, stderr = process.communicate(timeout=max_duration + 30)  # Add buffer time
                    
                    # Read the simulation results
                    if os.path.exists(output_path):
                        if output_format == "json":
                            with open(output_path, 'r') as f:
                                results = json.load(f)
                        else:
                            with open(output_path, 'r') as f:
                                results = f.read()
                    else:
                        results = {"stdout": stdout, "stderr": stderr}
                    
                    # Clean up temporary files
                    try:
                        os.unlink(params_path)
                        os.unlink(output_path)
                    except:
                        pass
                    
                    return {
                        "success": process.returncode == 0,
                        "scenario": scenario,
                        "results": results,
                        "return_code": process.returncode
                    }
                else:
                    return {
                        "success": False,
                        "error": "Isaac Sim path not properly configured",
                        "scenario": scenario
                    }
            except Exception as e:
                logger.error(f"Error running simulation {scenario}: {str(e)}")
                return {
                    "success": False,
                    "scenario": scenario,
                    "error": str(e)
                }
        
        # Initialize the Tool parent class with the run_simulation function
        super().__init__(
            name="run_simulation",
            description="Run robotics simulations in Isaac Sim",
            func_or_tool=run_simulation
        )
        
        logger.info("Initialized SimulationTool for Isaac Sim integration")
    
    def _check_isaac_sim_available(self) -> bool:
        """
        Check if Isaac Sim is available on the system.
        
        Returns:
            bool: True if Isaac Sim is available, False otherwise
        """
        # Method 1: Check for Python module
        isaac_available = importlib.util.find_spec("omni.isaac.kit") is not None
        
        # Method 2: Check for environment variable
        if not isaac_available and "ISAAC_SIM_PATH" in os.environ:
            isaac_path = os.environ.get("ISAAC_SIM_PATH", "")
            isaac_available = os.path.exists(isaac_path)
            if isaac_available:
                self.isaac_sim_path = isaac_path
        
        if isaac_available:
            logger.info("Isaac Sim is available on the system")
        else:
            logger.warning("Isaac Sim is not available on the system")
        
        return isaac_available
