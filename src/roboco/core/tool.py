"""
Tool Base Class for Roboco

This module provides a base class for tools in the Roboco system.
It wraps autogen.tools.Tool to provide a consistent interface for all Roboco tools.
"""

import inspect
from typing import Any, Callable, Dict, Optional, TypeVar, Set
from loguru import logger

from autogen.tools import Tool as AutogenTool

T = TypeVar('T')

# Initialize logger
logger = logger.bind(module=__name__)

def command():
    """
    Decorator to mark a method as a command that should be registered with the tool.
    
    Returns:
        Decorated function
    """
    def decorator(func):
        # Mark the function as a command using setattr
        setattr(func, '_is_command', True)
        # logger.debug(f"Marking function {func.__name__} as a command")
        return func
    
    return decorator

class Tool(AutogenTool):
    """
    Base class for all Roboco tools.
    
    This is a wrapper around autogen.tools.Tool that provides a consistent
    interface for all Roboco tools with support for dynamic command registration.
    
    Example:
        ```python
        class MyTool(Tool):
            def __init__(self):
                # Initialize with the parent class
                super().__init__(
                    name="my_tool",
                    description="Tool for processing queries and searching data"
                )
            
            @command()
            def process_query(self, query: str) -> Dict[str, Any]:
                '''
                Process a query.
                
                Args:
                    query: The query to process
                    
                Returns:
                    The processed result
                '''
                return {"result": f"Processed {query}"}
            
            @command()
            def search_data(self, term: str, max_results: int = 10) -> Dict[str, Any]:
                '''
                Search for data with the given term.
                
                Args:
                    term: The search term
                    max_results: Maximum number of results to return
                    
                Returns:
                    The search results
                '''
                return {"results": [f"Result {i} for {term}" for i in range(max_results)]}
        ```
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        func_or_tool: Optional[Callable] = None,
        auto_discover: bool = True,
        **kwargs
    ):
        """
        Initialize the tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            func_or_tool: Optional function or tool to wrap
            auto_discover: Whether to automatically discover and register commands
            **kwargs: Additional arguments to pass to the parent class
        """
        self._name = name
        self._base_description = description  # Store the original description
        self.commands: Dict[str, Callable] = {}
        self.registered_with_agents: Set = set()
        
        # Auto-discover and register commands if enabled
        if auto_discover:
            discovered_commands = {}
            for command_name, command_method in inspect.getmembers(self, predicate=inspect.ismethod):
                # Skip methods that start with underscore (private methods)
                if command_name.startswith('_'):
                    logger.debug(f"Skipping private method: {command_name}")
                    continue
                
                # Check if method is marked as a command using getattr
                if getattr(command_method, '_is_command', False):
                    discovered_commands[command_name] = command_method
                    logger.debug(f"Discovered command method: {command_name}")
            
            # Register all discovered commands
            self.commands = discovered_commands
            # logger.info(f"Auto-registered {len(discovered_commands)} commands: {', '.join(discovered_commands.keys())}")
        
        # Create and store the command executor function
        self._command_executor = func_or_tool if func_or_tool is not None else self._create_command_executor()
        
        # Generate the final description once
        self._description = self._generate_description()
        
        # Initialize the parent class with the generated description
        super().__init__(name=self._name, description=self._description, func_or_tool=self._command_executor, **kwargs)
        
        logger.debug(f"Initialized {self.__class__.__name__} tool")
    
    def _create_command_executor(self) -> Callable:
        """
        Create a function that executes a specified command.
        
        This method creates a function that will be used by the AutogenTool parent class
        as the main entry point for executing commands.
        
        Returns:
            A function that executes commands
        """
        # Store the original tool name to avoid it being overwritten
        logger.debug(f"⚙️ Creating command executor for tool: {self._name}")
        
        # Create a unique function name for this tool
        def execute_command(command: str, args: Any) -> Any:
            """
            Execute a command with the given arguments.
            
            Args:
                command: The name of the command to execute
                args: Arguments for the command (can be positional or keyword arguments)
                
            Returns:
                The result of the command execution
            """
            # Log the raw input for debugging
            logger.info(f"🚀 Tool {self._name} command: {command} and args: {args}")
            
            # Get the actual command function
            if command not in self.commands:
                available_commands = list(self.commands.keys())
                return {
                    "success": False,
                    "error": f"❌ Command '{command}' not found in {self.name}. Available commands: {', '.join(available_commands)}"
                }
            
            command_func = self.commands[command]
            
            try:
                # Get function signature to understand parameter requirements
                sig = inspect.signature(command_func)
                param_names = list(sig.parameters.keys())
                
                # If args is a dictionary, map keys to function parameters
                if isinstance(args, dict):
                    # Skip 'self' as it's handled automatically for method calls
                    param_names = [p for p in param_names if p != 'self']
                    
                    # First check for required parameters that might be missing
                    required_params = [p for p in param_names if sig.parameters[p].default == inspect.Parameter.empty]
                    missing_required = [p for p in required_params if p not in args]
                    
                    if missing_required:
                        return {
                            "success": False,
                            "error": f"❌ Error executing command {command}: missing required parameters: {', '.join(missing_required)}",
                            "command": command
                        }
                    
                    # Filter args to only include parameters that exist in the function signature
                    # This prevents unrelated keys from causing errors
                    valid_args = {k: v for k, v in args.items() if k in param_names}
                    
                    # Call the function with keyword arguments
                    return command_func(**valid_args)
                    
                # If args is a list or tuple, use positional arguments
                elif isinstance(args, (list, tuple)):
                    # Skip 'self' when counting required parameters
                    required_count = len([p for p in param_names if p != 'self' and 
                                         sig.parameters[p].default == inspect.Parameter.empty])
                    
                    if len(args) < required_count:
                        return {
                            "success": False,
                            "error": f"❌ Error executing command {command}: expected at least {required_count} arguments, got {len(args)}",
                            "command": command
                        }
                    
                    return command_func(*args)
                    
                # Handle single argument that's not a dict/list/tuple
                else:
                    # If there's only one parameter (excluding self), pass the argument directly
                    non_self_params = [p for p in param_names if p != 'self']
                    if len(non_self_params) == 1:
                        return command_func(args)
                    else:
                        return {
                            "success": False,
                            "error": f"❌ Error executing command {command}: expected a dict, list, or tuple for multiple parameters, got {type(args).__name__}",
                            "command": command
                        }
                        
            except TypeError as e:
                # Provide more helpful error message
                logger.error(f"❌ Error executing command {command}: {e}")
                return {
                    "success": False,
                    "error": f"❌ Error executing command {command}: {e}",
                    "command": command
                }
        
        # Set a shorter function name to comply with OpenAI's 40-character limit for tool IDs
        # Convert the tool name to a shorter representation if needed
        tool_id = self._name
        if len(tool_id) > 30:
            # Truncate and add a hash suffix to ensure uniqueness while keeping it under 30 chars
            import hashlib
            hash_suffix = hashlib.md5(tool_id.encode()).hexdigest()[:8]
            tool_id = f"{tool_id[:20]}_{hash_suffix}"
            
        execute_command.__name__ = f"{tool_id}_exec"
        return execute_command
    
    def _generate_description(self) -> str:
        """
        Generate a compact description for the tool.
        
        Returns:
            The generated description
        """
        if not self.commands:
            return self._base_description
        
        # List available commands
        available_commands = list(self.commands.keys())
        
        # Start with the base description
        description = self._base_description
        
        # Add command information with emojis
        description += f"🛠️ TOOL NAME: {self._name}\n"
        description += f"⚡ AVAILABLE COMMANDS: {', '.join(available_commands)}\n\n"
        
        # Process each command with minimal documentation
        for cmd_name, cmd_func in self.commands.items():
            # Get the function signature
            sig = inspect.signature(cmd_func)
            
            # Get the docstring
            docstring = inspect.getdoc(cmd_func)
            
            # Add command header and description with emoji
            description += f"\n## 🎯 {cmd_name}\n\n"
            if docstring:
                description += f"{docstring}\n"
            
        return description
    
    def register_with_agents(self, *agents, executor_agent) -> None:
        """
        Register this tool with one or more agents.
        
        Args:
            *agents: One or more agents to register with
            executor_agent: Executor agent for the tool.
        """
        for agent in agents:
            if agent in self.registered_with_agents:
                logger.warning(f"🔄 Tool {self.name} already registered with agent {agent.name}")
                continue
            
            try:
                # Use the stored command executor
                # Print the actual description for debugging
                # logger.info(f"🔧 Tool {self.name} being registered with {agent.name}\n")
                agent.register_tool(self._command_executor, executor_agent, description=self.description)
                self.registered_with_agents.add(agent)
                # logger.debug(f"✅ Tool {self.name} registered with agent {agent.name}")
            except Exception as e:
                logger.warning(f"❌ Error registering tool {self.name} with agent {agent.name}: {e}")
    
    @property
    def name(self) -> str:
        """
        Get the name of the tool.
        
        Returns:
            The tool name
        """
        return self._name
    
    @property
    def description(self) -> str:
        """
        Get the tool description.
        
        Returns:
            The tool description, enhanced with command information if available
        """
        return self._description
