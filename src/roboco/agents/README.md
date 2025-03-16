# Roboco Agents

This directory contains the agent implementations for the Roboco system. Each agent is designed to fulfill a specific role in the research and report generation process.

## Available Agents

### ProductManager

The ProductManager agent is responsible for defining the research scope and delegating tasks to other agents. It outlines the key areas to investigate and the expected deliverables.

### Researcher

The Researcher agent specializes in analyzing data and extracting insights. It processes raw information, identifies patterns, and extracts actionable insights from various data sources.

### ReportWriter

The ReportWriter agent compiles findings into comprehensive reports. It structures information in a clear, concise format and provides recommendations based on the research.

### ToolUser

The ToolUser agent is responsible for executing tools and functions. It acts as a proxy for executing various tools, such as web searches and file operations.

## Agent Collaboration

The agents are designed to work together in a collaborative workflow:

1. **ProductManager** defines the research scope and delegates tasks
2. **Researcher** analyzes information and extracts insights
3. **ReportWriter** compiles the findings into a comprehensive report

This collaboration can be orchestrated using AG2's Swarm pattern or through direct agent interactions.

## Web Browsing Capabilities

Web browsing capabilities are provided through the `BrowserTool` in the tools package. This tool can be attached to any agent to provide web browsing and interaction capabilities.

### Usage

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

### Requirements

To use the BrowserTool, you need to install the following dependencies:

```bash
# Install AG2 with browser-use
pip install -U ag2[openai,browser-use]

# Install Playwright
playwright install
# For Linux only
playwright install-deps

# Install nest_asyncio for Jupyter notebooks
pip install nest_asyncio
```
