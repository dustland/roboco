"""
Tool component for function calling and code execution.
"""

import asyncio
import inspect
import time
from typing import Dict, List, Optional, Any, Callable, get_type_hints
from dataclasses import dataclass

from pydantic import BaseModel, Field, create_model

from ..utils.logger import get_logger
from ..utils.id import generate_short_id

logger = get_logger(__name__)


class ToolCall(BaseModel):
    """Tool call specification with retry policy."""
    id: str = Field(default_factory=lambda: f"tc_{generate_short_id()}")
    tool_name: str
    args: Dict[str, Any]
    expected_output_type: Optional[str] = None
    timeout: Optional[int] = None
    retry_policy: Optional[Dict[str, Any]] = None


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def tool(description: str = "", return_description: str = ""):
    """
    Decorator to mark methods as available tool calls.
    
    Args:
        description: Clear description of what this tool does
        return_description: Description of what the tool returns
    """
    def decorator(func):
        func._is_tool_call = True
        func._tool_description = description or func.__doc__ or ""
        func._return_description = return_description
        return func
    return decorator


def _create_pydantic_model_from_signature(func: Callable) -> Optional[BaseModel]:
    """Create a Pydantic model from function signature for validation and schema generation."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    docstring = func.__doc__ or ""
    
    # Extract parameter descriptions from docstring
    param_descriptions = _extract_all_param_descriptions(docstring)
    
    fields = {}
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'kwargs']:
            continue
        
        param_type = type_hints.get(param_name, str)
        param_desc = param_descriptions.get(param_name, f"Parameter {param_name}")
        
        if param.default != inspect.Parameter.empty:
            # Optional parameter with default
            fields[param_name] = (param_type, Field(default=param.default, description=param_desc))
        else:
            # Required parameter
            fields[param_name] = (param_type, Field(description=param_desc))
    
    if not fields:
        return None
    
    # Create dynamic Pydantic model
    model_name = f"{func.__name__.title()}Params"
    return create_model(model_name, **fields)


def _extract_all_param_descriptions(docstring: str) -> Dict[str, str]:
    """Extract all parameter descriptions from docstring."""
    descriptions = {}
    if not docstring:
        return descriptions
    
    lines = docstring.split('\n')
    in_args_section = False
    
    for line in lines:
        line = line.strip()
        if line.lower().startswith('args:') or line.lower().startswith('parameters:'):
            in_args_section = True
            continue
        elif line.lower().startswith('returns:') or line.lower().startswith('return:'):
            in_args_section = False
            continue
        elif in_args_section and ':' in line:
            # Handle both "param: description" and "param (type): description"
            colon_idx = line.find(':')
            param_part = line[:colon_idx].strip()
            desc_part = line[colon_idx + 1:].strip()
            
            # Extract parameter name (remove type annotation if present)
            if '(' in param_part and ')' in param_part:
                param_name = param_part.split('(')[0].strip()
            else:
                param_name = param_part
            
            descriptions[param_name] = desc_part
    
    return descriptions


class Tool:
    """Base class for tools that provide multiple callable methods for LLMs."""
    
    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__.lower().replace('tool', '')
    
    def get_callable_methods(self) -> Dict[str, Callable]:
        """Get all methods marked with @tool decorator."""
        methods = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_is_tool_call'):
                tool_name = attr_name
                methods[tool_name] = attr
        return methods
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed OpenAI function schemas for all callable methods using Pydantic."""
        schemas = {}
        methods = self.get_callable_methods()
        
        for tool_name, method in methods.items():
            # Use Pydantic for schema generation
            pydantic_model = _create_pydantic_model_from_signature(method)
            if pydantic_model:
                # Get Pydantic's JSON schema
                pydantic_schema = pydantic_model.model_json_schema()
                
                # Convert to OpenAI function calling format
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": method._tool_description,
                        "parameters": pydantic_schema
                    }
                }
                
                # Add return information if available
                if hasattr(method, '_return_description') and method._return_description:
                    schema["function"]["returns"] = {
                        "description": method._return_description
                    }
                
                schemas[tool_name] = schema
            else:
                # Methods with no parameters
                schemas[tool_name] = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": method._tool_description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
        
        return schemas

