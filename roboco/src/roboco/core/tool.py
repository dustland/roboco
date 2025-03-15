"""
Tool Module

This module defines the base Tool class that all specialized tools inherit from.
Tools are designed to be compatible with AG2's function calling mechanism.
"""

import inspect
from typing import Dict, Any, List, Optional, Callable, get_type_hints
from loguru import logger

class Tool:
    """Base class for all tools that can be used by agents."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
        """
        self.name = name
        self.description = description
    
    def get_functions(self) -> Dict[str, Callable]:
        """
        Get a dictionary of the tool's functions.
        
        Returns:
            Dictionary mapping function names to callables
        """
        # Get all public methods of the class
        functions = {}
        
        # First, check if the tool implements get_function_definitions
        # This is the preferred method for tools with multiple functions
        if hasattr(self, 'get_function_definitions') and callable(getattr(self, 'get_function_definitions')):
            # Get function definitions from the tool
            function_defs = self.get_function_definitions()
            
            # Make sure execute_function is available
            if not (hasattr(self, 'execute_function') and callable(getattr(self, 'execute_function'))):
                logger.warning(f"Tool {self.name} provides function definitions but no execute_function method")
                return {}
            
            # For each function definition, create a wrapper that calls execute_function
            for func_def in function_defs:
                func_name = func_def.get('name')
                if func_name:
                    # Create a wrapper that calls execute_function with the appropriate name
                    def create_wrapper(f_name):
                        def wrapper(**kwargs):
                            return self.execute_function(f_name, kwargs)
                        return wrapper
                    
                    functions[func_name] = create_wrapper(func_name)
            
            return functions
        
        # Fallback: use the legacy approach of extracting methods
        for attr_name in dir(self):
            # Skip special methods, private methods, and known non-function attributes
            if (attr_name.startswith('_') or 
                attr_name in ['name', 'description', 'get_functions', 
                              'get_function_definitions', 'execute_function']):
                continue
                
            attr = getattr(self, attr_name)
            if callable(attr):
                # Use the method name directly without prefixing with tool name
                # This is simpler and more consistent with the get_function_definitions approach
                function_name = attr_name
                functions[function_name] = attr
                
        return functions
        
    def get_function_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get descriptions for all functions provided by this tool.
        This is used for generating AG2-compatible function descriptions.
        
        Returns:
            Dictionary mapping function names to their descriptions
        """
        descriptions = {}
        
        # If the tool provides explicit function definitions, use those
        if hasattr(self, 'get_function_definitions') and callable(getattr(self, 'get_function_definitions')):
            function_defs = self.get_function_definitions()
            for func_def in function_defs:
                func_name = func_def.get('name')
                if func_name:
                    descriptions[func_name] = {
                        'description': func_def.get('description', f"Function {func_name} from {self.name} tool"),
                        'parameters': func_def.get('parameters', {})
                    }
            return descriptions
        
        # Auto-extract descriptions from function signatures and docstrings
        functions = self.get_functions()
        for func_name, func in functions.items():
            # Extract description from docstring
            docstring = func.__doc__ or f"Function {func_name} from {self.name} tool"
            description = docstring.strip().split('\n')[0]  # First line of docstring
            
            # Parse parameters from the function signature
            parameters = self._parse_function_parameters(func)
            
            descriptions[func_name] = {
                'description': description,
                'parameters': parameters
            }
            
        return descriptions
    
    def _parse_function_parameters(self, func: Callable) -> Dict[str, Any]:
        """
        Parse function parameters to create a schema compatible with AG2.
        
        Args:
            func: The function to parse
            
        Returns:
            Parameter schema in AG2-compatible format
        """
        # Get function signature and type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Skip 'self' parameter if present
        parameters = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == 'self':
                continue
                
            # Add to required list if no default value
            if param.default is param.empty:
                parameters['required'].append(param_name)
            
            # Get parameter type if available
            param_type = type_hints.get(param_name, Any)
            json_type = self._python_type_to_json_type(param_type)
            
            # Extract parameter description from docstring if available
            param_desc = self._extract_param_doc(func, param_name) or f"Parameter {param_name}"
            
            # Add parameter to properties
            parameters['properties'][param_name] = {
                'type': json_type,
                'description': param_desc
            }
            
            # Handle Optional types
            if hasattr(param_type, "__origin__") and param_type.__origin__ is Optional:
                parameters['properties'][param_name]['type'] = self._python_type_to_json_type(param_type.__args__[0])
                
        return parameters
    
    def _python_type_to_json_type(self, py_type: Any) -> str:
        """
        Convert Python type to JSON schema type.
        
        Args:
            py_type: Python type
            
        Returns:
            Corresponding JSON schema type
        """
        # Handle basic types
        type_map = {
            str: 'string',
            int: 'integer',
            float: 'number',
            bool: 'boolean',
            list: 'array',
            dict: 'object',
            Any: 'string'  # Default to string for Any
        }
        
        # Check if it's a basic type
        if py_type in type_map:
            return type_map[py_type]
            
        # Handle list/sequence types
        if hasattr(py_type, "__origin__"):
            if py_type.__origin__ is list or py_type.__origin__ is List:
                return 'array'
            if py_type.__origin__ is dict or py_type.__origin__ is Dict:
                return 'object'
            if py_type.__origin__ is Optional:
                return self._python_type_to_json_type(py_type.__args__[0])
                
        # Default to string for unknown types
        return 'string'
    
    def _extract_param_doc(self, func: Callable, param_name: str) -> Optional[str]:
        """
        Extract parameter description from function docstring.
        
        Args:
            func: Function to extract from
            param_name: Parameter name to find
            
        Returns:
            Parameter description if found, None otherwise
        """
        if not func.__doc__:
            return None
            
        # Look for parameter in docstring (supports both Google and NumPy style docstrings)
        docstring = func.__doc__
        
        # Try Google-style docstring (Args: param_name: description)
        param_patterns = [
            f"Args:\n        {param_name}: ",
            f"Args:\n    {param_name}: ",
            f"Parameters:\n        {param_name}: ",
            f"Parameters:\n    {param_name}: ",
            f"{param_name} : ",  # NumPy style
            f"{param_name}: "    # Simple style
        ]
        
        for pattern in param_patterns:
            if pattern in docstring:
                parts = docstring.split(pattern, 1)
                if len(parts) > 1:
                    desc = parts[1].split('\n')[0].strip()
                    return desc
                    
        return None
