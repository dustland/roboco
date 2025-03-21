# Roboco Examples

This directory contains example scripts demonstrating how to use the Roboco library.

## Tool System Examples

### `tools_example.py`

This example demonstrates how to use the enhanced Tool class and FileSystemTool with the new command-based approach:

1. Using FileSystemTool directly to perform file operations
2. Registering the FileSystemTool with an agent and having the agent use its commands

To run:

```bash
python examples/tools_example.py
```

### `custom_tool.py`

This example shows how to create a custom tool using the Tool base class:

1. Implementing a CalculatorTool with multiple mathematical operations
2. Using the tool directly to perform calculations
3. Registering the tool with an agent and having the agent use its commands

To run:

```bash
python examples/custom_tool.py
```

## Key Features Demonstrated

These examples showcase the following key features of the enhanced Tool system:

1. **Dynamic Command Registration**: Tools can register multiple commands and have them all available through a single entry point
2. **Command Execution**: The `execute_command` method provides a unified interface for executing tool commands
3. **Agent Integration**: Tools can register all their commands with agents automatically
4. **Error Handling**: Built-in error handling for command execution
5. **Primary Command**: Automatic selection of a primary command when none is specified

## Usage Tips

- When creating a new tool, inherit from `Tool` and implement your command functions as methods
- Use `register_commands` to register all the command functions with the tool
- Initialize the tool with `self.execute_command` as the entry point
- Use `register_with_agent` to register all commands with an agent

## Directory Structure

Each example is organized in its own directory with a consistent structure:

```
examples/
├── example_name/
│   ├── main.py         # Main entry point for the example
│   ├── README.md       # Documentation for the example
│   └── ...             # Additional files specific to the example
```

## Available Examples

### Tool Examples

The `tool/` directory contains various examples demonstrating how to use tools:

- FileSystem tool examples for file operations
- Web browsing with BrowserUseTool
- GitHub and ArXiv API tools
- And more...

```bash
# Run the file system example
python examples/tool/fs_example.py

# Run the web browsing example
python examples/tool/web_surf.py

# Run the GitHub API tool example
python examples/tool/github_example.py
```

### Team Chat

The `team_chat` directory contains an example of how to use the Roboco system to create a team of agents and initiate a chat with automatic handoffs between them.

```bash
# Run the team chat example
python examples/team_chat/main.py
```

### Market Research

The `market_research` directory contains examples of how to use the Roboco system for market research. It demonstrates how to use the various agents to generate comprehensive market research reports.

```bash
# Run market research with swarm orchestration
python examples/market_research/main.py --query "Your research query here"

# Run market research with direct research approach
python examples/market_research/main.py --query "Your research query here" --direct

# Run market research with browser capabilities
python examples/market_research/main.py --query "Your research query here" --direct --browser-type browser-use
```

## Requirements

Different examples may have different requirements. Please refer to the README.md file in each example directory for specific requirements.

### Browser Automation Dependencies

For examples that use browser capabilities:

```bash
# Install browser-use and playwright
uv pip install "ag2[browser-use]"
uv pip install playwright

# Install browser engines
playwright install

# Install system dependencies (Linux only)
playwright install-deps
```

## Standard Command Format

Most examples can be run using:

```bash
python examples/<example_name>/main.py [options]
```

For more detailed instructions, refer to the README.md file in each example directory.