class ToolRegistry:
    """
    Global tool registry that manages all available tools and creates schemas.
    
    This is a singleton that holds all registered tools and provides
    schema generation for any subset of tool names.
    """
    
    _instance = None
    _tools: Dict[str, tuple[Tool, Callable, Optional[BaseModel]]]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            # Initialize state here to ensure it's done only once.
            cls._instance._tools = {}
        return cls._instance

    def clear(self):
        """Clears all registered tools. Primarily for testing."""
        self._tools = {}

    def register_tool(self, tool: Tool):
        """Register a tool and all its callable methods."""
        methods = tool.get_callable_methods()
        schemas = tool.get_tool_schemas()
        
        for tool_name, method in methods.items():
            if tool_name in self._tools:
                logger.warning(f"Tool '{tool_name}' is already registered. Overwriting.")
            
            # Create a Pydantic model for the method's arguments for validation
            pydantic_model = _create_pydantic_model_from_signature(method)
            self._tools[tool_name] = (tool, method, pydantic_model)
            logger.debug(f"Registered tool method: {tool_name}")

    def get_tool_schemas(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Get detailed OpenAI function schemas for specified tools."""
        schemas = []
        for name in tool_names:
            if name in self._tools:
                tool_instance, method, _ = self._tools[name]
                # We need to get the schema for the specific method.
                # The Tool class get_tool_schemas returns a dict for all its methods.
                all_schemas = tool_instance.get_tool_schemas()
                if name in all_schemas:
                    schemas.append(all_schemas[name])
        return schemas
    
    def get_tool(self, name: str) -> Optional[tuple[Tool, Callable, Optional[BaseModel]]]:
        """Get a tool, method, and pydantic model by name (for executor use)."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def execute_tool_sync(self, name: str, **kwargs) -> ToolResult:
        """Synchronous wrapper for executing a tool. For use in non-async contexts."""
        try:
            # For environments where the top-level is sync, run async func
            return asyncio.run(self.execute_tool(name, **kwargs))
        except RuntimeError as e:
            # If an event loop is already running, try to use it
            if "cannot run loop while another loop is running" in str(e):
                loop = asyncio.get_running_loop()
                future = self.execute_tool(name, **kwargs)
                return loop.run_until_complete(future)
            raise e

    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with automatic parameter validation."""
        start_time = time.time()
        tool_info = self._tools.get(name)
        if not tool_info:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{name}' not found"
            )
        
        tool_instance, method, pydantic_model = tool_info
        
        # Validate parameters using Pydantic
        if pydantic_model:
            try:
                validated_params = pydantic_model(**kwargs)
                # Convert Pydantic model to dict for method call
                kwargs = validated_params.model_dump()
            except Exception as e:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Parameter validation failed: {str(e)}"
                )
        
        return await method(**kwargs)


# Global tool registry using the singleton pattern
_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return _tool_registry


def register_tool(tool: Tool):
    """Register a tool with the global registry."""
    get_tool_registry().register_tool(tool)


def get_tool_schemas(tool_names: List[str]) -> List[Dict[str, Any]]:
    """Get tool schemas from the global registry."""
    return get_tool_registry().get_tool_schemas(tool_names)


def get_tool(name: str) -> Optional[tuple[Tool, Callable, Optional[BaseModel]]]:
    """Get a tool from the global registry."""
    return get_tool_registry().get_tool(name)


def list_tools() -> List[str]:
    """List all registered tool names."""
    return get_tool_registry().list_tools()


async def execute_tool(name: str, **kwargs) -> ToolResult:
    """Execute a tool from the global registry."""
    return await get_tool_registry().execute_tool(name, **kwargs)


def print_available_tools():
    """Prints a formatted table of all available tools."""
    registry = get_tool_registry()
    tool_list = registry.list_tools()
    
    if not tool_list:
        print("No tools are registered.")
        return
        
    print(f"{'Tool Name':<30} {'Description':<70}")
    print("-" * 100)
    
    for tool_name in sorted(tool_list):
        _, method, _ = registry.get_tool(tool_name)
        description = getattr(method, '_tool_description', 'No description available.').splitlines()[0]
        print(f"{tool_name:<30} {description:<70}")


def validate_agent_tools(tool_names: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of tool names against the registry.
    
    Returns:
        A tuple of (valid_tools, invalid_tools)
    """
    registry = get_tool_registry()
    available_tools = registry.list_tools()
    
    valid = [name for name in tool_names if name in available_tools]
    invalid = [name for name in tool_names if name not in available_tools]
    
    return valid, invalid


def suggest_tools_for_agent(agent_name: str, agent_description: str = "") -> List[str]:
    """
    Suggest a list of relevant tools for a new agent.
    (This is a placeholder for a more intelligent suggestion mechanism)
    """
    # For now, just return a few basic tools
    return ['read_file', 'write_file', 'list_directory']








 