"""
MCP Agent Module

This module provides a base agent class for interacting with MCP (Machine Control Protocol) servers.
It can be used as a foundation for specialized agents that need to communicate with various 
MCP-compatible services like Genesis, Simulacra, or other simulation/control systems.
"""

from typing import Dict, Optional, List, Any, Union, Tuple
import asyncio
from abc import ABC, abstractmethod
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

class MCPTransport(ABC):
    """Abstract base class for MCP transport mechanisms."""
    
    @abstractmethod
    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to the MCP server and return the input/output streams."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass
        
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the MCP server."""
        pass
        
class StdioTransport(MCPTransport):
    """Transport for connecting to a local MCP server using stdio."""
    
    def __init__(self, command: str, args: Optional[List[str]] = None):
        """Initialize the stdio transport.
        
        Args:
            command: The command to start the MCP server
            args: Optional arguments to pass to the command
        """
        self.command = command
        self.args = args or []
        self._process = None
        self._reader = None
        self._writer = None
        
    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to the MCP server and return the reader/writer pair."""
        if not HAS_MCP:
            raise ImportError("MCP package not installed")
        self._process, self._reader, self._writer = await stdio_client(
            StdioServerParameters(cmd=self.command, args=self.args)
        )
        return self._reader, self._writer
        
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                self._process.kill()
        
    @property
    def is_connected(self) -> bool:
        """Check if connected to the MCP server."""
        return (
            self._process is not None and 
            self._process.returncode is None and
            self._writer is not None and 
            not self._writer.is_closing()
        )

class TransportFactory:
    """Factory for creating MCP transports."""
    
    @staticmethod
    def create_transport(config: Dict[str, Any]) -> MCPTransport:
        """Create a transport based on configuration.
        
        Args:
            config: Transport configuration dictionary
                - type: Transport type ('stdio', 'sse', etc.)
                - Other type-specific parameters
                
        Returns:
            An MCPTransport implementation
        """
        if not isinstance(config, dict):
            raise ValueError("Transport configuration must be a dictionary")
            
        transport_type = config.get('type', 'stdio')
        
        if transport_type == 'stdio':
            command = config.get('command', 'mcp-server')
            args = config.get('args', [])
            return StdioTransport(command, args)
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")

class MCPAgent(Agent):
    """Base agent class for interacting with MCP servers.
    
    This agent extends the standard Agent with the ability to:
    - Connect to MCP servers using various transport mechanisms
    - Send commands and receive responses
    - Manage session lifecycle
    
    It can be subclassed to create specialized agents for specific MCP services.
    """
    
    def __init__(
        self,
        name: str,
        system_message: str,
        transport_config: Optional[Dict[str, Any]] = None,
        mcp_server_command: Optional[str] = None,
        mcp_server_args: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize the MCP agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            transport_config: Configuration for the MCP transport
            mcp_server_command: Command to start the MCP server (legacy support)
            mcp_server_args: Optional arguments for the MCP server (legacy support)
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
        
        # Handle backward compatibility
        if transport_config is None and mcp_server_command is not None:
            transport_config = {
                "type": "stdio",
                "command": mcp_server_command,
                "args": mcp_server_args or []
            }
        elif transport_config is None:
            # Default configuration
            transport_config = {
                "type": "stdio",
                "command": "mcp-server",
                "args": []
            }
            
        # Create the transport
        try:
            self.transport = TransportFactory.create_transport(transport_config)
        except (ImportError, ValueError) as e:
            logger.error(f"Failed to create MCP transport: {e}")
            self.transport = None
            
        self.session = None
        self.read_stream = None
        self.write_stream = None
        
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
            
        if self.transport is None:
            logger.error("No valid transport configured. Cannot initialize connection.")
            return False
            
        try:
            logger.debug(f"Connecting to MCP server using transport: {type(self.transport).__name__}")
            
            # Connect using the transport
            self.read_stream, self.write_stream = await self.transport.connect()
            self.session = ClientSession(self.read_stream, self.write_stream)
            
            # Initialize the session
            await self.session.initialize()
            logger.info(f"Successfully connected to MCP server with {self.name} agent")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            return False
            
    async def close(self):
        """Close the connection to the MCP server."""
        if self.session:
            try:
                await self.session.close()
                self.session = None
                
                if self.transport and self.transport.is_connected:
                    await self.transport.disconnect()
                    
                self.read_stream = None
                self.write_stream = None
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
            if not self.session or not self.transport or not self.transport.is_connected:
                logger.debug(f"No active MCP session, attempting to initialize")
                success = await self.initialize()
                if not success:
                    return {
                        "success": False,
                        "message": "Failed to initialize MCP connection",
                        "result": None
                    }
                
            logger.debug(f"Sending MCP command: {command} with args: {args or {}}")
            result = await self.session.call_tool(command, args or {})
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
    
    async def get_resource(self, resource_name: str) -> Tuple[Optional[str], bool]:
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
            if not self.session or not self.transport or not self.transport.is_connected:
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