# Model Context Protocol (MCP) Integration

This document provides information about how Roboco integrates with the Model Context Protocol (MCP).

## What is MCP?

The Model Context Protocol is a standardized way for agents to interact with external context, tools, and resources.
It provides a server-client architecture for LLM applications to access external capabilities through a uniform interface.

## Using the McpAgent

The `McpAgent` class in Roboco provides a simple interface for connecting to and interacting with MCP servers.

### Basic Usage

```python
from roboco.core import McpAgent

# Create an MCP agent with a connection to a server
mcp_agent = McpAgent(
    name="mcp_assistant",
    system_message="You're an agent that can access external tools and context.",
    mcp_server_command="mcp-server",
    mcp_server_args=["--config", "mcp_config.json"]
)

# Connect to the server
await mcp_agent.connect_to_server()

# Send a command to the MCP server
response = await mcp_agent.send_command("get_context", {"query": "weather"})
print(response)

# Access a resource provided by the MCP server
content, success = await mcp_agent.get_resource("system_status")
if success:
    print(content)

# Close the connection when done
await mcp_agent.close()
```

### Using as a Context Manager

```python
async with McpAgent(
    name="mcp_assistant",
    system_message="You're an agent that can access external tools and context.",
    mcp_server_command="mcp-server"
) as agent:
    response = await agent.send_command("get_tool_list")
    print(f"Available tools: {response}")
```

## Genesis MCP Integration

Roboco includes a specialized `GenesisAgent` that connects to a Genesis MCP server.

```python
from roboco.agents import GenesisAgent

# Create a Genesis agent
genesis_agent = GenesisAgent(
    name="genesis_assistant",
    system_message="You're an agent that can control Genesis simulations.",
    mcp_server_command="genesis-mcp"
)

# Connect to the Genesis MCP server
await genesis_agent.connect_to_server()

# Run a simulation
await genesis_agent.send_command("run_simulation", {
    "code": "print('Hello from Genesis!')"
})

# Close the connection
await genesis_agent.close()
```

## Best Practices

- Always connect to the server before use with `await agent.connect_to_server()`
- Handle connection errors gracefully
- Close the connection when finished with `await agent.close()`
- Use the context manager interface when possible for automatic resource cleanup
