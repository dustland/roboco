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
            @self.register_for_llm(description="Run a Genesis physics simulation with the provided code")
            async def run_simulation(code: str, parameters: Optional[Dict] = None) -> Dict:
                """Run a Genesis simulation with the provided code and parameters.
                
                Args:
                    code: Python code for the simulation
                    parameters: Optional parameters for the simulation
                    
                Returns:
                    Dict: The simulation results
                """
                return await self.run_simulation(code, parameters)
            
            @self.register_for_llm(description="Get information about Genesis World features")
            async def get_world_info(name: str) -> str:
                """Get information about Genesis World features.
                
                Args:
                    name: Name of the information to retrieve (e.g., "overview", "capabilities")
                    
                Returns:
                    str: The requested information
                """
                return await self.get_world_info(name)
            
            @self.register_for_llm(description="Get a basic simulation template")
            async def get_basic_simulation(world_size: int = 10, agent_count: int = 2) -> str:
                """Get a basic simulation prompt.
                
                Args:
                    world_size: Size of the simulation world
                    agent_count: Number of agents to create
                    
                Returns:
                    str: The simulation prompt
                """
                return await self.get_basic_simulation(world_size, agent_count)
                
        except Exception as e:
            logger.error(f"Error registering Genesis tools: {e}")
    
    async def run_simulation(self, code: str, parameters: Optional[Dict] = None) -> Dict:
        """Run a Genesis simulation with the provided code and parameters.
        
        Args:
            code: Python code for the simulation
            parameters: Optional parameters for the simulation
            
        Returns:
            Dict: The simulation results
        """
        try:
            response = await self.send_command(
                "run_simulation", 
                {"code": code, "parameters": parameters or {}}
            )
            
            if response["success"]:
                return response["result"]
            else:
                return {
                    "success": False,
                    "message": response["message"],
                    "logs": [f"Error: {response['message']}"],
                    "results": {}
                }
        except Exception as e:
            logger.error(f"Error running Genesis simulation: {e}")
            return {
                "success": False,
                "message": f"Error running simulation: {str(e)}",
                "logs": [f"Error: {str(e)}"],
                "results": {}
            }
    
    async def get_world_info(self, name: str) -> str:
        """Get information about Genesis World features.
        
        Args:
            name: Name of the information to retrieve (e.g., "overview", "capabilities")
            
        Returns:
            str: The requested information
        """
        content, success = await self.get_resource(f"world_info://{name}")
        if success:
            return content
        else:
            return f"Error retrieving information: {name} not found"
    
    async def get_basic_simulation(self, world_size: int = 10, agent_count: int = 2) -> str:
        """Get a basic simulation prompt.
        
        Args:
            world_size: Size of the simulation world
            agent_count: Number of agents to create
            
        Returns:
            str: The simulation prompt
        """
        try:
            if not self.session:
                await self.initialize()
                
            logger.debug(f"Getting basic simulation template with world_size={world_size}, agent_count={agent_count}")
            result = await self.session.get_prompt(
                "basic_simulation",
                arguments={"world_size": world_size, "agent_count": agent_count}
            )
            return result.messages[0].content.text
        except Exception as e:
            logger.error(f"Error getting Genesis simulation template: {e}")
            return f"Error retrieving simulation template: {str(e)}"