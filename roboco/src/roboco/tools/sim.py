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
        super().__init__(name="sim", description="Run robotics simulations in Isaac Sim")
        
        self.config = load_config()
        self._check_isaac_sim_available()
        
        # Set default paths from config or use reasonable defaults
        sim_config = self.config.get("simulation", {})
        self.isaac_sim_path = sim_config.get("isaac_sim_path", "")
        self.default_simulation_output = sim_config.get("output_directory", "simulation_results")
        
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
        
        # Store the availability status
        self.isaac_sim_available = isaac_available
        if isaac_available:
            logger.info("Isaac Sim is available on the system")
        else:
            logger.warning("Isaac Sim is not available on the system")
        
        return isaac_available
    
    def is_available(self) -> Dict[str, Any]:
        """
        Check if Isaac Sim is available and ready to use.
        
        Returns:
            Dictionary with availability status
        """
        available = self._check_isaac_sim_available()
        return {
            "available": available,
            "isaac_sim_path": self.isaac_sim_path if available else None,
            "message": "Isaac Sim is available" if available else "Isaac Sim is not available on the system"
        }
    
    def run_simulation(self, 
                       scenario: str, 
                       parameters: Dict[str, Any] = None, 
                       output_format: str = "json",
                       max_duration: int = 300) -> Dict[str, Any]:
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
    
    def _create_default_launcher(self) -> str:
        """
        Create a default launcher script template if one doesn't exist.
        
        Returns:
            str: Path to the created launcher script
        """
        # Create simulation directory if it doesn't exist
        sim_dir = os.path.join(os.path.dirname(__file__), '..', 'simulation')
        os.makedirs(sim_dir, exist_ok=True)
        
        # Create a default launcher script
        launcher_path = os.path.join(sim_dir, 'launcher.py')
        
        if not os.path.exists(launcher_path):
            with open(launcher_path, 'w') as f:
                f.write("""
#!/usr/bin/env python
\"\"\"
Isaac Sim Simulation Launcher

This script launches Isaac Sim simulations based on provided parameters.
It is called by the SimulationTool to run simulations.
\"\"\"

import argparse
import json
import os
import sys
import time

# This will be imported when running with Isaac Sim python
try:
    import omni.kit
    import omni.isaac.core
    from omni.isaac.core import SimulationContext
    HAS_ISAAC = True
except ImportError:
    HAS_ISAAC = False
    print("Warning: omni.isaac modules not found. Running in test mode.")

def parse_args():
    parser = argparse.ArgumentParser(description="Run an Isaac Sim simulation")
    parser.add_argument("--scenario", type=str, required=True, help="Scenario name or path")
    parser.add_argument("--params", type=str, required=True, help="Path to JSON parameter file")
    parser.add_argument("--output", type=str, required=True, help="Path to output file")
    parser.add_argument("--format", type=str, default="json", help="Output format (json, csv)")
    parser.add_argument("--max-duration", type=int, default=300, help="Maximum simulation duration in seconds")
    return parser.parse_args()

def run_simulation(scenario, params_path, output_path, output_format, max_duration):
    if not HAS_ISAAC:
        # In test mode, just create a dummy result
        with open(output_path, 'w') as f:
            json.dump({
                "status": "test_mode",
                "message": "Running in test mode without Isaac Sim",
                "scenario": scenario,
                "parameters": json.load(open(params_path)) if os.path.exists(params_path) else {}
            }, f)
        return 0
    
    # Load simulation parameters
    with open(params_path, 'r') as f:
        parameters = json.load(f)
    
    try:
        # Initialize simulation
        simulation_context = SimulationContext(physics_dt=1.0/60.0, rendering_dt=1.0/60.0)
        
        # TODO: Load the specific scenario here based on the scenario name
        # This is a placeholder - you'll need to implement the actual scenario loading
        
        # Start the simulation
        simulation_context.play()
        
        # Run for specified duration
        start_time = time.time()
        while time.time() - start_time < max_duration:
            # TODO: Collect simulation data here
            simulation_context.step()
            
            # Example of collecting data (replace with actual data collection)
            if time.time() - start_time > max_duration - 1:
                break
        
        # Stop the simulation
        simulation_context.stop()
        
        # Save results based on output format
        results = {
            "status": "success",
            "scenario": scenario,
            "duration": time.time() - start_time,
            "parameters": parameters,
            # Add other simulation results here
            "data": {
                "joint_positions": [0.1, 0.2, 0.3],  # Placeholder data
                "end_effector_position": [1.0, 0.5, 0.8],  # Placeholder data
                "collision_detected": False  # Placeholder data
            }
        }
        
        if output_format == "json":
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
        elif output_format == "csv":
            # TODO: Implement CSV output if needed
            pass
        
        return 0
    except Exception as e:
        # Save error information
        with open(output_path, 'w') as f:
            json.dump({
                "status": "error",
                "message": str(e),
                "scenario": scenario,
                "parameters": parameters
            }, f)
        return 1

if __name__ == "__main__":
    args = parse_args()
    exit_code = run_simulation(
        args.scenario,
        args.params,
        args.output,
        args.format,
        args.max_duration
    )
    sys.exit(exit_code)
                """)
        
        return launcher_path
    
    def list_available_scenarios(self) -> Dict[str, Any]:
        """
        List all available simulation scenarios.
        
        Returns:
            Dictionary with list of available scenarios
        """
        if not self.isaac_sim_available:
            return {
                "success": False,
                "error": "Isaac Sim is not available on the system"
            }
        
        try:
            # This is a simplified implementation
            # In a real implementation, you would scan for available scenarios
            # in predefined directories or query Isaac Sim
            
            # Example directory where scenarios might be stored
            scenario_dir = os.path.join(os.path.dirname(__file__), '..', 'simulation', 'scenarios')
            
            scenarios = []
            if os.path.exists(scenario_dir) and os.path.isdir(scenario_dir):
                for item in os.listdir(scenario_dir):
                    if item.endswith(".py") or item.endswith(".usd"):
                        scenarios.append(item)
            
            # Add some default built-in scenarios as an example
            builtin_scenarios = [
                "pick_and_place",
                "robot_arm_trajectory",
                "humanoid_walking",
                "mobile_navigation"
            ]
            
            all_scenarios = scenarios + builtin_scenarios
            
            return {
                "success": True,
                "scenarios": all_scenarios,
                "count": len(all_scenarios)
            }
        except Exception as e:
            logger.error(f"Error listing simulation scenarios: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """
        Get results of a previously run simulation.
        
        Args:
            simulation_id: ID of the simulation to get results for
            
        Returns:
            Dictionary with simulation results
        """
        try:
            # Construct the path to the simulation results
            results_path = os.path.join(self.default_simulation_output, f"{simulation_id}.json")
            
            if not os.path.exists(results_path):
                return {
                    "success": False,
                    "simulation_id": simulation_id,
                    "error": f"Simulation results not found for ID: {simulation_id}"
                }
            
            # Read the simulation results
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            return {
                "success": True,
                "simulation_id": simulation_id,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error retrieving simulation results for {simulation_id}: {str(e)}")
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }
