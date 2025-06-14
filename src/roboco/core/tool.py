"""
Tool component for function calling and code execution.
"""

import asyncio
import inspect
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union, get_type_hints, get_origin, get_args
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps

from pydantic import BaseModel, Field, create_model

from ..utils.logger import get_logger

logger = get_logger(__name__)


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


class CodeExecutionTool(Tool):
    """Tool for executing code securely."""
    
    def __init__(self):
        super().__init__("code_execution")
        self.executor = None
        self._init_executor()
    
    def _init_executor(self):
        """Initialize code executor."""
        try:
            from autogen.coding import LocalCommandLineCodeExecutor
            import tempfile
            
            self.executor = LocalCommandLineCodeExecutor(
                timeout=60,
                work_dir=tempfile.mkdtemp()
            )
        except ImportError:
            logger.warning("autogen not available, code execution disabled")
            self.executor = None
    
    @tool(
        description="Execute Python code securely in a sandboxed environment",
        return_description="ToolResult with execution output, success status, and execution time"
    )
    async def execute_code(self, code: str, language: str = "python") -> ToolResult:
        """
        Execute code and return result.
        
        Args:
            code: The Python code to execute (required)
            language: Programming language, defaults to 'python'. Supported: python, bash, shell
            
        Returns:
            ToolResult containing execution output and metadata
        """
        if not self.executor:
            return ToolResult(
                success=False,
                result=None,
                error="Code executor not available"
            )
        
        start_time = time.time()
        
        try:
            result = self.executor.execute_code_blocks([{
                "code": code,
                "language": language
            }])
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"language": language}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Code execution failed: {e}")
            
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"language": language, "error_type": type(e).__name__}
            )


class ToolRegistry:
    """
    Global tool registry that manages all available tools and creates schemas.
    
    This is a singleton that holds all registered tools and provides
    schema generation for any subset of tool names.
    """
    
    def __init__(self):
        self._tools: Dict[str, tuple[Tool, Callable, Optional[BaseModel]]] = {}
    
    def register_tool(self, tool: Tool):
        """Register a tool and all its callable methods."""
        methods = tool.get_callable_methods()
        for tool_name, method in methods.items():
            pydantic_model = _create_pydantic_model_from_signature(method)
            self._tools[tool_name] = (tool, method, pydantic_model)
            logger.info(f"Registered tool call '{tool_name}' from {tool.__class__.__name__}")
    
    def get_tool_schemas(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Get detailed OpenAI function schemas for specified tools."""
        schemas = []
        for name in tool_names:
            if name in self._tools:
                tool_instance, method, pydantic_model = self._tools[name]
                all_schemas = tool_instance.get_tool_schemas()
                if name in all_schemas:
                    schemas.append(all_schemas[name])
            else:
                logger.warning(f"Tool '{name}' not found in registry")
        return schemas
    
    def get_tool(self, name: str) -> Optional[tuple[Tool, Callable, Optional[BaseModel]]]:
        """Get a tool, method, and pydantic model by name (for executor use)."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with automatic parameter validation."""
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


# Global singleton instance
_tool_registry = ToolRegistry()


# Convenience functions that delegate to the global registry
def register_tool(tool: Tool):
    """Register a tool in the global registry."""
    _tool_registry.register_tool(tool)


def get_tool_schemas(tool_names: List[str]) -> List[Dict[str, Any]]:
    """Get detailed OpenAI function schemas for specified tools."""
    return _tool_registry.get_tool_schemas(tool_names)


def get_tool(name: str) -> Optional[tuple[Tool, Callable, Optional[BaseModel]]]:
    """Get a tool, method, and pydantic model by name."""
    return _tool_registry.get_tool(name)


def list_tools() -> List[str]:
    """List all registered tool names."""
    return _tool_registry.list_tools()


async def execute_tool(name: str, **kwargs) -> ToolResult:
    """Execute a tool by name with automatic parameter validation."""
    return await _tool_registry.execute_tool(name, **kwargs)


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return _tool_registry


def print_available_tools():
    """Print all available tools with descriptions for developers."""
    tools = _tool_registry.list_tools()
    if not tools:
        print("No tools registered yet. Register tools first with register_tool()")
        return
    
    print("Available Tools:")
    print("=" * 50)
    
    for tool_name in sorted(tools):
        tool_info = _tool_registry.get_tool(tool_name)
        if tool_info:
            tool_instance, method, _ = tool_info
            description = getattr(method, '_tool_description', 'No description')
            print(f"  {tool_name:<20} - {description}")
    
    print(f"\nTotal: {len(tools)} tools available")
    print("\nUsage in YAML config:")
    print("  tools:")
    for tool_name in sorted(tools)[:3]:  # Show first 3 as examples
        print(f"    - {tool_name}")


def validate_agent_tools(tool_names: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of tool names against available tools.
    
    Returns:
        tuple: (valid_tools, invalid_tools)
    """
    available = set(_tool_registry.list_tools())
    requested = set(tool_names)
    
    valid_tools = list(requested & available)
    invalid_tools = list(requested - available)
    
    return valid_tools, invalid_tools


def suggest_tools_for_agent(agent_name: str, agent_description: str = "") -> List[str]:
    """
    Suggest relevant tools based on agent name and description.
    
    This is a simple heuristic that can be improved with better matching.
    """
    available_tools = _tool_registry.list_tools()
    suggestions = []
    
    # Simple keyword matching
    text = f"{agent_name} {agent_description}".lower()
    
    for tool_name in available_tools:
        tool_info = _tool_registry.get_tool(tool_name)
        if tool_info:
            _, method, _ = tool_info
            description = getattr(method, '_tool_description', '').lower()
            
            # Check for keyword matches
            if any(keyword in text for keyword in ['web', 'search', 'browser']) and 'web' in tool_name:
                suggestions.append(tool_name)
            elif any(keyword in text for keyword in ['search', 'find']) and 'search' in tool_name:
                suggestions.append(tool_name)
            elif any(keyword in text for keyword in ['code', 'execute', 'run']) and 'code' in tool_name:
                suggestions.append(tool_name)
    
    return suggestions








 