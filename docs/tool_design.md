# Tool Design in Roboco

## Overview

This document outlines the standardized approach for implementing and using tools in the Roboco framework. Tools are a core component that enable agents to interact with external systems and perform specific tasks.

## Core Concepts

### ToolFactory

The `ToolFactory` is the primary way to create and manage tools. It abstracts away concrete tool implementations and provides a unified interface for tool creation and registration:

```python
from roboco.core.tool_factory import ToolFactory

# Create tools through the factory
browser_tool = ToolFactory.create_tool("BrowserTool")
fs_tool = ToolFactory.create_tool("FileSystemTool")

# Register tools with an agent
ToolFactory.register_tools_with_agent(
    agent=assistant,
    tool_names=["BrowserTool", "FileSystemTool"]
)
```

Key benefits of using the ToolFactory:

- Decouples tool usage from implementation details
- Centralizes tool configuration and instantiation
- Enables easy tool discovery and registration
- Facilitates testing through dependency injection
- Supports future extensibility without changing client code

### Tool Base Class

Tools in Roboco inherit from the `Tool` base class, which provides:

- Automatic function discovery through method introspection
- Documentation generation from method docstrings
- Standard interface for function execution
- Integration with autogen's function registration system

```python
from roboco.core import Tool

@ToolFactory.register("MyTool")  # Register with factory
class MyTool(Tool):
    """Example tool implementation."""

    async def my_function(self, param1: str, param2: int) -> dict:
        """
        Function description.

        Args:
            param1: Description of param1
            param2: Description of param2

        Returns:
            dict: Description of return value
        """
        # Implementation
        pass
```

### Tool Registration

Tools should always be created and registered using the ToolFactory. There are two main patterns:

1. Register tools with autogen agents:

```python
# Create and register tools
ToolFactory.register_tools_with_agent(
    agent=assistant,
    tool_names=["BrowserTool"]
)
```

2. Create tools for agent initialization:

```python
# Create tools for agent initialization
tools = [
    ToolFactory.create_tool("BrowserTool"),
    ToolFactory.create_tool("FileSystemTool")
]

agent = UserProxy(
    name="user",
    tools=tools,
    system_message="Use the available tools..."
)
```

## Implementation Guidelines

### 1. Method Signatures

- Use type hints for all parameters and return values
- Use descriptive parameter names
- Implement as async methods when involving I/O operations
- Return structured data (preferably Pydantic models)

```python
async def search(
    self,
    query: str,
    max_results: int = 5,
    domains: Optional[List[str]] = None
) -> SearchResults:
    """
    Search the web for information.

    Args:
        query: The search query
        max_results: Maximum number of results to return
        domains: Optional list of domains to restrict search to

    Returns:
        SearchResults: Pydantic model containing search results
    """
```

### 2. Error Handling

- Use custom exceptions for expected error cases
- Include error context in exception messages
- Log errors appropriately
- Return structured error responses

```python
class ToolError(Exception):
    """Base class for tool-related errors."""
    pass

class BrowserError(ToolError):
    """Raised when browser operations fail."""
    pass

async def browse(self, url: str) -> BrowseResult:
    try:
        # Implementation
    except Exception as e:
        raise BrowserError(f"Failed to browse {url}: {str(e)}")
```

### 3. Configuration

- Use Pydantic models for configuration
- Support both file-based and programmatic configuration
- Provide sensible defaults
- Validate configuration at initialization

```python
class ToolConfig(BaseModel):
    timeout: int = 30
    retry_count: int = 3
    cache_enabled: bool = True

class ConfigurableTool(Tool):
    def __init__(self, config: Optional[ToolConfig] = None):
        self.config = config or ToolConfig()
```

### 4. Testing

- Write unit tests for each method
- Mock external dependencies
- Test error cases
- Include integration tests for critical paths

```python
async def test_browser_search():
    tool = BrowserTool()
    results = await tool.search("test query")
    assert len(results.items) <= 5
    assert all(isinstance(item.url, str) for item in results.items)
```

## Example Tools

### BrowserTool

The BrowserTool provides web browsing and information extraction capabilities:

```python
class BrowserTool(Tool):
    """Tool for web browsing and information extraction."""

    async def browse(self, url: str) -> BrowseResult:
        """Browse a webpage and extract its content."""

    async def search(
        self,
        query: str,
        max_results: int = 5,
        domains: Optional[List[str]] = None
    ) -> SearchResults:
        """Search the web for information."""

    async def extract_text(
        self,
        url: str,
        selector: Optional[str] = None
    ) -> ExtractResult:
        """Extract text content from a webpage."""
```

### FileSystemTool

The FileSystemTool provides file system operations:

```python
class FileSystemTool(Tool):
    """Tool for file system operations."""

    async def read_file(self, path: str) -> str:
        """Read content from a file."""

    async def write_file(self, path: str, content: str) -> bool:
        """Write content to a file."""

    async def list_directory(self, path: str) -> List[str]:
        """List contents of a directory."""
```

## Usage in Examples

Here's how to use tools in a typical example:

```python
from roboco.agents import UserProxy, ProductManager, Researcher

async def main():
    # Create agents with tool names
    user = UserProxy(
        name="User",
        tool_names=["BrowserTool", "FileSystemTool"],
        system_message="Use the available tools..."
    )

    # Create specialized agents with their required tools
    assistant = ProductManager(
        name="PM",
        tool_names=["BrowserTool", "FileSystemTool"],
        system_message="Use the tools to research..."
    )

    # Example with custom tool configuration
    research_assistant = Researcher(
        name="Researcher",
        tool_names=["BrowserTool"],
        tool_configs={
            "BrowserTool": {
                "timeout": 60,
                "retry_count": 5
            }
        }
    )

    # Start the conversation
    await user.initiate_chat(
        [assistant],
        message="Research task description..."
    )
```

This example demonstrates:

1. Specifying tools by name when creating agents
2. Configuring tools using simple dictionaries
3. Letting the agent system handle tool creation and management

The agent system internally uses the `ToolFactory` to:

- Create and configure tools based on the provided names
- Register tools with the appropriate agents
- Handle tool lifecycle and dependencies

## Best Practices

1. **Documentation**

   - Provide clear docstrings for all methods
   - Include usage examples
   - Document error cases and handling

2. **Performance**

   - Implement caching where appropriate
   - Use async/await for I/O operations
   - Batch operations when possible

3. **Security**

   - Validate all inputs
   - Implement rate limiting
   - Handle sensitive data appropriately

4. **Maintainability**
   - Keep methods focused and single-purpose
   - Use consistent naming conventions
   - Follow SOLID principles

## Future Improvements

1. Tool discovery and auto-registration system
2. Enhanced error handling and recovery
3. Metrics and monitoring integration
4. Tool composition and pipelines
5. Enhanced caching and optimization
