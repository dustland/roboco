"""
Tool registry for managing tool definitions and discovery.

The registry is responsible for:
- Registering tools and their metadata
- Tool discovery and lookup
- Schema generation
- NOT for execution (that's ToolExecutor's job)
"""

from typing import Dict, List, Any, Optional, Callable
import inspect
from ..utils.logger import get_logger
from .base import Tool, ToolFunction

logger = get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing tool definitions and metadata.
    
    This class handles tool registration and discovery but NOT execution.
    Tool execution is handled by ToolExecutor for security and performance.
    """
    
    def __init__(self):
        """Initialize empty tool registry."""
        self.tools: Dict[str, ToolFunction] = {}
        self.tool_objects: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool instance and all its callable methods.
        
        Args:
            tool: Tool instance to register
        """
        tool_name = tool.__class__.__name__
        logger.debug(f"Registering tool: {tool_name}")
        
        # Store the tool object
        self.tool_objects[tool_name] = tool
        
        # Register each callable method
        for method_name in tool.get_callable_methods():
            method = getattr(tool, method_name)
            
            # Create tool function entry
            tool_function = ToolFunction(
                name=method_name,
                description=inspect.getdoc(method) or f"Execute {method_name}",
                function=method,
                parameters=self._extract_parameters(method)
            )
            
            self.tools[method_name] = tool_function
            logger.debug(f"Registered tool function: {method_name}")
    
    def register_function(self, func: Callable, name: Optional[str] = None) -> None:
        """
        Register a standalone function as a tool.
        
        Args:
            func: Function to register
            name: Optional name override (defaults to function name)
        """
        tool_name = name or func.__name__
        logger.debug(f"Registering function tool: {tool_name}")
        
        tool_function = ToolFunction(
            name=tool_name,
            description=inspect.getdoc(func) or f"Execute {tool_name}",
            function=func,
            parameters=self._extract_parameters(func)
        )
        
        self.tools[tool_name] = tool_function
    
    def get_tool_function(self, name: str) -> Optional[ToolFunction]:
        """
        Get a tool function by name.
        
        Args:
            name: Tool function name
            
        Returns:
            ToolFunction if found, None otherwise
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self.tools.keys())
    
    def get_tool_schemas(self, tool_names: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get JSON schemas for tools.
        
        Args:
            tool_names: Optional list of specific tool names to get schemas for.
                       If None, returns schemas for all tools.
                       
        Returns:
            List of tool schemas in OpenAI function calling format
        """
        if tool_names is None:
            tool_names = self.list_tools()
        
        schemas = []
        for name in tool_names:
            if name in self.tools:
                tool_func = self.tools[name]
                schema = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool_func.description,
                        "parameters": tool_func.parameters
                    }
                }
                schemas.append(schema)
            else:
                logger.warning(f"Tool '{name}' not found in registry")
        
        return schemas
    
    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """
        Extract parameter schema from function signature and docstring.
        
        Args:
            func: Function to analyze
            
        Returns:
            Parameter schema in JSON Schema format
        """
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        # Extract parameter descriptions from docstring
        param_descriptions = self._extract_param_descriptions_from_docstring(func)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_schema = {"type": "string"}  # Default type
            
            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_schema["type"] = "integer"
                elif param.annotation == float:
                    param_schema["type"] = "number"
                elif param.annotation == bool:
                    param_schema["type"] = "boolean"
                elif param.annotation == list:
                    param_schema["type"] = "array"
                elif param.annotation == dict:
                    param_schema["type"] = "object"
            
            # Add description from docstring if available
            if param_name in param_descriptions:
                param_schema["description"] = param_descriptions[param_name]
            
            properties[param_name] = param_schema
            
            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _extract_param_descriptions_from_docstring(self, func: Callable) -> Dict[str, str]:
        """
        Extract parameter descriptions from function docstring.
        
        Supports Google-style docstrings with Args: section.
        
        Args:
            func: Function to analyze
            
        Returns:
            Dictionary mapping parameter names to descriptions
        """
        docstring = inspect.getdoc(func)
        if not docstring:
            return {}
        
        param_descriptions = {}
        lines = docstring.split('\n')
        
        # Find Args: section
        in_args_section = False
        for line in lines:
            stripped_line = line.strip()
            
            if stripped_line.startswith('Args:'):
                in_args_section = True
                continue
            elif in_args_section and stripped_line.startswith(('Returns:', 'Yields:', 'Raises:', 'Note:', 'Example:')):
                break
            elif in_args_section and stripped_line and not line.startswith(' '):
                # End of args section if we hit a non-indented line
                break
            elif in_args_section and ':' in stripped_line and not stripped_line.startswith(('Returns:', 'Yields:', 'Raises:')):
                # Parse parameter line: "param_name: description"
                parts = stripped_line.split(':', 1)
                if len(parts) == 2:
                    param_name = parts[0].strip()
                    description = parts[1].strip()
                    if param_name and description:
                        param_descriptions[param_name] = description
        
        return param_descriptions
    
    def clear(self):
        """Clear all registered tools."""
        self.tools.clear()
        self.tool_objects.clear()
        logger.debug("Tool registry cleared")


# Global registry instance
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return _global_registry


def register_tool(tool: Tool) -> None:
    """
    Register a tool in the global registry.
    
    Args:
        tool: Tool instance to register
    """
    _global_registry.register_tool(tool)


def register_function(func: Callable, name: Optional[str] = None) -> None:
    """
    Register a function as a tool in the global registry.
    
    Args:
        func: Function to register
        name: Optional name override
    """
    _global_registry.register_function(func, name)


def list_tools() -> List[str]:
    """List all registered tool names."""
    return _global_registry.list_tools()


def validate_agent_tools(tool_names: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of tool names against the registry.
    
    Returns:
        A tuple of (valid_tools, invalid_tools)
    """
    available_tools = _global_registry.list_tools()
    
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
        tool_func = registry.get_tool_function(tool_name)
        if tool_func:
            description = tool_func.description.splitlines()[0] if tool_func.description else 'No description available.'
            print(f"{tool_name:<30} {description:<70}") 