"""
Genesis Agent for Roboco

This module provides a specialized agent that can interact with the Genesis MCP server
for physics simulations and robotics tasks.
"""

from typing import Dict, Optional, List, Any
import asyncio
from loguru import logger

from roboco.core.mcp_agent import McpAgent

class GenesisAgent(McpAgent):
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
        executor_agent: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize the Genesis agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            mcp_server_command: Command to start the MCP server
            mcp_server_args: Optional arguments for the MCP server
            executor_agent: Optional agent that will execute the tools (if None, self is used)
            **kwargs: Additional arguments passed to Agent
        """
        # Add Genesis capabilities to system message
        genesis_info = (
            "\n\nYou have access to the Genesis physics simulation environment. "
            "You can create and run simulations, add robots and objects, and analyze results. "
            "Use the run_simulation, get_world_info, and get_basic_simulation methods to interact with Genesis."
        )
        
        enhanced_system_message = f"{system_message}{genesis_info}"
        
        # Add a more descriptive message about connecting to Genesis
        logger.info(f"Initializing GenesisAgent '{name}' to connect to Genesis MCP server")
        logger.debug(f"Using command: {mcp_server_command} {' '.join(mcp_server_args or [])}")
        
        # Store the executor agent reference
        self.executor_agent = executor_agent
        
        super().__init__(
            name=name, 
            system_message=enhanced_system_message, 
            mcp_server_command=mcp_server_command,
            mcp_server_args=mcp_server_args,
            **kwargs
        )
        
    def _register_mcp_tools(self):
        """Register Genesis tools for the LLM to use."""
        try:
            # Determine the executor (self or provided executor_agent)
            executor = self.executor_agent if self.executor_agent is not None else self
            executor_name = executor.name if hasattr(executor, 'name') else 'unknown'
            
            logger.debug(f"Registering Genesis tools with executor: {executor_name}")
            
            # Define tool functions
            async def run_simulation(code: str, parameters: Optional[Dict] = None) -> Dict:
                """Run a Genesis simulation with the provided code and parameters."""
                if not self.session:
                    await self.initialize()
                    if not self.session:
                        return {"error": "Failed to connect to Genesis MCP server. Please make sure it's running."}
                        
                logger.info(f"Running Genesis simulation with {len(code)} characters of code")
                try:
                    response = await self.send_command("run_simulation", {
                        "code": code,
                        "parameters": parameters or {}
                    })
                    return response
                except Exception as e:
                    logger.error(f"Error running Genesis simulation: {e}")
                    return {"error": f"Error running simulation: {str(e)}"}

            async def get_world_info() -> Dict:
                """Get information about the current Genesis world state."""
                if not self.session:
                    await self.initialize()
                    if not self.session:
                        return {"error": "Failed to connect to Genesis MCP server. Please make sure it's running."}
                        
                logger.info("Requesting Genesis world information")
                try:
                    response = await self.send_command("get_world_info", {})
                    return response
                except Exception as e:
                    logger.error(f"Error getting Genesis world info: {e}")
                    return {"error": f"Error getting world info: {str(e)}"}
                
            async def get_basic_simulation() -> Dict:
                """Get a basic Genesis simulation template."""
                if not self.session:
                    await self.initialize()
                    if not self.session:
                        return {"error": "Failed to connect to Genesis MCP server. Please make sure it's running."}
                        
                logger.info("Requesting basic Genesis simulation template")
                try:
                    response = await self.send_command("get_basic_simulation", {})
                    return response
                except Exception as e:
                    logger.error(f"Error getting basic simulation: {e}")
                    return {"error": f"Error getting basic simulation: {str(e)}"}
            
            # Register the tools with the determined executor
            self.register_tool(run_simulation, executor, 
                description="Run a Genesis physics simulation with the provided code")
            self.register_tool(get_world_info, executor, 
                description="Get information about the Genesis world")
            self.register_tool(get_basic_simulation, executor, 
                description="Get a basic Genesis simulation template")
            
            logger.info(f"Genesis tools registered successfully with executor: {executor_name}")
        except Exception as e:
            logger.error(f"Error registering Genesis tools: {e}")
    
    def register_tools_with_executor(self, executor_agent):
        """Register Genesis tools to be executed by the specified agent.
        
        Args:
            executor_agent: The agent that will execute the tools
        """
        # Update the executor agent reference
        self.executor_agent = executor_agent
        
        # Re-register the tools with the new executor
        self._register_mcp_tools()
    