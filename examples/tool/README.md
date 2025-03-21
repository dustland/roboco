# Tool System Examples

This directory contains examples demonstrating how to use the enhanced Tool system in Roboco.

## Available Examples

### File System Tool Examples

1. **fs_example.py** - Basic usage of the FileSystemTool

   - Demonstrates direct command execution
   - Shows how to create, read, and list files
   - Includes error handling examples

   Run with:

   ```bash
   python examples/tool/fs_example.py
   ```

2. **fs_with_agent.py** - Using the FileSystemTool with an agent

   - Shows how to register tool commands with an agent
   - Demonstrates having the agent create, read, and update files
   - Contains several file management tasks

   Run with:

   ```bash
   python examples/tool/fs_with_agent.py
   ```

### Auto-Discovery Examples

3. **auto_discover_example.py** - Demonstrates automatic function discovery

   - Shows how functions defined in `__init__` are automatically discovered and registered as commands
   - Implements a `UtilityTool` with date, math, and string helper functions
   - No manual command registration required

   Run with:

   ```bash
   python examples/tool/auto_discover_example.py
   ```

## Key Features Demonstrated

These examples showcase the following key features of the enhanced Tool system:

1. **Dynamic Command Registration** - Tools can register multiple commands that are all available through a single entry point
2. **Command Execution** - The `execute_command` method provides a unified interface for executing tool commands
3. **Agent Integration** - Tools can register all their commands with agents automatically
4. **Error Handling** - Built-in error handling for command execution with appropriate error messages
5. **Primary Command** - Automatic selection of a primary command when none is specified
6. **Auto-Discovery** - Automatic discovery and registration of functions defined in the tool's `__init__` method

## Implementation Patterns

### Manual Registration

```python
class MyTool(Tool):
    def __init__(self):
        # Define functions
        def function1():
            pass

        def function2():
            pass

        # Initialize the tool
        super().__init__(
            name="my_tool",
            description="My custom tool"
        )

        # Manually register commands
        self.register_commands({
            "function1": function1,
            "function2": function2
        })
```

### Auto-Discovery (Recommended)

```python
class MyTool(Tool):
    def __init__(self):
        # Define functions - they will be auto-discovered
        def function1():
            pass

        def function2():
            pass

        # Initialize the tool - functions are automatically discovered and registered
        super().__init__(
            name="my_tool",
            description="My custom tool"
        )
```

## Directory Structure

- **data/** - Created by fs_example.py, contains sample files
- **agent_data/** - Created by fs_with_agent.py, contains files created by an agent

## Testing

To verify that all tools work correctly, run the examples:

```bash
python examples/tool/fs_example.py
python examples/tool/fs_with_agent.py
python examples/tool/auto_discover_example.py
```
