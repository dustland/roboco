"""
MCP Agent Module

This module provides a base agent class for interacting with MCP (Machine Control Protocol) servers.
It can be used as a foundation for specialized agents that need to communicate with various 
MCP-compatible services like Genesis, Simulacra, or other simulation/control systems.
"""

from typing import Dict, Optional, List, Any
import asyncio
import shlex
from loguru import logger

from roboco.core import Agent

# Check for MCP dependencies
try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    HAS_MCP = True
except ImportError:
    logger.warning("MCP package not installed. MCPAgent functionality will be limited.")
    HAS_MCP = False
    # Define empty classes for type checking
    class ClientSession:
        pass
    class StdioServerParameters:
        pass

class McpAgent(Agent):
    """Base agent class for interacting with MCP servers.
    
    This agent extends the standard Agent with the ability to:
    - Connect to MCP servers using stdio transport
    - Send commands and receive responses
    - Manage session lifecycle
    
    It can be subclassed to create specialized agents for specific MCP services.
    """
    
    def __init__(
        self,
        name: str,
        system_message: str,
        mcp_server_command: str = "mcp-server",
        mcp_server_args: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize the MCP agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            mcp_server_command: Command to start the MCP server (e.g., "mcp-server", "mcp dev server.py")
            mcp_server_args: Optional additional arguments for the MCP server
            **kwargs: Additional arguments passed to Agent
        """
        if not HAS_MCP:
            logger.warning("MCP package not installed. This agent will not be fully functional.")
        
        # Add MCP capabilities info to system message
        mcp_info = (
            "\n\nYou have access to an MCP (Machine Control Protocol) server. "
            "You can send commands to the server and receive responses. "
            "Use the available tools to interact with the MCP server."
        )
        
        enhanced_system_message = f"{system_message}{mcp_info}"
        
        # Initialize the Agent parent class with the enhanced system message
        super().__init__(name=name, system_message=enhanced_system_message, **kwargs)
        
        # Parse the server command into command and arguments
        # This handles cases like "mcp dev server.py" and splits it appropriately
        command_parts = shlex.split(mcp_server_command)
        self.mcp_base_command = command_parts[0]  # e.g., "mcp"
        self.mcp_command_args = command_parts[1:] # e.g., ["dev", "server.py"]
        
        # Add any additional arguments
        if mcp_server_args:
            self.mcp_command_args.extend(mcp_server_args)
        
        # Session management
        self._session_ctx = None
        self.session = None
        
        # Register common MCP tools
        self._register_mcp_tools()
        
    def _register_mcp_tools(self):
        """Register common MCP tools for the LLM to use.
        
        Subclasses should override this to register specific tools.
        """
        pass
            
    async def initialize(self) -> bool:
        """Initialize the connection to the MCP server.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not HAS_MCP:
            logger.error("MCP package is not installed. Cannot initialize connection.")
            return False
        
        try:
            # Create server parameters with the properly split command and args
            server_params = StdioServerParameters(
                command=self.mcp_base_command,
                args=self.mcp_command_args
            )
            
            full_command = f"{self.mcp_base_command} {' '.join(self.mcp_command_args)}"
            logger.debug(f"Connecting to MCP server with command: {full_command}")
            
            # Use the stdio_client as shown in the example
            self._session_ctx = stdio_client(server_params)
            read, write = await self._session_ctx.__aenter__()
            
            # Create and initialize the session
            self.session = ClientSession(read, write)
            await self.session.initialize()
            
            # Log available tools
            tools = self.session.list_tools()
            logger.info(f"Successfully connected to MCP server with {self.name} agent")
            logger.debug(f"Available MCP tools: {tools}")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            # Clean up resources if connection failed
            if self._session_ctx is not None:
                try:
                    await self._session_ctx.__aexit__(None, None, None)
                except Exception:
                    pass
            self._session_ctx = None
            self.session = None
            return False
            
    async def close(self):
        """Close the connection to the MCP server."""
        if self.session:
            try:
                await self.session.close()
                self.session = None
            except Exception as e:
                logger.error(f"Error closing MCP session: {e}")
                
        if self._session_ctx is not None:
            try:
                await self._session_ctx.__aexit__(None, None, None)
                self._session_ctx = None
                logger.debug(f"Closed connection to MCP server for {self.name} agent")
            except Exception as e:
                logger.error(f"Error closing MCP connection: {e}")
    
    async def send_command(self, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to the MCP server.
        
        Args:
            command: The command to send
            args: Optional arguments for the command
            
        Returns:
            Dict: The response from the server
        """
        if not HAS_MCP:
            return {
                "success": False,
                "message": "MCP package is not installed",
                "result": None
            }
            
        try:
            if not self.session:
                logger.debug(f"No active MCP session, attempting to initialize")
                success = await self.initialize()
                if not success:
                    return {
                        "success": False,
                        "message": "Failed to initialize MCP connection",
                        "result": None
                    }
                
            logger.debug(f"Sending MCP command: {command} with args: {args or {}}")
            result = await self.session.call_tool(command, inputs=args or {})
            return {
                "success": True,
                "message": "Command executed successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error sending MCP command '{command}': {e}")
            return {
                "success": False,
                "message": f"Error sending command: {str(e)}",
                "result": None
            }
    
    async def get_resource(self, resource_name: str) -> tuple[Optional[str], bool]:
        """Get a resource from the MCP server.
        
        Args:
            resource_name: The name of the resource to retrieve
            
        Returns:
            Tuple[Optional[str], bool]: The resource content and a success flag
        """
        if not HAS_MCP:
            logger.error("MCP package is not installed. Cannot get resource.")
            return None, False
            
        try:
            if not self.session:
                logger.debug(f"No active MCP session, attempting to initialize")
                success = await self.initialize()
                if not success:
                    return None, False
                
            logger.debug(f"Getting MCP resource: {resource_name}")
            content, _ = await self.session.read_resource(resource_name)
            return content, True
        except Exception as e:
            logger.error(f"Error getting MCP resource '{resource_name}': {e}")
            return None, False
        
    async def __aenter__(self):
        """Async context manager entry point."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close() 