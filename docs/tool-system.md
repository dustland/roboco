# Roboco Tool System - Decorator-based AG2 Integration

The Roboco tool system provides a clean, decorator-based approach to tool development with automatic AG2 function generation and registration. This design eliminates code duplication while maintaining full compatibility with AG2's native function system.

## Architecture Overview

The tool system consists of three main components:

1. **`@tool` Decorator**: Marks methods as tool functions with metadata
2. **`Tool` Base Class**: Provides automatic discovery and AG2 integration
3. **`ToolRegistry`**: Manages tool instances and provides AG2 functions

## Core Components

### @tool Decorator

The `@tool` decorator marks methods as tool functions and provides metadata for AG2 integration:

```python
@tool(name="web_search", description="Search the web for information")
async def search(
    self,
    task_id: str,
    agent_id: str,
    query: Annotated[str, "Search query"],
    max_results: Annotated[int, "Max results"] = 10
) -> str:
    # Implementation
```

**Key Features:**

- Automatic function discovery via reflection
- Metadata preservation for AG2 type checking
- Clean separation of concerns

### Tool Base Class

The `Tool` base class provides automatic AG2 integration:

```python
class WebSearchTool(Tool):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    @tool(name="web_search", description="Search the web for information")
    async def search(
        self,
        task_id: str,
        agent_id: str,
        query: Annotated[str, "Search query"],
        max_results: Annotated[int, "Max results"] = 10
    ) -> str:
        # Search implementation
        results = await self._perform_search(query, max_results)
        return self._format_results(results)

    async def _perform_search(self, query: str, max_results: int):
        # Private helper method
        pass

    def _format_results(self, results):
        # Private helper method
        pass
```

**Key Methods:**

- `discover_tools()`: Automatically finds @tool decorated methods
- `create_ag2_functions()`: Generates AG2-compatible wrapper functions
- `_emit_tool_event()`: Override for custom monitoring

### ToolRegistry

The `ToolRegistry` manages tool instances and provides AG2 functions:

```python
# Create registry
registry = ToolRegistry()

# Register tool instances
registry.register_tool_instance("search_tools", WebSearchTool(api_key="..."))
registry.register_tool_instance("memory_tools", MemoryTool(memory_manager))

# Get AG2 functions for specific categories
functions = registry.get_tools_for_categories(["search_tools", "memory_tools"])

# Register with AG2 agents
for func_name, func in functions.items():
    register_function(func, caller=agent, executor=executor)
```

## Built-in Tools

### Memory Tools

Provides persistent memory capabilities:

```python
class MemoryTool(Tool):
    @tool(name="add_memory", description="Add content to persistent memory")
    async def add_memory(self, task_id: str, agent_id: str, content: str) -> str:
        # Store content with intelligent extraction

    @tool(name="search_memory", description="Search memories using semantic similarity")
    async def search_memory(self, task_id: str, agent_id: str, query: str, limit: int = 5) -> str:
        # Search and return relevant memories

    @tool(name="list_memories", description="List recent memories")
    async def list_memories(self, task_id: str, agent_id: str, limit: int = 10) -> str:
        # List recent memories from current session
```

### Basic Tools

File system and utility operations:

```python
class BasicTool(Tool):
    @tool(name="read_file", description="Read file contents")
    async def read_file(self, task_id: str, agent_id: str, path: str) -> str:
        # Read file safely within workspace

    @tool(name="write_file", description="Write content to file")
    async def write_file(self, task_id: str, agent_id: str, path: str, content: str) -> str:
        # Write file safely within workspace

    @tool(name="list_directory", description="List directory contents")
    async def list_directory(self, task_id: str, agent_id: str, path: str = ".") -> str:
        # List directory contents safely
```

### Search Tools

Web search and content extraction:

```python
class SearchTool(Tool):
    @tool(name="web_search", description="Search the web for information")
    async def web_search(self, task_id: str, agent_id: str, query: str, max_results: int = 10) -> str:
        # Perform web search using configured engines

    @tool(name="extract_url", description="Extract content from URL")
    async def extract_url(self, task_id: str, agent_id: str, url: str, max_length: int = 8000) -> str:
        # Extract clean content using Jina Reader API
```

## Security Features

### Access Control

Use the `@secure_tool` decorator for access control:

```python
@secure_tool(allowed_agents=["admin_agent"], security_level="admin")
@tool(name="delete_database", description="Delete database (admin only)")
async def delete_database(self, task_id: str, agent_id: str, database_name: str) -> str:
    # Admin-only operation
```

### Workspace Isolation

Built-in tools enforce workspace boundaries:

```python
def _resolve_path(self, path: str) -> Path:
    """Resolve path relative to workspace and validate security."""
    target_path = (self.workspace_path / path).resolve()

    # Security check: ensure path is within workspace
    try:
        target_path.relative_to(self.workspace_path)
    except ValueError:
        raise PermissionError(f"Access denied: Path '{path}' is outside workspace")

    return target_path
```

## Monitoring and Observability

### Automatic Event Emission

Tools automatically emit execution events:

```python
def _emit_tool_event(self, **event_data):
    """Override for custom monitoring."""
    # Log to your monitoring system
    logger.info(f"Tool executed: {event_data['tool_name']}", extra=event_data)

    # Send to metrics system
    metrics.increment(f"tool.{event_data['tool_name']}.executions")
    metrics.timing(f"tool.{event_data['tool_name']}.duration", event_data['execution_time'])
```

