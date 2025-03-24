# Roboco Tool System

## Overview

The Roboco Tool System provides a flexible framework for creating tools that can be used by agents to interact with various systems and services. Tools are designed to be modular, reusable, and easily extensible, following Domain-Driven Design principles.

## Core Concepts

### Tool Class

The `Tool` class is the foundation of the tool system. It provides:

- A standardized interface for defining commands
- Automatic command registration via decorators
- Command execution with parameter validation
- Rich description generation for LLM consumption

### Commands

Commands are methods within a tool class that perform specific operations. Each command:

- Is explicitly marked with the `@command` decorator
- Has a well-defined signature with typed parameters
- Returns a standardized response format (typically a dictionary)
- Includes comprehensive documentation

### Primary Commands

Each tool can designate one command as the "primary" command, which is used when no specific command is specified. This is useful for tools that have a main operation.

## Creating Custom Tools

### Basic Tool Structure

```python
from roboco.core.tool import Tool, command

class MyCustomTool(Tool):
    """Description of your custom tool."""
    
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Description of what your tool does.",
            auto_discover=True  # Enable automatic command discovery
        )
    
    @command(primary=True)  # Mark as the primary command
    def main_operation(self, param1: str, param2: int = 0) -> dict:
        """
        Description of what this command does.
        
        Args:
            param1: Description of param1
            param2: Description of param2, with default value
            
        Returns:
            Dictionary with operation results
        """
        # Implementation
        return {
            "success": True,
            "result": "Operation completed",
            "data": {"param1": param1, "param2": param2}
        }
    
    @command()  # Mark as a regular command
    def secondary_operation(self, option: str) -> dict:
        """
        Description of what this command does.
        
        Args:
            option: Description of the option parameter
            
        Returns:
            Dictionary with operation results
        """
        # Implementation
        return {
            "success": True,
            "result": f"Processed option: {option}"
        }
```

### Using the Command Decorator

The `@command` decorator is used to explicitly mark methods that should be registered as commands:

```python
@command(primary=True)  # Mark as the primary command
def main_operation(self, param1: str, param2: int = 0) -> dict:
    # Implementation
    pass

@command()  # Mark as a regular command
def secondary_operation(self, option: str) -> dict:
    # Implementation
    pass
```

Benefits of using the decorator:
- Explicit marking of commands (vs. implicit discovery)
- Clear separation between public API and internal implementation
- Ability to designate a primary command
- Self-documenting code

### Command Execution

Commands can be executed using the `execute_command` method:

```python
# Execute a specific command
result = tool.execute_command(
    command="command_name",
    param1="value1",
    param2=123
)

# Execute the primary command
result = tool.execute_command(
    param1="value1",
    param2=123
)
```

### Error Handling

Tools should handle errors gracefully and return standardized error responses:

```python
@command()
def risky_operation(self, input_data: str) -> dict:
    try:
        # Potentially risky operation
        result = self._process_data(input_data)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## Best Practices

### 1. Command Design

- Keep commands focused on a single responsibility
- Use clear, descriptive names for commands
- Provide comprehensive docstrings with parameter descriptions
- Use type hints for all parameters and return values
- Return standardized response dictionaries with at least a "success" field

### 2. Tool Organization

- Group related commands in a single tool
- Use a clear naming convention for tools and commands
- Separate domain logic from infrastructure concerns
- Consider creating base classes for common tool patterns

### 3. Error Handling

- Handle exceptions within commands
- Return structured error information
- Log errors with appropriate context
- Provide clear error messages that help diagnose issues

### 4. Testing

- Write unit tests for each command
- Test both success and error paths
- Mock external dependencies
- Include integration tests for tools that interact with external systems

## Example: FileSystemTool

The `FileSystemTool` demonstrates best practices for tool implementation:

```python
from roboco.core.tool import Tool, command

class FileSystemTool(Tool):
    """Tool for file system operations."""
    
    def __init__(self):
        super().__init__(
            name="filesystem",
            description="Tool for file system operations.",
            auto_discover=True
        )
    
    @command(primary=True)
    def save_file(self, content: str, file_path: str, mode: str = "w") -> dict:
        """
        Save content to a file.
        
        Args:
            content: The content to save
            file_path: Where to save the file
            mode: File opening mode ('w' for write, 'a' for append)
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Implementation
            return {"success": True, "file_path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @command()
    def read_file(self, file_path: str) -> dict:
        """
        Read content from a file.
        
        Args:
            file_path: The path of the file to read
            
        Returns:
            Dictionary with file content
        """
        # Implementation
```

## Integration with Agents

Tools are designed to be used by agents in the Roboco system:

```python
from roboco.agents.base import Agent
from roboco.tools.fs import FileSystemTool

class MyAgent(Agent):
    def __init__(self):
        super().__init__()
        self.register_tool(FileSystemTool())
    
    async def process(self, message):
        # Agent can now use the FileSystemTool
        pass
```

## Advanced Topics

### Custom Type Definitions

For complex operations, define custom types using Pydantic models:

```python
from pydantic import BaseModel, Field
from typing import List

class ProjectFile(BaseModel):
    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content of the file")

class ProjectManifest(BaseModel):
    name: str = Field(..., description="Project name")
    directories: List[str] = Field(..., description="Directories to create")
    files: List[ProjectFile] = Field(..., description="Files to create")
```

Then use these types in your tool commands:

```python
@command()
def execute_project_manifest(self, manifest: ProjectManifest, base_path: str) -> dict:
    """
    Execute a project manifest to create a project structure.
    
    Args:
        manifest: Project manifest with directories and files
        base_path: Base path for the project
        
    Returns:
        Dictionary with operation results
    """
    # Implementation
```

### Tool Composition

Complex tools can be composed from simpler tools:

```python
class ProjectTool(Tool):
    def __init__(self):
        super().__init__(
            name="project",
            description="Tool for project operations.",
            auto_discover=True
        )
        self.fs_tool = FileSystemTool()
    
    @command()
    def create_project(self, manifest: ProjectManifest, path: str) -> dict:
        """Create a new project from a manifest."""
        # Use the FileSystemTool to implement this command
        return self.fs_tool.execute_project_manifest(manifest, path)
```

## Conclusion

The Roboco Tool System provides a flexible, extensible framework for creating tools that can be used by agents. By following the patterns and best practices outlined in this document, you can create powerful, reusable tools that integrate seamlessly with the Roboco ecosystem.
