"""
Tool Base Class for Roboco

This module provides a base class for tools in the Roboco system.
It wraps autogen.tools.Tool to provide a consistent interface for all Roboco tools.
"""

import inspect
import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Set
from loguru import logger

from autogen.tools import Tool as AutogenTool

T = TypeVar('T')

def command(primary: bool = False):
    """
    Decorator to mark a method as a command that should be registered with the tool.
    
    Args:
        primary: Whether this command should be the primary (default) command
        
    Returns:
        Decorated function
    """
    def decorator(func):
        # Mark the function as a command without wrapping it
        func._is_command = True
        func._is_primary = primary
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
            
            @command(primary=True)
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
        self._description = description
        self.commands: Dict[str, Callable] = {}
        self.primary_command: Optional[str] = None
        self.registered_with_agents: Set = set()
        
        # Auto-discover and register commands if enabled
        if auto_discover:
            discovered_commands = {}
            for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
                # Skip methods that start with underscore (private methods)
                if name.startswith('_'):
                    continue
                
                # Skip methods that are not marked as commands
                if not hasattr(method, '_is_command'):
                    continue
                
                # Add to discovered commands
                discovered_commands[name] = method
                
                # Check if this is the primary command
                if hasattr(method, '_is_primary') and method._is_primary:
                    self.primary_command = name
            
            # Register all discovered commands
            for name, method in discovered_commands.items():
                self.register_command(name, method)
            
            logger.debug(f"Auto-registered {len(discovered_commands)} commands: {', '.join(discovered_commands.keys())}")
        
        # Create the command executor function for the parent class
        executor = func_or_tool if func_or_tool is not None else self._create_command_executor()
        
        # Initialize the parent class
        super().__init__(name=name, description=description, func_or_tool=executor, **kwargs)
        
        # Set the description
        self._description = self._generate_description()
        
        logger.debug(f"Initialized {self.__class__.__name__} tool")
    
    def _create_command_executor(self) -> Callable:
        """
        Create a function that executes the primary command or a specified command.
        
        This method creates a function that will be used by the AutogenTool parent class
        as the main entry point for executing commands.
        
        Returns:
            A function that executes commands
        """
        def execute_command(*args: Any, **kwargs: Any) -> Any:
            """
            Execute a command with the given arguments.
            
            Args:
                *args: Positional arguments to pass to the command
                **kwargs: Keyword arguments to pass to the command
                
            Returns:
                The result of the command execution
            
            Raises:
                ValueError: If the command is not found or if required parameters are missing
            """
            # Extract the command name from kwargs if it exists
            command = kwargs.pop("command", None)
            
            # Handle special case for agent tool calls which may pass args/kwargs in a specific format
            if len(args) == 1 and isinstance(args[0], dict):
                agent_args = []
                agent_kwargs = {}
                
                # Case 1: Agent passes {"args": [...], "kwargs": {...}}
                if "args" in args[0] and "kwargs" in args[0]:
                    agent_args = args[0].get("args", [])
                    agent_kwargs = args[0].get("kwargs", {})
                    
                    # If the first arg is a command name (string), extract it
                    if agent_args and isinstance(agent_args[0], str) and agent_args[0] in self.commands:
                        command = agent_args[0]
                        agent_args = agent_args[1:]
                
                # Case 2: Agent passes direct parameters as a dict
                else:
                    agent_kwargs = args[0]
                
                # Special handling for FileSystemTool's save_file command
                if self.name == "filesystem" and command == "save_file" and len(agent_args) >= 1:
                    # If we have a file_path as the first arg but no content in kwargs, try to extract from args
                    if "content" not in agent_kwargs and len(agent_args) >= 1:
                        # The first arg might be the file_path, and we need to find content
                        if "file_path" not in agent_kwargs:
                            agent_kwargs["file_path"] = agent_args[0]
                            
                        # If there's a second arg, it might be the content
                        if len(agent_args) >= 2:
                            agent_kwargs["content"] = agent_args[1]
                
                # Special handling for FileSystemTool's read_file command
                if self.name == "filesystem" and (command == "read_file" or "read_file" in agent_args):
                    if "read_file" in agent_args:
                        command = "read_file"
                        agent_args.remove("read_file")
                    
                    if len(agent_args) >= 1 and "file_path" not in agent_kwargs:
                        agent_kwargs["file_path"] = agent_args[0]
                
                # Use these instead of the original args/kwargs
                args = agent_args
                kwargs.update(agent_kwargs)
            
            # If no command is specified, use the primary command
            if command is None:
                if self.primary_command is None:
                    raise ValueError(f"No command specified and no primary command found for {self.name}")
                command = self.primary_command
            
            try:
                # Execute the command
                return self.execute_command(command=command, *args, **kwargs)
            except TypeError as e:
                # Provide more helpful error message
                logger.error(f"Error executing command {command}: {e}")
                return {
                    "success": False,
                    "error": f"Error executing command {command}: {e}",
                    "command": command
                }
            
        return execute_command
    
    def _generate_description(self) -> str:
        """
        Generate a description for the tool.
        
        This method generates a rich description of the tool and its commands,
        including parameter information, return values, and examples.
        
        Returns:
            The generated description
        """
        if not self.commands:
            return self._description
        
        # Start with the basic description
        description = f"{self._description}\n\n"
        
        # Add information about available commands
        description += f"This tool provides the following commands:\n\n"
        
        # Process each command
        for cmd_name, cmd_func in self.commands.items():
            # Get the function signature
            sig = inspect.signature(cmd_func)
            
            # Get the docstring
            docstring = cmd_func.__doc__ or ""
            docstring = inspect.cleandoc(docstring) if docstring else ""
            
            # Extract parameter descriptions from docstring
            param_descriptions = {}
            return_description = ""
            current_param = None
            
            if docstring:
                lines = docstring.split('\n')
                in_args_section = False
                in_returns_section = False
                
                for line in lines:
                    # Skip empty lines
                    if not line:
                        continue
                        
                    # Check for Args section
                    if line.lower() in ("args:", "parameters:"):
                        in_args_section = True
                        in_returns_section = False
                        continue
                    
                    # Check for Returns section
                    if line.lower() == "returns:":
                        in_args_section = False
                        in_returns_section = True
                        continue
                    
                    # Check if we're exiting the current section
                    if (in_args_section or in_returns_section) and (not line or (line.lower().endswith(':') and not line.lower() in ("args:", "parameters:", "returns:"))):
                        in_args_section = False
                        in_returns_section = False
                        continue
                    
                    # Parse parameter and its description
                    if in_args_section:
                        # Check if this is a new parameter definition
                        if line and ':' in line:
                            parts = line.split(':', 1)
                            param_name = parts[0].strip()
                            param_desc = parts[1].strip()
                            param_descriptions[param_name] = param_desc
                            current_param = param_name
                        elif current_param and line:
                            # Continuation of description for the current parameter
                            param_descriptions[current_param] += " " + line
                    
                    # Parse return description
                    if in_returns_section and line:
                        if return_description:
                            return_description += " " + line
                        else:
                            return_description = line
            
            # Format the parameters for clarity
            params = []
            for param_name, param in sig.parameters.items():
                # Safely get type annotation name
                if param.annotation is not param.empty:
                    try:
                        if hasattr(param.annotation, "__name__"):
                            type_name = param.annotation.__name__
                        elif hasattr(param.annotation, "_name"):
                            type_name = param.annotation._name
                        else:
                            type_name = str(param.annotation).replace("typing.", "")
                    except Exception:
                        type_name = "Any"
                else:
                    type_name = "Any"
                
                if param.default is param.empty:
                    default_str = ""
                else:
                    default_str = f" = {repr(param.default)}"
                
                # Skip 'self' parameter for methods
                if param_name == 'self':
                    continue
                
                param_str = f"{param_name}: {type_name}{default_str}"
                params.append(param_str)
            
            # Create the command signature
            signature = f"{cmd_name}({', '.join(params)})"
            
            # Add primary command indicator
            primary_indicator = " (primary command)" if cmd_name == self.primary_command else ""
            
            # Add the command to the description
            description += f"## {signature}{primary_indicator}\n\n"
            
            # Add the command description (first line of docstring)
            if docstring:
                first_line = docstring.split('\n')[0].strip()
                description += f"{first_line}\n\n"
            
            # Add parameter descriptions
            if param_descriptions:
                description += "Parameters:\n"
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    param_desc = param_descriptions.get(param_name, "No description available")
                    description += f"- {param_name}: {param_desc}\n"
                description += "\n"
            
            # Add return description
            if return_description:
                description += f"Returns: {return_description}\n\n"
            
            # Add examples if available
            examples = self._extract_examples_from_docstring(docstring)
            if examples:
                description += "Examples:\n"
                for example in examples:
                    description += f"{example}\n"
                description += "\n"
        
        # Add usage guidance
        description += "\n## Usage\n\n"
        description += f"To use this tool, specify a command and its parameters. "
        if self.primary_command:
            description += f"If no command is specified, the primary command '{self.primary_command}' will be used."
        description += "\n\n"
        
        return description
    
    def _extract_examples_from_docstring(self, docstring: str) -> List[str]:
        """
        Extract example usages from a function's docstring.
        
        Args:
            docstring: The function's docstring
            
        Returns:
            List of example strings
        """
        if not docstring:
            return []
            
        examples = []
        lines = docstring.split('\n')
        in_examples_section = False
        current_example = []
        
        for line in lines:
            # Check for Examples section
            if line.strip().lower() == "examples:" or line.strip().lower() == "example:":
                in_examples_section = True
                continue
                
            # Check if we're exiting the Examples section
            if in_examples_section and line.strip() and line.strip().lower().endswith(':') and not line.strip().lower() in ("example:", "examples:"):
                in_examples_section = False
                if current_example:
                    examples.append('\n'.join(current_example))
                    current_example = []
                continue
                
            # Add the line to the current example
            if in_examples_section:
                if line.strip():
                    current_example.append(line)
                elif current_example:  # Empty line after content, possible example separation
                    examples.append('\n'.join(current_example))
                    current_example = []
        
        # Add the last example if there is one
        if current_example:
            examples.append('\n'.join(current_example))
            
        return examples

    def register_commands(self, commands: Dict[str, Callable]) -> None:
        """
        Register multiple commands with the tool.
        
        Args:
            commands: Dictionary mapping command names to functions
        """
        for cmd_name, cmd_func in commands.items():
            self.register_command(cmd_name, cmd_func)
        
        # After registering all commands, update the description
        self._description = self._generate_description()
    
    def register_command(self, command_name: str, command_func: Callable) -> None:
        """
        Register a single command with the tool.
        
        Args:
            command_name: Name of the command
            command_func: Function to execute for the command
        """
        if command_name in self.commands:
            logger.warning(f"Command {command_name} already registered, overwriting")
        
        self.commands[command_name] = command_func
        
        # If this is the first command, set it as primary
        if self.primary_command is None:
            self.primary_command = command_name
            
        logger.debug(f"Registered command: {command_name}")
        
        # Update the description after registering a command
        self._description = self._generate_description()
    
    def execute_command(self, command: str = None, **kwargs) -> Any:
        """
        Execute a command from this tool.
        
        Args:
            command: The command to execute - must be a registered command name
            **kwargs: Parameters for the command
            
        Returns:
            The result of the command execution
        """
        if command is None:
            # Use the default command if no command is specified
            # This is useful for tools with a single command
            if len(self.commands) == 1:
                command = next(iter(self.commands.keys()))
            elif hasattr(self, "primary_command") and self.primary_command:
                command = self.primary_command
            else:
                return {
                    "success": False,
                    "error": "No command specified and no default command available. Available commands: " + ", ".join(self.commands.keys()),
                    "command": command
                }
                
        logger.debug(f"Executing command: {command} with parameters: {kwargs}")
            
        # Check that the command exists
        if command not in self.commands:
            return {
                "success": False,
                "error": f"Unknown command '{command}'. Available commands: {', '.join(self.commands.keys())}",
                "command": command
            }
            
        # Execute the command - pass the parameters directly, not wrapped in kwargs
        try:
            # Get the command from the registry
            command_func = self.commands[command]
            
            # Check if kwargs contains a nested 'kwargs' dictionary
            # This happens when a tool is called with {'command': 'cmd', 'kwargs': {'arg1': val1}}
            if 'kwargs' in kwargs and isinstance(kwargs['kwargs'], dict):
                # Extract the actual parameters from the nested kwargs
                actual_kwargs = kwargs['kwargs']
                # Call the function with the extracted parameters
                return command_func(**actual_kwargs)
            else:
                # Call the function with the original parameters if no nesting
                return command_func(**kwargs)
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            return {
                "success": False,
                "error": f"Error executing command {command}: {str(e)}",
                "command": command
            }
    
    def register_with_agents(self, *agents, executor_agent=None) -> None:
        """
        Register this tool with one or more agents.
        
        Args:
            *agents: One or more agents to register with
            executor_agent: Optional executor agent for the tool. If None, the first agent is used as executor.
        """
        # If no executor_agent is provided, use the first agent as executor
        if executor_agent is None and agents:
            executor_agent = agents[0]
            
        for agent in agents:
            if agent in self.registered_with_agents:
                logger.debug(f"Tool {self.name} already registered with agent {agent.name}")
                continue
                
            try:
                # Check if the agent has a register_tool method
                if hasattr(agent, 'register_tool'):
                    # Register the main tool function first
                    func = self.func
                    func.__name__ = self.name  # Set the name attribute for logging
                    
                    # Check if the agent has a valid llm_config
                    if hasattr(agent, 'llm_config') and agent.llm_config:
                        # Register the main function
                        agent.register_tool(func, executor_agent)
                        
                        # Register individual commands as separate functions
                        for cmd_name, cmd_func in self.commands.items():
                            # Create a wrapper function that calls the command with proper parameter mapping
                            def create_command_wrapper(command_name, command_func):
                                # Get the signature of the command function to understand its parameters
                                sig = inspect.signature(command_func)
                                param_names = list(sig.parameters.keys())
                                
                                # Skip 'self' if it's the first parameter
                                if param_names and param_names[0] == 'self':
                                    param_names = param_names[1:]
                                
                                @functools.wraps(command_func)
                                def wrapper(*args, **kwargs):
                                    # Handle different ways agents might call the function
                                    processed_kwargs = {}
                                    
                                    # Case 1: Agent passes a single dict with 'args' and 'kwargs' keys
                                    if len(args) == 1 and isinstance(args[0], dict):
                                        agent_args = args[0].get('args', [])
                                        agent_kwargs = args[0].get('kwargs', {})
                                        
                                        # If agent_args is not empty, map positional args to named parameters
                                        for i, arg in enumerate(agent_args):
                                            if i < len(param_names):
                                                processed_kwargs[param_names[i]] = arg
                                        
                                        # Add any explicitly named parameters from agent_kwargs
                                        processed_kwargs.update(agent_kwargs)
                                    else:
                                        # Case 2: Regular function call with args/kwargs
                                        # Map positional args to named parameters
                                        for i, arg in enumerate(args):
                                            if i < len(param_names):
                                                processed_kwargs[param_names[i]] = arg
                                        
                                        # Add any explicitly named parameters
                                        processed_kwargs.update(kwargs)
                                    
                                    # Call the command with the processed parameters
                                    return self.execute_command(command=command_name, **processed_kwargs)
                                
                                # Set the function name for proper registration
                                wrapper.__name__ = f"{self.name}_{command_name}"
                                
                                # Add proper parameter annotations for the wrapper
                                # This helps avoid the "missing annotations" warning
                                sig_params = list(sig.parameters.values())
                                if sig_params and sig_params[0].name == 'self':
                                    sig_params = sig_params[1:]
                                
                                # Create new parameters without 'self' but with proper annotations
                                wrapper.__annotations__ = {p.name: p.annotation for p in sig_params 
                                                         if p.annotation is not inspect.Parameter.empty}
                                
                                return wrapper
                            
                            # Register the command wrapper
                            cmd_wrapper = create_command_wrapper(cmd_name, cmd_func)
                            agent.register_tool(cmd_wrapper, executor_agent)
                            logger.info(f"Registered function {cmd_name} with caller {agent.name} and executor {executor_agent.name}")
                        
                        self.registered_with_agents.add(agent)
                        logger.debug(f"Registered tool {self.name} with agent {agent.name} using register_tool")
                    else:
                        # For agents without llm_config, register the function directly
                        if hasattr(agent, '_function_map'):
                            agent._function_map[self.name] = self.func
                            
                            # Also register individual commands
                            for cmd_name, cmd_func in self.commands.items():
                                def create_command_wrapper(command_name, command_func):
                                    # Get the signature of the command function to understand its parameters
                                    sig = inspect.signature(command_func)
                                    param_names = list(sig.parameters.keys())
                                    
                                    # Skip 'self' if it's the first parameter
                                    if param_names and param_names[0] == 'self':
                                        param_names = param_names[1:]
                                    
                                    @functools.wraps(command_func)
                                    def wrapper(*args, **kwargs):
                                        # Handle different ways agents might call the function
                                        processed_kwargs = {}
                                        
                                        # Case 1: Agent passes a single dict with 'args' and 'kwargs' keys
                                        if len(args) == 1 and isinstance(args[0], dict):
                                            agent_args = args[0].get('args', [])
                                            agent_kwargs = args[0].get('kwargs', {})
                                            
                                            # If agent_args is not empty, map positional args to named parameters
                                            for i, arg in enumerate(agent_args):
                                                if i < len(param_names):
                                                    processed_kwargs[param_names[i]] = arg
                                            
                                            # Add any explicitly named parameters from agent_kwargs
                                            processed_kwargs.update(agent_kwargs)
                                        else:
                                            # Case 2: Regular function call with args/kwargs
                                            # Map positional args to named parameters
                                            for i, arg in enumerate(args):
                                                if i < len(param_names):
                                                    processed_kwargs[param_names[i]] = arg
                                            
                                            # Add any explicitly named parameters
                                            processed_kwargs.update(kwargs)
                                        
                                        # Call the command with the processed parameters
                                        return self.execute_command(command=command_name, **processed_kwargs)
                                    
                                    # Set the function name for proper registration
                                    wrapper.__name__ = f"{self.name}_{command_name}"
                                    
                                    # Add proper parameter annotations for the wrapper
                                    # This helps avoid the "missing annotations" warning
                                    sig_params = list(sig.parameters.values())
                                    if sig_params and sig_params[0].name == 'self':
                                        sig_params = sig_params[1:]
                                    
                                    # Create new parameters without 'self' but with proper annotations
                                    wrapper.__annotations__ = {p.name: p.annotation for p in sig_params 
                                                             if p.annotation is not inspect.Parameter.empty}
                                    
                                    return wrapper
                                
                                # Register the command wrapper
                                cmd_wrapper = create_command_wrapper(cmd_name, cmd_func)
                                agent._function_map[f"{self.name}_{cmd_name}"] = cmd_wrapper
                                logger.debug(f"Directly registered command {cmd_name} with agent {agent.name}")
                            
                            self.registered_with_agents.add(agent)
                            logger.debug(f"Directly registered tool {self.name} with agent {agent.name}")
                        else:
                            logger.warning(f"Agent {agent.name} does not have llm_config or _function_map, skipping registration")
                # Check if the agent has a register_function method (autogen compatibility)
                elif hasattr(agent, 'register_function'):
                    try:
                        # Create a function map with all commands
                        function_map = {self.name: self.func}
                        description_map = {self.name: self._description if hasattr(self, '_description') else self.description}
                        
                        # Add individual commands
                        for cmd_name, cmd_func in self.commands.items():
                            def create_command_wrapper(command_name, command_func):
                                # Get the signature of the command function to understand its parameters
                                sig = inspect.signature(command_func)
                                param_names = list(sig.parameters.keys())
                                
                                # Skip 'self' if it's the first parameter
                                if param_names and param_names[0] == 'self':
                                    param_names = param_names[1:]
                                
                                @functools.wraps(command_func)
                                def wrapper(*args, **kwargs):
                                    # Handle different ways agents might call the function
                                    processed_kwargs = {}
                                    
                                    # Case 1: Agent passes a single dict with 'args' and 'kwargs' keys
                                    if len(args) == 1 and isinstance(args[0], dict):
                                        agent_args = args[0].get('args', [])
                                        agent_kwargs = args[0].get('kwargs', {})
                                        
                                        # If agent_args is not empty, map positional args to named parameters
                                        for i, arg in enumerate(agent_args):
                                            if i < len(param_names):
                                                processed_kwargs[param_names[i]] = arg
                                        
                                        # Add any explicitly named parameters from agent_kwargs
                                        processed_kwargs.update(agent_kwargs)
                                    else:
                                        # Case 2: Regular function call with args/kwargs
                                        # Map positional args to named parameters
                                        for i, arg in enumerate(args):
                                            if i < len(param_names):
                                                processed_kwargs[param_names[i]] = arg
                                        
                                        # Add any explicitly named parameters
                                        processed_kwargs.update(kwargs)
                                    
                                    # Call the command with the processed parameters
                                    return self.execute_command(command=command_name, **processed_kwargs)
                                
                                # Set the function name for proper registration
                                wrapper.__name__ = f"{self.name}_{command_name}"
                                
                                # Add proper parameter annotations for the wrapper
                                # This helps avoid the "missing annotations" warning
                                sig_params = list(sig.parameters.values())
                                if sig_params and sig_params[0].name == 'self':
                                    sig_params = sig_params[1:]
                                
                                # Create new parameters without 'self' but with proper annotations
                                wrapper.__annotations__ = {p.name: p.annotation for p in sig_params 
                                                         if p.annotation is not inspect.Parameter.empty}
                                
                                return wrapper
                            
                            # Register the command wrapper
                            cmd_wrapper = create_command_wrapper(cmd_name, cmd_func)
                            function_map[f"{self.name}_{cmd_name}"] = cmd_wrapper
                            description_map[f"{self.name}_{cmd_name}"] = f"Execute the {cmd_name} command of the {self.name} tool"
                        
                        agent.register_function(
                            function_map=function_map,
                            description=description_map
                        )
                        self.registered_with_agents.add(agent)
                        logger.debug(f"Registered tool {self.name} with agent {agent.name} using register_function")
                    except Exception as e:
                        logger.warning(f"Failed to register tool {self.name} with agent {agent.name}: {e}")
                else:
                    logger.warning(f"Agent {agent.name} does not have register_tool or register_function method")
            except Exception as e:
                logger.warning(f"Error registering tool {self.name} with agent {agent.name}: {e}")
    
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
