"""
Tool Base Class for Roboco

This module provides a base class for tools in the Roboco system.
It wraps autogen.tools.Tool to provide a consistent interface for all Roboco tools.
"""

import inspect
import functools
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Set
from loguru import logger

from autogen.tools import Tool as AutogenTool

T = TypeVar('T')

class Tool(AutogenTool):
    """
    Base class for all Roboco tools.
    
    This is a wrapper around autogen.tools.Tool that provides a consistent
    interface for all Roboco tools with support for dynamic command registration.
    
    Example:
        ```python
        class MyTool(Tool):
            def __init__(self):
                # Define commands that will be dynamically registered
                
                def process_query(query: str) -> Dict[str, Any]:
                    '''
                    Process a query.
                    
                    Args:
                        query: The query to process
                        
                    Returns:
                        The processed result
                    '''
                    return {"result": f"Processed {query}"}
                
                def search_data(term: str, max_results: int = 10) -> Dict[str, Any]:
                    '''
                    Search for data with the given term.
                    
                    Args:
                        term: The search term
                        max_results: Maximum number of results to return
                        
                    Returns:
                        Dictionary with search results
                    '''
                    return {"results": [f"Result for {term}: {i}" for i in range(max_results)]}
                
                # Initialize with the parent class
                super().__init__(
                    name="my_tool",
                    description="Tool for processing queries and searching data"
                )
                
                # Register all commands
                commands = {
                    "process_query": process_query,
                    "search_data": search_data
                }
                self.register_commands(commands)
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
        Initialize the Tool.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
            func_or_tool: The function to be called when the tool is invoked (optional)
            auto_discover: Whether to automatically discover functions defined in __init__ (default: True)
            **kwargs: Additional arguments to pass to the parent class
        """
        # Initialize instance variables
        self.commands = {}
        self.primary_command = None
        self.registered_with_agents = set()
        
        # If auto_discover is enabled, find functions defined in __init__
        if auto_discover:
            # Get the local variables from the caller frame (__init__ of the child class)
            import inspect
            caller_frame = inspect.currentframe().f_back
            local_vars = caller_frame.f_locals if caller_frame else {}
            
            # Find all callable objects that aren't methods or built-ins
            discovered_commands = {}
            for name, obj in local_vars.items():
                # Skip non-callable, private, or special items
                if not callable(obj) or name.startswith('_') or name == 'self':
                    continue
                    
                # Skip methods (bound to an instance)
                if inspect.ismethod(obj):
                    continue
                    
                # Skip builtins and imports
                if obj.__module__ in ('builtins', '__builtin__'):
                    continue
                    
                # Avoid infinite recursion edge case with nested functions that call Tool.__init__
                if name in ('super', '__init__'):
                    continue
                
                # It's a function we can use as a command
                discovered_commands[name] = obj
                logger.debug(f"Auto-discovered command: {name}")
            
            # Register the discovered commands
            if discovered_commands:
                self.register_commands(discovered_commands)
                logger.debug(f"Auto-registered {len(discovered_commands)} commands: {', '.join(discovered_commands.keys())}")
        
        # If no function is provided, create a command executor wrapper
        if func_or_tool is None or func_or_tool == self.execute_command:
            func_or_tool = self._create_command_executor()
        
        super().__init__(
            name=name,
            description=description,
            func_or_tool=func_or_tool,
            **kwargs
        )
        
        # Update the description with registered commands
        self._update_tool_description()
        
        logger.debug(f"Initialized {self.__class__.__name__} tool")
    
    def _create_command_executor(self) -> Callable:
        """
        Create a command executor function for this tool.
        
        The command executor is a function that takes a command name and parameters,
        and executes the appropriate command.
        
        Returns:
            A function that can be used to execute commands
        """
        tool_instance = self
        
        def command_executor(command: str = None, **kwargs: Any) -> Any:
            """
            Execute a command with the given parameters.
            
            Args:
                command: The command to execute
                **kwargs: Parameters for the command
                
            Returns:
                The result of the command execution
            """
            return tool_instance.execute_command(command, **kwargs)
            
        # Set the name to match the tool's name
        command_executor.__name__ = f"{self.__class__.__name__}_command_executor"
        
        return command_executor
    
    def register_commands(self, commands: Dict[str, Callable]) -> None:
        """
        Register multiple commands with the tool.
        
        Args:
            commands: Dictionary mapping command names to functions
        """
        for cmd_name, cmd_func in commands.items():
            self.register_command(cmd_name, cmd_func)
        
        # After registering all commands, update the description
        self._update_tool_description()
    
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
        self._update_tool_description()
    
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

    def _update_tool_description(self) -> None:
        """
        Update the tool description to include information about registered commands.
        This helps LLMs understand how to use the tool with its various commands.
        """
        if not self.commands:
            return
        
        # Start with the original description
        base_description = self.description if hasattr(self, 'description') else ""
        
        # Add command information
        command_details = []
        all_examples = []
        
        for cmd_name, cmd_func in self.commands.items():
            # Extract function signature and docstring
            sig = inspect.signature(cmd_func)
            doc = inspect.getdoc(cmd_func) or ""
            
            # Extract examples from the docstring
            examples = self._extract_examples_from_docstring(doc)
            if examples:
                for example in examples:
                    # Format the example to clearly show which command it's for
                    formatted_example = f"Example for `{cmd_name}`:\n```python\n{example}\n```"
                    all_examples.append(formatted_example)
            
            # Parse docstring to extract parameter descriptions and return info
            param_descriptions = {}
            return_description = ""
            if doc:
                # Simple docstring parser to extract parameter descriptions
                lines = doc.split('\n')
                in_args_section = False
                in_returns_section = False
                current_param = None
                
                for line in lines:
                    line = line.strip()
                    
                    # Check for Args section
                    if line.lower() == "args:" or line.lower() == "parameters:":
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
                    params.append(f"{param_name}: {type_name}")
                else:
                    default_val = repr(param.default)
                    params.append(f"{param_name}: {type_name} = {default_val}")
            
            param_str = ", ".join(params)
            
            # Format the return type if available
            if sig.return_annotation is not sig.empty:
                try:
                    if hasattr(sig.return_annotation, "__name__"):
                        return_type = sig.return_annotation.__name__
                    elif hasattr(sig.return_annotation, "_name"):
                        return_type = sig.return_annotation._name
                    else:
                        return_type = str(sig.return_annotation).replace("typing.", "")
                except Exception:
                    return_type = "Any"
            else:
                return_type = "Any"
            
            # Create command description
            cmd_desc = f"- `{cmd_name}({param_str})` -> {return_type}"
            
            # Add the brief description from the first line of the docstring
            if doc:
                brief_doc = doc.split('\n')[0].strip()
                cmd_desc += f": {brief_doc}"
            
            command_details.append(cmd_desc)
            
            # Add parameter descriptions if available
            if param_descriptions:
                param_details = []
                for p_name, p_desc in param_descriptions.items():
                    if p_name in sig.parameters:
                        param_details.append(f"  - `{p_name}`: {p_desc}")
                
                if param_details:
                    command_details.append("  Parameters:")
                    command_details.extend(param_details)
            
            # Add return value description if available
            if return_description:
                command_details.append(f"  Returns: {return_description}")
                
            # Add a blank line after each command for better readability
            command_details.append("")
        
        # Build the full description
        commands_section = "\n\nAvailable commands:\n" + "\n".join(command_details)
        
        # Add information about primary command
        primary_command_info = ""
        if self.primary_command:
            primary_command_info = f"\n\nPrimary Command: `{self.primary_command}` (used if no command is specified)"
        
        usage_section = f"{primary_command_info}\n\nUsage: Call this tool with `command='{self.primary_command}'` (or another command name) and any required parameters for that command."
        
        # Add examples section if any examples were found
        examples_section = ""
        if all_examples:
            examples_section = "\n\nExamples:\n" + "\n".join(all_examples)
        else:
            # Safely get the tool name
            tool_name = None
            if hasattr(self, '_name') and self._name:
                tool_name = self._name
            elif hasattr(self, 'name') and self.name:
                tool_name = self.name
            else:
                # Try even deeper access for autogen Tool
                try:
                    # From autogen.tool.Tool
                    if hasattr(self, '_function') and hasattr(self._function, '__self__') and hasattr(self._function.__self__, 'name'):
                        tool_name = self._function.__self__.name
                except:
                    pass
                
            # Fallback to class name if all else fails
            if not tool_name:
                tool_name = self.__class__.__name__.lower()
            
            # Fix for FileSystemTool special case
            if self.__class__.__name__ == "FileSystemTool":
                tool_name = "filesystem"
                
            examples_section = f"\n\nExample: `{tool_name}(command='{self.primary_command}', param1='value', param2=42)`"
        
        # Set the updated description
        full_description = base_description + commands_section + usage_section + examples_section
        
        # Update the description in parent class
        if hasattr(self, '_description'):
            self._description = full_description
        # For compatibility with different AutogenTool versions
        elif hasattr(self, 'description'):
            self.description = full_description
    
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
                "error": str(e),
                "command": command
            }
    
    def register_with_agents(self, caller_agent: Any, executor_agent: Any) -> None:
        """
        Register this tool with a caller agent and an executor agent.
        
        This follows AG2's pattern of having a caller agent (that suggests the tool)
        and an executor agent (that executes the tool).
        
        Args:
            caller_agent: The agent that will suggest using the tool
            executor_agent: The agent that will execute the tool
        """
        try:
            # Register the tool with both agents
            self.register_for_llm(caller_agent)
            self.register_for_execution(executor_agent)
            
            # Check if the function was registered correctly
            if hasattr(executor_agent, "_function_map") and self.name in executor_agent._function_map:
                logger.debug(f"{self.name} function successfully registered with executor agent")
            else:
                logger.warning(f"{self.name} function not found in executor_agent._function_map after registration")
                
            logger.info(f"Registered {self.name} from {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error registering {self.name}: {e}")
    
    @classmethod
    def discover_methods(cls, instance: Any, prefix: str = "", exclude: Set[str] = None) -> Dict[str, Callable]:
        """
        Discover all methods in an instance that match a prefix and are not in the exclude set.
        
        This is a utility method to help with auto-registering methods as commands.
        
        Args:
            instance: The instance to inspect
            prefix: Only include methods starting with this prefix
            exclude: Set of method names to exclude
            
        Returns:
            Dictionary mapping method names to method functions
        """
        if exclude is None:
            exclude = set()
            
        methods = {}
        
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            # Skip methods that start with _ (private/special methods)
            if name.startswith('_'):
                continue
                
            # Skip methods that don't start with the prefix
            if prefix and not name.startswith(prefix):
                continue
                
            # Skip methods in the exclude set
            if name in exclude:
                continue
                
            # Add the method to the result
            methods[name] = method
            
        return methods
