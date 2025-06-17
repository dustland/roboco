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
        Extract parameter schema from function signature.
        
        Args:
            func: Function to analyze
            
        Returns:
            Parameter schema in JSON Schema format
        """
        sig = inspect.signature(func)
        properties = {}
        required = []
        
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
            
            properties[param_name] = param_schema
            
            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
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