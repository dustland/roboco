"""
Genesis Agent for Roboco

This module provides a specialized agent that can interact with the Genesis MCP server
for physics simulations and robotics tasks.

Thanks to https://github.com/jtanningbed/mcp-ag2-example/blob/main/mcp_agent.py
"""

from typing import Dict, Optional, List, Any, Union
import asyncio
from loguru import logger

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from roboco.core.agent import Agent


class GenesisAgent(Agent):
    """A specialized agent for interacting with Genesis physics simulation.
    
    This agent extends the standard Agent with the ability to:
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
        **kwargs,
    ):
        """Initialize the Genesis agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            mcp_server_command: Command to start the MCP server
            mcp_server_args: Optional arguments for the MCP server
            **kwargs: Additional arguments passed to Agent
        """
        # Add Genesis capabilities to system message
        genesis_info = (
            "\n\nYou have access to the Genesis physics simulation environment. "
            "You can create and run simulations, add robots and objects, and analyze results. "
            "Use the run_simulation, get_world_info, and get_basic_simulation methods to interact with Genesis."
        )
        
        enhanced_system_message = f"{system_message}{genesis_info}"
        
        super().__init__(name=name, system_message=enhanced_system_message, **kwargs)
        self.server_params = StdioServerParameters(
            command=mcp_server_command, 
            args=mcp_server_args or []
        )
        self.session = None
        self.read_stream = None
        self.write_stream = None
        
        # Register Genesis tools for the LLM
        self._register_genesis_tools()
        
    def _register_genesis_tools(self):
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
            
    async def initialize(self):
        """Initialize the connection to the Genesis MCP server."""
        try:
            logger.debug(f"Connecting to Genesis MCP server with command: {self.server_params.command}")
            
            # Properly handle the async context manager
            self.read_stream, self.write_stream = await stdio_client(self.server_params)
            self.session = ClientSession(self.read_stream, self.write_stream)
            
            # Initialize the session
            await self.session.initialize()
            logger.info(f"Successfully connected to Genesis MCP server")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Genesis MCP server: {e}")
            return False
            
    async def close(self):
        """Close the connection to the Genesis MCP server."""
        if self.session:
            try:
                self.session = None
                self.read_stream = None
                self.write_stream = None
                logger.debug("Closed connection to Genesis MCP server")
            except Exception as e:
                logger.error(f"Error closing Genesis MCP connection: {e}")
    
    async def run_simulation(self, code: str, parameters: Optional[Dict] = None) -> Dict:
        """Run a Genesis simulation with the provided code and parameters.
        
        Args:
            code: Python code for the simulation
            parameters: Optional parameters for the simulation
            
        Returns:
            Dict: The simulation results
        """
        try:
            if not self.session:
                await self.initialize()
                
            logger.debug(f"Running Genesis simulation with parameters: {parameters or {}}")
            result = await self.session.call_tool(
                "run_simulation", 
                {"code": code, "parameters": parameters or {}}
            )
            logger.debug(f"Simulation result: {result}")
            return result
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
        try:
            if not self.session:
                await self.initialize()
                
            logger.debug(f"Getting Genesis world info: {name}")
            content, _ = await self.session.read_resource(f"world_info://{name}")
            return content
        except Exception as e:
            logger.error(f"Error getting Genesis world info: {e}")
            return f"Error retrieving information: {str(e)}"
    
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
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()