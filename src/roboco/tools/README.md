# Roboco Tools

This directory contains the tool implementations for the Roboco system. Each tool is designed to provide specific capabilities that can be attached to agents.

## Available Tools

### BrowserTool

The BrowserTool provides web browsing capabilities that can be attached to any agent. It allows agents to browse websites and interact with web content using the browser-use package.

#### Features

- **URL Browsing**: Browse specific URLs to extract information
- **Web Interaction**: Interact with web content and extract information
- **Agent Integration**: Can be attached to any agent as a skill

#### Usage

```python
from roboco.tools import BrowserTool
from autogen import AssistantAgent

# Create the BrowserTool
browser_tool = BrowserTool()

# Create an agent
researcher = AssistantAgent(
    name="Researcher",
    system_message="You are a researcher with web browsing capabilities.",
    llm_config=llm_config
)

# Attach browser tool to the agent
browser_tool.attach_to_agent(researcher)

# Use the tool directly if needed
result = browser_tool.browse("Visit example.com and extract information about their latest product")
```

### FileSystemTool

The FileSystemTool provides file system operations that can be attached to agents.

### BashTool

The BashTool provides bash command execution capabilities that can be attached to agents.

### TerminalTool

The TerminalTool provides terminal command execution capabilities that can be attached to agents.

### RunTool

The RunTool provides code execution capabilities that can be attached to agents.

### SimulationTool

The SimulationTool provides simulation capabilities that can be attached to agents.

## Tool Integration

Tools are designed to be attached to agents to provide specific capabilities. This approach follows the principle that agents have roles (like researcher, analyst, etc.) and tools/skills enable them to perform specific tasks.

```python
# Example of attaching multiple tools to an agent
from roboco.tools import BrowserTool, FileSystemTool
from autogen import AssistantAgent

# Create tools
browser_tool = BrowserTool()
file_system_tool = FileSystemTool()

# Create an agent
researcher = AssistantAgent(
    name="Researcher",
    system_message="You are a researcher with web browsing and file system capabilities.",
    llm_config=llm_config
)

# Attach tools to the agent
browser_tool.attach_to_agent(researcher)
file_system_tool.attach_to_agent(researcher)
```
