# GenesisAgent Remote Server Integration - Proof of Concept

## Objective

Create a minimal working proof of concept to validate that the GenesisAgent can connect to a remote MCP server using SSE transport before proceeding with the full implementation.

## Scope

The proof of concept will:

- Implement a minimal transport interface
- Create a basic SSE transport implementation
- Modify GenesisAgent to use the new transport
- Successfully connect to a remote MCP server
- Execute a simple simulation command

## Out of Scope

The proof of concept will NOT include:

- Full error handling
- Authentication
- Reconnection logic
- Backward compatibility layer
- Performance optimization

## Implementation Steps

### 1. Create Transport Interface

```python
# src/roboco/core/transport/base.py
from typing import Tuple, Optional, AsyncIterator
import asyncio
from abc import ABC, abstractmethod

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
```

### 2. Implement StdioTransport

```python
# src/roboco/core/transport/stdio.py
from typing import Tuple, Optional, List
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters

from .base import MCPTransport

class StdioTransport(MCPTransport):
    """Stdio-based transport for local MCP server."""

    def __init__(self, command: str, args: Optional[List[str]] = None):
        """Initialize the stdio transport.

        Args:
            command: Command to start the MCP server
            args: Optional arguments for the MCP server
        """
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
```

### 3. Implement SSETransport

```python
# src/roboco/core/transport/sse.py
from typing import Tuple, Optional, Dict, Any
import asyncio
import json
import uuid
import httpx
from httpx_sse import aconnect_sse

from .base import MCPTransport

class SSEStreamReader(asyncio.StreamReader):
    """Adapter to convert SSE events to StreamReader interface."""

    def __init__(self, sse_client):
        super().__init__()
        self.sse_client = sse_client
        self._buffer = bytearray()
        self._waiter = None
        self._sse_task = asyncio.create_task(self._read_sse())

    async def _read_sse(self):
        """Read events from SSE and put them in the buffer."""
        try:
            async for event in self.sse_client.aiter_sse():
                if event.event == "message":
                    data = event.data.encode() + b"\n"
                    self._buffer.extend(data)
                    if self._waiter:
                        waiter = self._waiter
                        self._waiter = None
                        waiter.set_result(None)
        except Exception as e:
            if self._waiter:
                self._waiter.set_exception(e)

    async def readline(self):
        """Read a line from the buffer."""
        if not self._buffer and not self.sse_client.is_closed:
            self._waiter = asyncio.Future()
            await self._waiter

        line = bytearray()
        idx = self._buffer.find(b"\n")
        if idx >= 0:
            line.extend(self._buffer[:idx+1])
            del self._buffer[:idx+1]
        return bytes(line)

    async def read(self, n=-1):
        """Read bytes from the buffer."""
        if not self._buffer and not self.sse_client.is_closed:
            self._waiter = asyncio.Future()
            await self._waiter

        if n == -1:
            data = bytes(self._buffer)
            self._buffer.clear()
        else:
            data = bytes(self._buffer[:n])
            del self._buffer[:n]
        return data

class SSEStreamWriter(asyncio.StreamWriter):
    """Adapter to convert StreamWriter interface to HTTP POST requests."""

    def __init__(self, url: str, session: httpx.AsyncClient):
        self.url = url
        self.session = session
        self.transport = None
        self._closed = False

    def write(self, data: bytes) -> None:
        """Queue data to be sent via HTTP POST."""
        asyncio.create_task(self._send_data(data))

    async def _send_data(self, data: bytes) -> None:
        """Send data via HTTP POST."""
        try:
            await self.session.post(
                self.url,
                content=data,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            print(f"Error sending data: {e}")

    def close(self) -> None:
        """Close the writer."""
        self._closed = True

    async def wait_closed(self) -> None:
        """Wait until the writer is closed."""
        if self.session:
            await self.session.aclose()

    @property
    def is_closing(self) -> bool:
        """Return True if the writer is closing."""
        return self._closed

class SSETransport(MCPTransport):
    """SSE-based transport for remote MCP server."""

    def __init__(self, server_url: str, client_id: Optional[str] = None):
        """Initialize the SSE transport.

        Args:
            server_url: URL of the MCP server
            client_id: Optional client ID for the connection
        """
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id or str(uuid.uuid4())
        self.sse_url = f"{self.server_url}/events/{self.client_id}"
        self.post_url = f"{self.server_url}/message/{self.client_id}"
        self.session = None
        self.sse_client = None
        self.read_stream = None
        self.write_stream = None

    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to the MCP server using SSE."""
        self.session = httpx.AsyncClient()

        # Connect to the SSE endpoint
        response = await self.session.get(self.sse_url, timeout=30.0)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to connect to SSE endpoint: {response.status_code}")

        # Create the SSE client
        self.sse_client = await aconnect_sse(self.session, "GET", self.sse_url)

        # Create the stream reader and writer
        self.read_stream = SSEStreamReader(self.sse_client)
        self.write_stream = SSEStreamWriter(self.post_url, self.session)

        return self.read_stream, self.write_stream

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.sse_client:
            await self.sse_client.aclose()
            self.sse_client = None

        if self.session:
            await self.session.aclose()
            self.session = None

        self.read_stream = None
        self.write_stream = None

    @property
    def is_connected(self) -> bool:
        """Return True if the transport is currently connected."""
        return self.sse_client is not None and not self.sse_client.is_closed
```

