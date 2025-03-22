# Model Context Protocol (MCP) Integration

The Model Context Protocol (MCP) is a standardized way for LLMs to interact with tools, data, and contexts through a server-client architecture. This document provides an overview of how RoboCo integrates with MCP servers.

## Overview

The `McpAgent` class extends the base Agent class to provide a standardized way to connect to and interact with MCP servers. It includes:

- Built-in support for stdio-based MCP servers
- Methods for sending commands and retrieving resources
- Tool registration capabilities
- Session management and lifecycle handling

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io/introduction) is a server-client architecture that allows Large Language Models to access tools and context through a standardized interface. It enables:

- **Tool Usage**: LLMs can use tools defined by MCP servers
- **Context Access**: LLMs can access resources and context managed by servers
- **Standardized Interface**: A consistent way to interact with various services

## Using McpAgent

### Basic Usage

```python
from roboco.core import McpAgent
from roboco.core.agent import HumanProxy

# Create a human proxy as the executor
human_proxy = HumanProxy(
    name="User",
    system_message="You are a user who tests tools.",
    human_input_mode="ALWAYS"
)

# Create an MCP agent
mcp_agent = McpAgent(
    name="McpAssistant",
    system_message="You can use tools provided by an MCP server.",
    mcp_server_command="mcp dev server.py",  # Command to connect to the server
    executor_agent=human_proxy  # Set who executes the tools
)

# Initialize the connection
await mcp_agent.initialize()

# Let the human proxy initiate a conversation
await human_proxy.initiate_chat(
    recipient=mcp_agent,
    message="Can you help me use the tools?",
    max_turns=10
)
```

### Creating a Specialized MCP Agent

To create a specialized MCP agent, extend the base `McpAgent` class:

```python
from roboco.core import McpAgent

class MyMcpAgent(McpAgent):
    def __init__(self, name, system_message, **kwargs):
        # Add custom capabilities to system message
        enhanced_message = f"{system_message}\n\nYou can use special capabilities..."
        super().__init__(name=name, system_message=enhanced_message, **kwargs)

    def _register_mcp_tools(self):
        """Register custom tools for the LLM."""
        @self.register_for_llm(description="Run a custom command")
        async def run_custom_command(param1, param2):
            """Run a custom command with parameters.

            Args:
                param1: First parameter
                param2: Second parameter

            Returns:
                Result of the command
            """
            result = await self.send_command("custom_command", {
                "param1": param1,
                "param2": param2
            })
            return result
```

## Genesis Agent Example

The `GenesisAgent` is an example of a specialized MCP agent that interacts with the Genesis physics simulation environment:

```python
from roboco.agents import GenesisAgent
from roboco.core.agent import HumanProxy

# Create a human proxy agent
human_proxy = HumanProxy(
    name="User",
    system_message="You are a user interested in physics simulations.",
    human_input_mode="ALWAYS"
)

# Create the Genesis agent with the human proxy as the executor
genesis_agent = GenesisAgent(
    name="GenesisAssistant",
    system_message="You are a physics simulation expert.",
    mcp_server_command="genesis-mcp",
    executor_agent=human_proxy
)

# Initialize the connection
await genesis_agent.initialize()

# Let the human proxy initiate the chat
await human_proxy.initiate_chat(
    recipient=genesis_agent,
    message="Hello, I'd like to learn about physics simulations.",
    max_turns=10
)
```

## Setting Up an MCP Server

To use MCP with RoboCo:

1. Install the MCP package:

   ```bash
   pip install mcp
   ```

2. Create or obtain an MCP server implementation

3. Start the server:

   ```bash
   mcp dev server.py
   ```

4. Connect to it using RoboCo's `McpAgent` or one of its subclasses

## Best Practices

- Always initialize the connection before use with `await agent.initialize()`
- Close the connection when finished using `await agent.close()`
- Use Python's async context manager (`async with`) when appropriate
- Configure logging to capture and debug MCP interactions
- Register tools with a specific executor agent when needed
- Let the executor agent initiate conversations when using tool execution

## Additional Resources

For more information, see the [official MCP documentation](https://modelcontextprotocol.io/).