### Event Data Structure

```python
{
    'tool_name': 'web_search',
    'task_id': 'task_123',
    'agent_id': 'researcher',
    'parameters': {'query': 'AI research', 'max_results': 10},
    'result': 'Search results...',
    'execution_time': 1.23,
    'success': True,
    'error_message': None
}
```

## Integration with Team Manager

The team manager automatically registers tools based on configuration:

```yaml
# team.yaml
agents:
  - name: researcher
    role: ConversableAgent
    tools: ["search_tools", "memory_tools"]

  - name: writer
    role: ConversableAgent
    tools: ["basic_tools", "memory_tools"]

  - name: executor
    role: UserAgent # Executes tool functions and handles user interaction
```

The team manager handles:

- Tool instance creation and configuration
- AG2 function registration with proper caller/executor separation
- Security enforcement through UserAgent pattern

## Creating Custom Tools

### Simple Tool Example

```python
from roboco.tool.base import Tool, tool
from typing import Annotated

class WeatherTool(Tool):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    @tool(name="get_weather", description="Get current weather for a location")
    async def get_weather(
        self,
        task_id: str,
        agent_id: str,
        location: Annotated[str, "City name or coordinates"]
    ) -> str:
        # Weather API implementation
        weather_data = await self._fetch_weather(location)
        return f"Weather in {location}: {weather_data['description']}, {weather_data['temperature']}°C"

    async def _fetch_weather(self, location: str):
        # Private helper method
        pass
```

### Advanced Tool with Security

```python
from roboco.tool.base import Tool, tool, secure_tool
from typing import Annotated

class DatabaseTool(Tool):
    @tool(name="query_database", description="Query the database")
    async def query_database(
        self,
        task_id: str,
        agent_id: str,
        query: Annotated[str, "SQL query to execute"]
    ) -> str:
        # Safe database query
        pass

    @secure_tool(security_level="admin")
    @tool(name="backup_database", description="Create database backup")
    async def backup_database(
        self,
        task_id: str,
        agent_id: str,
        backup_name: Annotated[str, "Name for the backup"]
    ) -> str:
        # Admin-only backup operation
        pass
```

## Best Practices

### 1. Method Signatures

Always use this signature pattern:

```python
async def tool_method(
    self,
    task_id: str,      # Required: Task context
    agent_id: str,     # Required: Agent context
    param1: Annotated[Type, "Description"],  # Tool parameters
    param2: Annotated[Type, "Description"] = default_value
) -> str:  # Always return string for LLM consumption
```

### 2. Error Handling

Provide user-friendly error messages:

```python
@tool(name="example_tool", description="Example tool")
async def example_tool(self, task_id: str, agent_id: str, param: str) -> str:
    try:
        result = await self._do_work(param)
        return f"✅ Success: {result}"
    except ValueError as e:
        return f"❌ Invalid input: {str(e)}"
    except Exception as e:
        return f"❌ Operation failed: {str(e)}"
```

### 3. Result Formatting

Format results for LLM readability:

```python
def _format_search_results(self, results):
    if not results:
        return "🔍 No results found."

    formatted = [f"🔍 Found {len(results)} results:\n"]
    for i, result in enumerate(results, 1):
        formatted.append(f"{i}. **{result['title']}**")
        formatted.append(f"   {result['snippet']}")
        formatted.append(f"   🔗 {result['url']}\n")

    return "\n".join(formatted)
```

### 4. Configuration Management

Use configuration for flexibility:

```python
class CustomTool(Tool):
    def __init__(self, **config):
        super().__init__(**config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.example.com')
        self.timeout = config.get('timeout', 30)
```

## Migration from Legacy System

### Old Approach (Deprecated)

```python
# Old: Separate methods for AG2 integration
class OldTool:
    def search(self, query: str) -> str:
        # Implementation

    def create_ag2_function(self):
        # Separate AG2 wrapper creation
        def ag2_wrapper(query: str) -> str:
            return self.search(query)
        return ag2_wrapper
```

### New Approach

```python
# New: Single method with decorator
class NewTool(Tool):
    @tool(name="search", description="Search functionality")
    async def search(
        self,
        task_id: str,
        agent_id: str,
        query: Annotated[str, "Search query"]
    ) -> str:
        # Single implementation, automatic AG2 integration
```

## Performance Considerations

### Function Caching

The registry caches AG2 functions for performance:

```python
# Functions are cached after first discovery
registry.register_tool_instance("category", tool_instance)
# Subsequent calls use cached functions
functions = registry.get_tools_for_categories(["category"])
```

### Lazy Loading

Tools are only instantiated when needed:

```python
# Tool instances created on-demand
def create_tool_factory(config):
    def factory():
        return CustomTool(**config)
    return factory

registry.register_tool_factory("custom_tools", create_tool_factory(config))
```

## Conclusion

The decorator-based tool system provides:

- **Clean Architecture**: Single method per tool function
- **Automatic Integration**: AG2 functions generated automatically
- **Type Safety**: Full type annotation support
- **Security**: Built-in access control and workspace isolation
- **Monitoring**: Automatic event emission and observability
- **Flexibility**: Easy customization and extension

This design eliminates the complexity of the previous system while maintaining full compatibility with AG2's native function registration.