### 4. Create Transport Factory

```python
# src/roboco/core/transport/factory.py
from typing import Dict, Any, Optional
from .base import MCPTransport
from .stdio import StdioTransport
from .sse import SSETransport

class TransportFactory:
    """Factory for creating MCP transports."""

    @staticmethod
    def create_transport(config: Dict[str, Any]) -> MCPTransport:
        """Create a transport from the given configuration.

        Args:
            config: Transport configuration

        Returns:
            An instance of MCPTransport

        Raises:
            ValueError: If the transport type is unknown
        """
        transport_type = config.get("type", "stdio")

        if transport_type == "stdio":
            return StdioTransport(
                command=config.get("command", "genesis-mcp"),
                args=config.get("args")
            )
        elif transport_type == "sse":
            return SSETransport(
                server_url=config.get("server_url"),
                client_id=config.get("client_id")
            )
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")
```

### 5. Modify GenesisAgent

```python
# Modified version of GenesisAgent.__init__ and initialize
def __init__(
    self,
    name: str,
    system_message: str,
    transport_config: Optional[Dict[str, Any]] = None,
    mcp_server_command: str = "genesis-mcp",  # For backward compatibility
    mcp_server_args: Optional[List[str]] = None,  # For backward compatibility
    **kwargs,
):
    """Initialize the Genesis agent."""
    # ... existing code ...

    # Handle backward compatibility
    if transport_config is None:
        transport_config = {
            "type": "stdio",
            "command": mcp_server_command,
            "args": mcp_server_args or []
        }

    # Create the transport
    self.transport = TransportFactory.create_transport(transport_config)
    self.session = None
    self.read_stream = None
    self.write_stream = None

    # ... rest of existing code ...

async def initialize(self):
    """Initialize the connection to the Genesis MCP server."""
    try:
        logger.debug(f"Connecting to Genesis MCP server using transport: {type(self.transport).__name__}")

        # Connect using the transport
        self.read_stream, self.write_stream = await self.transport.connect()
        self.session = ClientSession(self.read_stream, self.write_stream)

        # Initialize the session
        await self.session.initialize()
        logger.info(f"Successfully connected to Genesis MCP server")
        return True
    except Exception as e:
        logger.error(f"Error connecting to Genesis MCP server: {e}")
        return False
```

## Testing Plan

1. Deploy a test MCP server with SSE support (or mock server for testing)
2. Create a simple test script to:
   - Instantiate GenesisAgent with SSE transport config
   - Connect to the remote server
   - Run a simple simulation
   - Verify results

## Success Criteria

- GenesisAgent successfully connects to a remote MCP server
- Basic simulation commands execute correctly
- Data flows bidirectionally between client and server
- Connection can be properly closed

## Next Steps After PoC

If the proof of concept is successful:

1. Implement full error handling and reconnection logic
2. Add authentication and security features
3. Create comprehensive test suite
4. Implement backward compatibility layer
5. Optimize performance
