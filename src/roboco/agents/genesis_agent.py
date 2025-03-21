"""
Genesis Agent for Roboco

This module provides a specialized agent that can interact with the Genesis MCP server
for physics simulations and robotics tasks.

Thanks to https://github.com/jtanningbed/mcp-ag2-example/blob/main/mcp_agent.py
"""

from typing import Dict, Optional, List, Any, Union
import asyncio
from loguru import logger

from roboco.core.mcp_agent import MCPAgent

class GenesisAgent(MCPAgent):
    """A specialized agent for interacting with Genesis physics simulation.
    
    This agent extends the MCPAgent with the ability to:
    - Run physics simulations through the Genesis MCP server
    - Create and manipulate simulation worlds
    - Add robots and objects to simulations
    - Execute simulation steps and collect results
    """
    
    def __init__(
        self,
        name: str,
        system_message: str,
        mcp_server_command: str = "genesis-mcp",
        mcp_server_args: Optional[List[str]] = None,
        transport_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Initialize the Genesis agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            mcp_server_command: Command to start the MCP server (legacy)
            mcp_server_args: Optional arguments for the MCP server (legacy)
            transport_config: Configuration for the MCP transport
            **kwargs: Additional arguments passed to Agent
        """
        # Add Genesis capabilities to system message
        genesis_info = (
            "\n\nYou have access to the Genesis physics simulation environment. "
            "You can create and run simulations, add robots and objects, and analyze results. "
            "Use the run_simulation, get_world_info, and get_basic_simulation methods to interact with Genesis."
        )
        
        enhanced_system_message = f"{system_message}{genesis_info}"
        
        # Default transport config for Genesis if not provided
        if transport_config is None:
            transport_config = {
                "type": "stdio",
                "command": mcp_server_command,
                "args": mcp_server_args or []
            }
        
        logger.debug(f"Initializing GenesisAgent '{name}' with transport configuration: {transport_config}")
        
        super().__init__(
            name=name, 
            system_message=enhanced_system_message, 
            transport_config=transport_config,
            **kwargs
        )
        
    def _register_mcp_tools(self):
        """Register Genesis tools for the LLM to use."""
        try:
            # Define tool functions and register them
            @self.register_tool(description="Run a Genesis physics simulation with the provided code")
            async def run_simulation(code: str, parameters: Optional[Dict] = None) -> Dict:
                """Run a Genesis simulation with the provided code and parameters.
                
                Args:
                    code: The Genesis simulation code to run
                    parameters: Optional parameters for the simulation
                    
                Returns:
                    Dict: The simulation results
                """
                logger.debug(f"Running Genesis simulation with {len(code)} characters of code")
                response = await self.send_command("run_simulation", {
                    "code": code,
                    "parameters": parameters or {}
                })
                return response
                
            @self.register_tool(description="Get information about the Genesis world")
            async def get_world_info() -> Dict:
                """Get information about the Genesis simulation world.
                
                Returns:
                    Dict: Information about the Genesis world
                """
                logger.debug("Getting Genesis world information")
                response = await self.send_command("get_world_info", {})
                return response
                
            @self.register_tool(description="Get a basic Genesis simulation template")
            async def get_basic_simulation() -> Dict:
                """Get a basic Genesis simulation template.
                
                Returns:
                    Dict: A template for a basic Genesis simulation
                """
                logger.debug("Getting basic Genesis simulation template")
                content, success = await self.get_resource("basic_simulation")
                if success and content:
                    return {
                        "success": True,
                        "message": "Retrieved basic simulation template",
                        "template": content
                    }
                else:
                    return {
                        "success": False,
                        "message": "Failed to retrieve basic simulation template",
                        "template": None
                    }
            
            logger.debug(f"Successfully registered Genesis tools for agent {self.name}")
        except Exception as e:
            logger.error(f"Error registering Genesis tools: {e}")
            raise