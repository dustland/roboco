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

from roboco.core.agent import Agent

# Check for MCP dependencies
try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    HAS_MCP = True
except ImportError:
    logger.warning("MCP package not installed. MCPAgent will not be fully functional.")
    HAS_MCP = False
    # Create mock classes for type checking
    class ClientSession:
        pass
    class StdioServerParameters:
        pass

class MCPTransport(ABC):
    """Base interface for MCP server transport mechanisms."""

    @abstractmethod
    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Establish connection to the MCP server and return read/write streams."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the MCP server."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the transport is currently connected."""
        pass

class StdioTransport(MCPTransport):
    """Stdio-based transport for local MCP server."""

    def __init__(self, command: str, args: Optional[List[str]] = None):
        """Initialize the stdio transport.

        Args:
            command: Command to start the MCP server
            args: Optional arguments for the MCP server
        """
        if not HAS_MCP:
            raise ImportError("MCP package is required for StdioTransport")
            
        self.params = StdioServerParameters(command=command, args=args or [])
        self.read_stream = None
        self.write_stream = None

    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to the MCP server using stdio."""
        self.read_stream, self.write_stream = await stdio_client(self.params)
        return self.read_stream, self.write_stream

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.write_stream:
            self.write_stream.close()
            await self.write_stream.wait_closed()
        self.read_stream = None
        self.write_stream = None

    @property
    def is_connected(self) -> bool:
        """Return True if the transport is currently connected."""
        return self.read_stream is not None and self.write_stream is not None

class TransportFactory:
    """Factory for creating MCP transports."""

    @staticmethod
    def create_transport(config: Dict[str, Any]) -> MCPTransport:
        """Create a transport from the given configuration.

        Args:
            config: Transport configuration dictionary

        Returns:
            An instance of MCPTransport

        Raises:
            ValueError: If the transport type is unknown
            ImportError: If required dependencies are missing
        """
        if not HAS_MCP:
            raise ImportError("MCP package is required for creating MCP transports")
            
        transport_type = config.get("type", "stdio")

        if transport_type == "stdio":
            return StdioTransport(
                command=config.get("command", "mcp-server"),
                args=config.get("args", [])
            )
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

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
            logger.info(f"Successfully connected to MCP server")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            return False
            
    async def close(self):
        """Close the connection to the MCP server."""
        if self.session:
            try:
                self.session = None
                
                if self.transport:
                    await self.transport.disconnect()
                    
                self.read_stream = None
                self.write_stream = None
                logger.debug("Closed connection to MCP server")
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
        try:
            if not self.session:
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
            logger.error(f"Error sending MCP command: {e}")
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
        try:
            if not self.session:
                success = await self.initialize()
                if not success:
                    return None, False
                
            logger.debug(f"Getting MCP resource: {resource_name}")
            content, _ = await self.session.read_resource(resource_name)
            return content, True
        except Exception as e:
            logger.error(f"Error getting MCP resource: {e}")
            return None, False
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close() 