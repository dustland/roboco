"""
Tool component for function calling and code execution.
"""

import asyncio
import inspect
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


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


class Tool(ABC):
    """Base class for all tools."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function schema for this tool."""
        # Get the execute method signature
        sig = inspect.signature(self.execute)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "kwargs":
                continue
                
            param_info = {"type": "string"}  # Default type
            
            # Infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list:
                    param_info["type"] = "array"
                elif param.annotation == dict:
                    param_info["type"] = "object"
            
            parameters[param_name] = param_info
            
            # Check if required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": parameters,
            }
        }
        
        if required:
            schema["parameters"]["required"] = required
        
        return schema


class FunctionTool(Tool):
    """Tool that wraps a regular function."""
    
    def __init__(self, name: str, func: Callable, description: str = ""):
        super().__init__(name, description or func.__doc__ or "")
        self.func = func
        self.is_async = asyncio.iscoroutinefunction(func)
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the wrapped function."""
        import time
        start_time = time.time()
        
        try:
            if self.is_async:
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {self.name} failed: {e}")
            
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )


class CodeExecutionTool(Tool):
    """Tool for executing code using Daytona."""
    
    def __init__(self, name: str = "execute_code", description: str = "Execute code securely"):
        super().__init__(name, description)
        self._executor = None
        self._init_executor()
    
    def _init_executor(self):
        """Initialize Daytona code executor."""
        try:
            # This would initialize Daytona
            # For now, just set a placeholder
            self._executor = True
            logger.info("Code execution tool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize code executor: {e}")
            self._executor = None
    
    async def execute(self, code: str, language: str = "python") -> ToolResult:
        """Execute code in a secure sandbox."""
        if not self._executor:
            return ToolResult(
                success=False,
                result=None,
                error="Code execution not available"
            )
        
        import time
        start_time = time.time()
        
        try:
            # This would use Daytona to execute code
            # For now, return a placeholder
            result = f"Executed {language} code: {code[:50]}..."
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"language": language, "code_length": len(code)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )


class ToolRegistry:
    """Registry for managing tools for an agent."""
    
    def __init__(self, agent: "Agent"):
        self.agent = agent
        self.tools: Dict[str, Tool] = {}
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        # Add code execution tool if enabled
        if self.agent.config.enable_code_execution:
            self.register(CodeExecutionTool())
    
    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' for agent '{self.agent.name}'")
    
    def unregister(self, tool_name: str):
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool '{tool_name}' from agent '{self.agent.name}'")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI function schemas for all tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        return await tool.execute(**kwargs)
    
    async def handle_message(self, message: "Message") -> Optional[str]:
        """Handle a message and execute tools if needed."""
        # This is a simplified version
        # In a real implementation, this would parse the message for tool calls
        
        content = message.content.lower()
        
        # Check for code execution requests
        if "execute" in content and "code" in content:
            if "execute_code" in self.tools:
                # Extract code (simplified)
                if "```" in message.content:
                    code_start = message.content.find("```") + 3
                    code_end = message.content.find("```", code_start)
                    if code_end > code_start:
                        code = message.content[code_start:code_end].strip()
                        result = await self.execute_tool("execute_code", code=code)
                        
                        if result.success:
                            return f"Code executed successfully:\n{result.result}"
                        else:
                            return f"Code execution failed: {result.error}"
        
        return None
    
    def register_function(self, func: Callable, name: Optional[str] = None, description: str = ""):
        """Register a regular function as a tool."""
        tool_name = name or func.__name__
        tool = FunctionTool(tool_name, func, description)
        self.register(tool)
    
    def clear(self):
        """Clear all tools."""
        self.tools.clear()
        self._register_default_tools()


# Utility functions
def create_function_tool(func: Callable, name: Optional[str] = None, description: str = "") -> FunctionTool:
    """Create a tool from a function."""
    tool_name = name or func.__name__
    return FunctionTool(tool_name, func, description)


def register_tool(agent: "Agent", tool: Tool):
    """Register a tool with an agent."""
    agent.tools.register(tool)


def register_function(agent: "Agent", func: Callable, name: Optional[str] = None, description: str = ""):
    """Register a function as a tool with an agent."""
    agent.tools.register_function(func, name, description) 