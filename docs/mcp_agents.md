# MCP Agent System

The Multi-Channel Protocol (MCP) Agent is a base class for creating agents that can interact with external servers and processes using the MCP protocol. This document provides an overview of the MCPAgent functionality and how to use it.

## Overview

The MCPAgent extends the base Agent class to provide a standardized way to connect to and interact with MCP servers. It includes:

- A transport abstraction that supports different connection methods
- Built-in support for local stdio-based MCP servers
- Support for remote SSE-based MCP servers
- Methods for sending commands and retrieving resources

## Using MCPAgent

### Basic Usage

To use the MCPAgent, you typically extend it to create a specialized agent. For example:

```python
from roboco.core import MCPAgent

class MyMCPAgent(MCPAgent):
    def __init__(self, name, system_message, **kwargs):
        # Add custom capabilities to system message
        enhanced_message = f"{system_message}\n\nYou can use special capabilities..."

        super().__init__(name=name, system_message=enhanced_message, **kwargs)

    def _register_mcp_tools(self):
        """Register custom tools for the LLM."""
        @self.register_for_llm(description="Run a custom command")
        async def run_custom_command(param1, param2):
            result = await self.send_command("custom_command", {
                "param1": param1,
                "param2": param2
            })
            return result
```

### Transport Configuration

The MCPAgent supports different transport mechanisms:

#### Local MCP Server (stdio)

```python
transport_config = {
    "type": "stdio",
    "command": "mcp-server-command",
    "args": ["--option", "value"]
}

agent = MyMCPAgent(
    name="MCP Assistant",
    system_message="You are an assistant with MCP capabilities.",
    transport_config=transport_config
)
```

#### Remote MCP Server (SSE)

```python
transport_config = {
    "type": "sse",
    "url": "https://mcp-server.example.com/sse",
    "auth_token": "your-auth-token"  # Optional
}

agent = MyMCPAgent(
    name="MCP Assistant",
    system_message="You are an assistant with MCP capabilities.",
    transport_config=transport_config
)
```

## Creating Your Own MCP Agent

To create your own MCP-based agent:

1. Create a new class that extends MCPAgent
2. Override the `_register_mcp_tools` method to define custom tools
3. (Optional) Implement custom methods for specific MCP server interactions
4. Use `send_command()` to send commands to the MCP server
5. Use `get_resource()` to retrieve resources from the MCP server

## Example Implementations

### Genesis Agent

The GenesisAgent is an example of a specialized MCPAgent that interacts with the Genesis physics simulation environment:

```python
from roboco.agents import GenesisAgent

agent = GenesisAgent(
    name="GenesisAssistant",
    system_message="You are a physics simulation expert.",
    transport_config={
        "type": "stdio",
        "command": "genesis-mcp"
    }
)

# Run a simulation
result = await agent.run_simulation(simulation_code)
```

## Best Practices

- Always provide clear error handling for MCP server interactions
- Close the connection when finished using `await agent.close()`
- Use Python's async context manager (`async with`) when appropriate
- Configure logging to capture and debug MCP interactions
