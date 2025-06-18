"""
Base classes for tool definitions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel
import inspect


class ToolFunction(BaseModel):
    """Represents a single tool function with its metadata."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True


class Tool(ABC):
    """
    Base class for tool implementations.
    
    Tools should inherit from this class and implement their methods.
    Each public method becomes a callable tool function.
    """
    
    def __init__(self):
        """Initialize the tool."""
        pass
    
    def get_callable_methods(self) -> List[str]:
        """Get list of callable method names for this tool."""
        methods = []
        for name in dir(self):
            if not name.startswith('_') and name not in ['get_callable_methods', 'get_method_schema']:
                attr = getattr(self, name)
                if callable(attr):
                    methods.append(name)
        return methods
    
    def get_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Get JSON schema for a specific method."""
        if not hasattr(self, method_name):
            raise ValueError(f"Method '{method_name}' not found in tool")
        
        method = getattr(self, method_name)
        if not callable(method):
            raise ValueError(f"'{method_name}' is not a callable method")
        
        # Get function signature
        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or f"Execute {method_name}"
        
        # Build parameter schema
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
            "type": "function",
            "function": {
                "name": method_name,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        } 